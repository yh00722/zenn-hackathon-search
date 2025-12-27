"""
Chat API ルーター
==================
ハイブリッド検索を用いたインテリジェントRAG会話クエリエンドポイント
"""
import json
import asyncio
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Query, Request
from sse_starlette.sse import EventSourceResponse

router = APIRouter()


class ChatRequest(BaseModel):
    """チャットリクエストモデル"""
    message: str
    use_hybrid: bool = True  # デフォルトでハイブリッド実行を使用
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "受賞作品の共通点は何ですか？",
                "use_hybrid": True
            }
        }


class ChatResponse(BaseModel):
    """チャットレスポンスモデル"""
    answer: str
    sources: list[dict]
    strategy: Optional[str] = None
    explanation: Optional[str] = None


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    ハッカソン作品についてAgentic RAGシステムと会話する。
    
    LangGraph ベースのマルチターン検索：
    - LLMが最適なツールを自動選択
    - 複数回のツール呼び出しで情報を収集
    - 統合された回答を生成
    
    日本語での質問を推奨、例：
    - 受賞作品の共通点は何ですか？
    - いいね数トップ5のプロジェクトは？
    - 第3回でRAGを使った作品の詳細を教えて
    """
    try:
        if request.use_hybrid:
            # Agentic RAG を使用（マルチターン）
            from services.agentic_rag import get_agentic_rag
            agent = get_agentic_rag(max_iterations=5)
            result = agent.query(request.message)
            
            return ChatResponse(
                answer=result["answer"],
                sources=[],  # Agentic RAG は sources を別途返さない
                strategy="agentic_rag",
                explanation=f"iterations={result['iterations']}, tool_calls={result['tool_calls']}"
            )
        else:
            # シンプルRAGへフォールバック
            from services.rag import get_rag_service
            rag = get_rag_service()
            result = rag.query(request.message)
            
            return ChatResponse(
                answer=result["answer"],
                sources=result["sources"],
                strategy="semantic_rag"
            )
    except ValueError as e:
        error_msg = str(e)
        if "AZURE_OPENAI" in error_msg:
            return ChatResponse(
                answer="⚠️ Azure OpenAI が設定されていません。.envファイルに認証情報を設定してください。",
                sources=[],
                strategy="config_error"
            )
        return ChatResponse(
            answer=f"設定エラー: {error_msg}",
            sources=[]
        )
    except Exception as e:
        return ChatResponse(
            answer="申し訳ありません。内部エラーが発生しました。しばらく後に再試行してください。",
            sources=[]
        )


@router.post("/stream")
async def chat_stream(request: ChatRequest, req: Request):
    """
    Server-Sent Events (SSE) を使用したストリーミングチャットレスポンス。
    
    イベント:
    - `metadata`: 戦略、ソース等の初期情報
    - `token`: 回答テキストの一部
    - `done`: 完了シグナル
    - `error`: エラーメッセージ
    
    クライアント使用例:
    ```javascript
    const eventSource = new EventSource('/api/chat/stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'token') {
            appendToAnswer(data.content);
        }
    };
    ```
    """
    async def event_generator():
        try:
            from services.agentic_rag import get_agentic_rag
            agent = get_agentic_rag(max_iterations=3)
            
            for event_type, data in agent.query_stream(request.message):
                # クライアント切断チェック
                if await req.is_disconnected():
                    break
                
                if event_type == "metadata":
                    yield {
                        "event": "metadata",
                        "data": json.dumps(data, ensure_ascii=False)
                    }
                elif event_type == "token":
                    yield {
                        "event": "token",
                        "data": json.dumps({"content": data}, ensure_ascii=False)
                    }
                elif event_type == "done":
                    yield {
                        "event": "done",
                        "data": json.dumps({"status": "complete"})
                    }
                elif event_type == "error":
                    yield {
                        "event": "error",
                        "data": json.dumps({"message": data}, ensure_ascii=False)
                    }
                
                # スムーズなストリーミングのための小さな遅延
                await asyncio.sleep(0.01)
                
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"message": str(e)}, ensure_ascii=False)
            }
    
    return EventSourceResponse(event_generator())


@router.post("/simple", response_model=ChatResponse)
async def simple_chat(request: ChatRequest):
    """ハイブリッドルーティングなしのシンプルRAG（比較用）"""
    try:
        from services.rag import get_rag_service
        rag = get_rag_service()
        result = rag.query(request.message)
        
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
            strategy="semantic_rag"
        )
    except Exception as e:
        return ChatResponse(
            answer=f"エラー: {str(e)}",
            sources=[]
        )


@router.post("/index")
async def index_documents(edition: int = None):
    """
    RAG用にドキュメントをベクトルストアにインデックス。
    チャット機能を使用する前に実行してください。
    """
    try:
        from services.rag import get_rag_service
        rag = get_rag_service()
        count = rag.index_projects(edition=edition)
        
        return {
            "status": "success",
            "indexed_chunks": count,
            "edition": edition or "all"
        }
    except ValueError as e:
        return {
            "status": "error",
            "message": str(e),
            "hint": ".envファイルにAzure OpenAIの認証情報を設定してください"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.get("/route")
async def analyze_route(q: str = Query(..., description="分析対象の質問")):
    """
    質問のルーティング方法を分析（デバッグ用）
    """
    try:
        from services.query_router import QueryRouter
        router_instance = QueryRouter()
        
        # LLMルート
        plan = router_instance.route(q)
        return {
            "method": "llm_route",
            "strategy": plan.strategy,
            "filters": plan.filters,
            "rewritten_query": plan.rewritten_query,
            "explanation": plan.explanation
        }
    except Exception as e:
        return {"error": str(e)}


@router.post("/sql")
async def execute_sql_query(q: str = Query(..., description="SQL生成用の質問")):
    """
    Text2SQLクエリを実行（デバッグ用）
    """
    try:
        from services.text2sql import Text2SQLGenerator
        generator = Text2SQLGenerator()
        result = generator.execute(q)
        return result
    except Exception as e:
        return {"error": str(e)}
