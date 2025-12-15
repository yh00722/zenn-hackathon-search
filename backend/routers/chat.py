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
    ハッカソン作品についてインテリジェントRAGシステムと会話する。
    
    システムは最適な検索戦略を自動選択：
    - **text2sql**: ランキング、統計、件数の取得
    - **filtered_rag**: 受賞作品、特定回の質問
    - **semantic_rag**: オープンエンドのトピック探索
    - **hybrid**: 複数戦略の組み合わせ
    
    日本語での質問を推奨、例：
    - 受賞作品の共通点は何ですか？
    - いいね数トップ5のプロジェクトは？
    - 第3回の受賞コメントを教えて
    - Flutterを使った作品を教えて
    """
    try:
        if request.use_hybrid:
            from services.hybrid_executor import get_hybrid_executor
            executor = get_hybrid_executor()
            result = executor.query(request.message)
            
            return ChatResponse(
                answer=result["answer"],
                sources=result.get("sources", []),
                strategy=result.get("strategy"),
                explanation=result.get("explanation")
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
        return ChatResponse(
            answer=f"エラー: {str(e)}. Azure OpenAIの設定を確認してください。",
            sources=[]
        )
    except Exception as e:
        return ChatResponse(
            answer=f"申し訳ありません。エラーが発生しました: {str(e)}",
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
            from services.hybrid_executor import get_hybrid_executor
            executor = get_hybrid_executor()
            
            for event_type, data in executor.query_stream(request.message):
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
        
        # まずクイックルートを試行
        quick_plan = router_instance.quick_route(q)
        if quick_plan:
            return {
                "method": "quick_route",
                "strategy": quick_plan.strategy,
                "filters": quick_plan.filters,
                "rewritten_query": quick_plan.rewritten_query
            }
        
        # フルLLMルート
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
