"""
Agentic RAG with LangGraph
==========================
マルチターン・ツール呼び出しによる高度な検索エンジン
"""
from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, SystemMessage
from .config import settings
from .database import db
from .llm_factory import get_chat_llm


class AgentState(TypedDict):
    """Agent の状態（LangGraph 推奨パターン）"""
    question: str                                      # 元の質問
    messages: Annotated[list, add_messages]            # 会話履歴（reducer で自動追加）
    iteration: int                                     # 現在のイテレーション数
    final_answer: str | None                           # 最終回答


# ============================================================
# ツール定義
# ============================================================

@tool
def semantic_search_summary(query: str, k: int = 4) -> list[dict]:
    """
    【推奨】プロジェクト単位の主題検索
    
    ユーザーが「〇〇関連のプロジェクト」「△△を使った作品」など
    主題・テーマで検索したい場合に使用。
    
    各プロジェクトの要約（ContentSummary）から検索し、
    プロジェクト単位で1件ずつ返すため重複なく関連作品を見つけやすい。
    """
    from .rag import get_rag_service
    rag = get_rag_service()
    docs = rag.summary_vectorstore.similarity_search(query, k=k)
    return [{"name": d.metadata.get("project_name"), 
             "url": d.metadata.get("url"),
             "summary": d.page_content,
             "is_winner": d.metadata.get("is_winner", False),
             "award_name": d.metadata.get("award_name"),
             "award_comment": d.metadata.get("award_comment")} for d in docs]


@tool
def semantic_search_content(query: str, k: int = 5) -> list[dict]:
    """
    記事本文からの詳細フラグメント検索
    
    ユーザーが「〇〇の実装方法」「具体的なコード例」「詳細な手順」など
    記事内の特定段落・技術実装の詳細を探したい場合に使用。
    
    記事本文（content_raw）のチャンクから検索するため、
    具体的なコードスニペットや実装詳細を見つけるのに適している。
    """
    from .rag import get_rag_service
    rag = get_rag_service()
    docs = rag.vectorstore.similarity_search(query, k=k)
    
    seen = set()
    results = []
    for d in docs:
        name = d.metadata.get("project_name")
        if name not in seen:
            seen.add(name)
            results.append({
                "name": name,
                "url": d.metadata.get("url"),
                "content_excerpt": d.page_content,
                "is_winner": d.metadata.get("is_winner", False),
                "award_name": d.metadata.get("award_name"),
                "award_comment": d.metadata.get("award_comment"),
            })
    return results


@tool
def text2sql_query(query: str) -> dict:
    """
    SQLクエリを生成・実行してデータベースから情報を取得
    
    以下の情報を取得したい場合にこのツールを使用：
    - 受賞作品一覧、賞の名前（award_name）、審査員コメント（award_comment）
    - ランキング（いいね数順、ブックマーク数順）
    - 統計情報（件数、集計）
    - チーム/個人での絞り込み
    - 回別（第1回/第2回/第3回）での絞り込み
    - 最終選考進出作品（is_final_pitch）
    """
    from .text2sql import Text2SQLGenerator
    gen = Text2SQLGenerator()
    return gen.execute(query)


@tool
def get_project_detail(project_name: str) -> dict:
    """プロジェクトの詳細情報を取得"""
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE project_name LIKE ? LIMIT 1",
            (f"%{project_name}%",)
        ).fetchone()
        return dict(row) if row else {"error": "プロジェクトが見つかりません"}


@tool
def keyword_search(keyword: str) -> list[dict]:
    """記事本文からキーワードでLIKE検索（技術名など完全一致向け）"""
    with db.get_connection() as conn:
        rows = conn.execute(
            """SELECT project_name, url, description 
               FROM projects WHERE content_raw LIKE ? LIMIT 10""",
            (f"%{keyword}%",)
        ).fetchall()
        return [dict(r) for r in rows]


TOOLS = [semantic_search_summary, semantic_search_content, text2sql_query, get_project_detail, keyword_search]


# ============================================================
# LangGraph Agent
# ============================================================

SYSTEM_PROMPT = """あなたはZenn AI Agent Hackathonの作品検索アシスタントです。
ユーザーの質問に答えるために、利用可能なツールを使って情報を収集してください。

利用可能なツール:
- semantic_search_summary: プロジェクトの要約から意味検索（プロジェクト探索向け）
- semantic_search_content: 記事本文から詳細を検索（技術実装向け）
- text2sql_query: ランキングや統計情報を取得（数値データ向け）
- get_project_detail: 特定プロジェクトの詳細を取得
- keyword_search: キーワードで全文検索（技術名検索向け）

十分な情報が集まったら、ツールを呼ばずに回答を生成してください。"""


class AgenticRAG:
    """LangGraph ベースの Agentic RAG"""
    
    def __init__(self, max_iterations: int = 3):
        self.max_iterations = max_iterations
        
        # LLMの初期化（Azure/OpenAI 自動選択）
        self.llm = get_chat_llm()
        
        # ツールをバインド
        self.llm_with_tools = self.llm.bind_tools(TOOLS)
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """ReActパターンのグラフを構築"""
        workflow = StateGraph(AgentState)
        
        # ノードを追加
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", ToolNode(TOOLS))
        workflow.add_node("increment_iteration", self._increment_iteration)
        workflow.add_node("generate", self._generate_node)
        
        # エントリーポイント
        workflow.set_entry_point("agent")
        
        # 条件分岐
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "generate": "generate",
            }
        )
        
        # ツール実行後 → イテレーション増加 → Agent に戻る
        workflow.add_edge("tools", "increment_iteration")
        workflow.add_edge("increment_iteration", "agent")
        
        # 生成後 → 終了
        workflow.add_edge("generate", END)
        
        return workflow.compile()
    
    def _agent_node(self, state: AgentState) -> dict:
        """Agent ノード: ツールを呼ぶか判断"""
        messages = state["messages"]
        
        # 最初のメッセージにシステムプロンプトを追加
        if len(messages) == 1:
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        
        response = self.llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    def _increment_iteration(self, state: AgentState) -> dict:
        """イテレーションカウンターを増加"""
        return {"iteration": state["iteration"] + 1}
    
    def _should_continue(self, state: AgentState) -> Literal["continue", "generate"]:
        """次のステップを決定"""
        last_message = state["messages"][-1]
        
        # ツール呼び出しがあるか
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            # イテレーション上限チェック
            if state["iteration"] >= self.max_iterations:
                return "generate"
            return "continue"
        
        return "generate"
    
    def _generate_node(self, state: AgentState) -> dict:
        """最終回答を生成"""
        # メッセージ履歴から検索結果を抽出
        tool_results = []
        for msg in state["messages"]:
            if isinstance(msg, ToolMessage):
                tool_results.append(f"[{msg.name}]: {msg.content}")
        
        prompt = f"""以下の検索結果を参考に、ユーザーの質問に日本語で回答してください。

## ユーザーの質問
{state["question"]}

## 検索結果
{chr(10).join(tool_results) if tool_results else "検索結果なし"}

## 回答ガイドライン
- 具体的なプロジェクト名を挙げながら説明
- 受賞作品は🏆マークで強調
- 情報が不足している場合は正直に伝える

回答:"""
        
        response = self.llm.invoke(prompt)
        return {"final_answer": response.content}
    
    def query(self, question: str) -> dict:
        """質問に回答"""
        initial_state = {
            "question": question,
            "messages": [HumanMessage(content=question)],
            "iteration": 0,
            "final_answer": None
        }
        
        result = self.graph.invoke(initial_state)
        
        # ツール呼び出し回数をカウント
        tool_call_count = sum(
            1 for m in result.get("messages", [])
            if isinstance(m, AIMessage) and hasattr(m, "tool_calls") and m.tool_calls
        )
        
        return {
            "answer": result.get("final_answer", "回答を生成できませんでした"),
            "iterations": result.get("iteration", 0),
            "tool_calls": tool_call_count
        }
    
    def query_stream(self, question: str):
        """
        質問に回答（ストリーミング版）
        
        Yields:
            (event_type, data) タプル:
            - "metadata": 初期情報（戦略、イテレーション等）
            - "token": 回答テキストの一部
            - "done": 完了シグナル
            - "error": エラーメッセージ
        """
        try:
            initial_state = {
                "question": question,
                "messages": [HumanMessage(content=question)],
                "iteration": 0,
                "final_answer": None
            }
            
            # グラフを実行（ツール呼び出し部分）
            # generate ノードを除いた状態まで実行する必要があるが、
            # LangGraph の compile() 後のグラフは途中停止が難しいため、
            # 代わりにフルグラフを実行して最終プロンプトを再構築してストリーム
            
            result = self.graph.invoke(initial_state)
            
            # ツール呼び出し回数をカウント
            tool_call_count = sum(
                1 for m in result.get("messages", [])
                if isinstance(m, AIMessage) and hasattr(m, "tool_calls") and m.tool_calls
            )
            
            # ツール結果を抽出
            tool_results = []
            sources = []
            for msg in result.get("messages", []):
                if isinstance(msg, ToolMessage):
                    tool_results.append(f"[{msg.name}]: {msg.content}")
                    # ソースURLを抽出
                    try:
                        import json
                        data = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and item.get("url"):
                                    sources.append({
                                        "project_name": item.get("name") or item.get("project_name"),
                                        "url": item.get("url"),
                                        "is_winner": item.get("is_winner", False)
                                    })
                        elif isinstance(data, dict) and data.get("results"):
                            for item in data["results"]:
                                if isinstance(item, dict) and item.get("url"):
                                    sources.append({
                                        "project_name": item.get("project_name"),
                                        "url": item.get("url"),
                                        "is_winner": bool(item.get("is_winner"))
                                    })
                    except:
                        pass
            
            # メタデータをyield
            yield ("metadata", {
                "strategy": "agentic_rag",
                "explanation": f"iterations={result.get('iteration', 0)}, tool_calls={tool_call_count}",
                "sources": sources[:10]
            })
            
            # 最終回答がすでに生成されている場合（非ストリーミングで生成済み）
            # ストリーミング用に再生成
            prompt = f"""以下の検索結果を参考に、ユーザーの質問に日本語で回答してください。

## ユーザーの質問
{question}

## 検索結果
{chr(10).join(tool_results) if tool_results else "検索結果なし"}

## 回答ガイドライン
- 具体的なプロジェクト名を挙げながら説明
- 受賞作品は🏆マークで強調
- 情報が不足している場合は正直に伝える

回答:"""
            
            # ストリーミングで回答を生成
            for chunk in self.llm.stream(prompt):
                if chunk.content:
                    yield ("token", chunk.content)
            
            yield ("done", None)
            
        except Exception as e:
            yield ("error", str(e))


# シングルトン（max_iterations はデフォルト値を使用）
_agentic_rag = None

def get_agentic_rag(max_iterations: int = 3) -> AgenticRAG:
    global _agentic_rag
    if _agentic_rag is None or _agentic_rag.max_iterations != max_iterations:
        _agentic_rag = AgenticRAG(max_iterations=max_iterations)
    return _agentic_rag
