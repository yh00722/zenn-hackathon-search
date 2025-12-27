"""
ハイブリッドクエリ実行エンジン
==============================
複数の戦略を組み合わせたインテリジェントなクエリ実行エンジン
"""
import json
from typing import Optional
from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate

from .config import settings
from .database import db
from .llm_factory import get_chat_llm, get_embeddings, check_llm_available
from .query_router import QueryRouter, QueryPlan, QueryStrategy
from .text2sql import Text2SQLGenerator, execute_template


# 回答生成プロンプト
ANSWER_PROMPT = """
あなたはZenn AI Agent Hackathonの作品に詳しいアシスタントです。
以下の検索結果を参考に、ユーザーの質問に日本語で丁寧に回答してください。

## 検索結果

{context}

## ユーザーの質問

{question}

## 回答ガイドライン

1. 具体的なプロジェクト名を挙げながら説明
2. 数値データがある場合は正確に引用
3. 受賞作品は「🏆」マークで強調
4. 回答は構造化して読みやすく

回答：
"""


class HybridQueryExecutor:
    """
    ハイブリッドクエリ実行エンジン。
    クエリを最適な戦略にインテリジェントにルーティングして実行。
    """
    
    def __init__(self):
        settings.ensure_dirs()
        
        if not check_llm_available():
            raise ValueError("OpenAI APIキーが設定されていません")
        
        # LLMの初期化（Azure/OpenAI 自動選択）
        self.llm = get_chat_llm()
        
        # 埋め込みの初期化（Azure/OpenAI 自動選択）
        self.embeddings = get_embeddings()
        
        # ベクトルストアの初期化
        self.vectorstore = Chroma(
            persist_directory=str(settings.CHROMA_DB_PATH),
            embedding_function=self.embeddings,
            collection_name="hackathon_projects"
        )
        
        # コンポーネントの初期化
        self.router = QueryRouter(self.llm)
        self.text2sql = Text2SQLGenerator(self.llm)
    
    def query(self, question: str) -> dict:
        """
        純粋なLLMベースのインテリジェントルーティングを使用してクエリを実行
        
        Args:
            question: 日本語のユーザー質問（任意の自然な表現）
        
        Returns:
            回答、ソース、メタデータを含む辞書
        """
        # 1. LLMを使用してクエリをルーティング
        plan = self.router.route(question)
        
        # 2. 戦略に基づいて実行
        if plan.strategy == QueryStrategy.TEXT2SQL.value:
            results = self._execute_text2sql(question, plan)
        elif plan.strategy == QueryStrategy.FILTERED_RAG.value:
            results = self._execute_filtered_rag(question, plan)
        elif plan.strategy == QueryStrategy.SEMANTIC_RAG.value:
            results = self._execute_semantic_rag(question, plan)
        elif plan.strategy == QueryStrategy.KEYWORD_SEARCH.value:
            results = self._execute_keyword_search(question, plan)
        elif plan.strategy == QueryStrategy.HYBRID.value:
            results = self._execute_hybrid(question, plan)
        else:
            # セマンティックRAGにフォールバック
            results = self._execute_semantic_rag(question, plan)
        
        # 3. 回答を生成
        answer = self._generate_answer(question, results, plan)
        
        return {
            "answer": answer,
            "strategy": plan.strategy,
            "explanation": plan.explanation,
            "sources": results.get("sources", []),
            "sql": results.get("sql")
        }
    
    def _execute_text2sql(self, question: str, plan: QueryPlan) -> dict:
        """Text2SQL戦略を実行"""
        result = self.text2sql.execute(question)
        
        if result.get("error"):
            return {
                "context": f"エラー: {result['error']}",
                "sources": []
            }
        
        # 結果をコンテキストとしてフォーマット
        rows = result.get("results", [])
        if not rows:
            return {
                "context": "該当するデータが見つかりませんでした。",
                "sources": [],
                "sql": result.get("sql")
            }
        
        # コンテキスト文字列を構築
        context_lines = [f"検索結果: {len(rows)}件\n"]
        
        for i, row in enumerate(rows[:20], 1):  # コンテキスト用に20件に制限
            line = f"{i}. "
            if row.get("project_name"):
                line += f"**{row['project_name']}**"
            if row.get("is_winner"):
                line += " 🏆"
            if row.get("author_name"):
                line += f" (by {row['author_name']})"
            if row.get("likes"):
                line += f" - ❤️{row['likes']}"
            if row.get("award_name"):
                line += f" [{row['award_name']}]"
            if row.get("award_comment"):
                line += f"\n   コメント: {row['award_comment']}"
            context_lines.append(line)
        
        sources = [
            {"project_name": r.get("project_name"), "url": r.get("url"), 
             "is_winner": bool(r.get("is_winner"))}
            for r in rows if r.get("url")
        ]
        
        return {
            "context": "\n".join(context_lines),
            "sources": sources[:10],
            "sql": result.get("sql"),
            "row_count": len(rows)
        }
    
    def _execute_filtered_rag(self, question: str, plan: QueryPlan) -> dict:
        """フィルター付きRAG戦略を実行"""
        # ChromaDBフィルターを構築
        chroma_filter = {}
        if plan.filters:
            for key, value in plan.filters.items():
                if key == "is_winner" and value:
                    chroma_filter["is_winner"] = True
                elif key == "hackathon_id":
                    chroma_filter["edition"] = value
                elif key == "is_final_pitch" and value:
                    chroma_filter["is_final_pitch"] = True
        
        # フィルター付きで検索
        try:
            if chroma_filter:
                docs = self.vectorstore.similarity_search(
                    query=plan.rewritten_query or question,
                    k=10,
                    filter=chroma_filter
                )
            else:
                docs = self.vectorstore.similarity_search(
                    query=plan.rewritten_query or question,
                    k=10
                )
        except Exception as e:
            # フィルターなしでフォールバック
            docs = self.vectorstore.similarity_search(
                query=plan.rewritten_query or question,
                k=10
            )
        
        return self._format_rag_results(docs)
    
    def _execute_semantic_rag(self, question: str, plan: QueryPlan) -> dict:
        """純粋なセマンティックRAGを実行"""
        docs = self.vectorstore.similarity_search(
            query=plan.rewritten_query or question,
            k=10
        )
        return self._format_rag_results(docs)
    
    def _execute_keyword_search(self, question: str, plan: QueryPlan) -> dict:
        """キーワードベースのSQL検索を実行"""
        # キーワードを抽出（シンプルなアプローチ）
        keywords = [w for w in question.split() if len(w) > 2]
        
        if not keywords:
            return self._execute_semantic_rag(question, plan)
        
        # パラメータ化クエリを構築
        placeholders = []
        params = []
        for kw in keywords[:3]:  # 最大3キーワード
            placeholders.append("(project_name LIKE ? OR description LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%"])
        
        where_clause = " OR ".join(placeholders)
        sql = f"""
            SELECT id, project_name, url, author_name, description, 
                   likes, is_winner, hackathon_id
            FROM projects 
            WHERE {where_clause}
            ORDER BY likes DESC
            LIMIT 20
        """
        
        try:
            with db.get_connection() as conn:
                rows = conn.execute(sql, tuple(params)).fetchall()
                results = [dict(row) for row in rows]
                
                if not results:
                    return self._execute_semantic_rag(question, plan)
                
                context_lines = [f"キーワード検索結果: {len(results)}件\n"]
                for i, r in enumerate(results[:10], 1):
                    line = f"{i}. **{r['project_name']}**"
                    if r.get("is_winner"):
                        line += " 🏆"
                    context_lines.append(line)
                
                return {
                    "context": "\n".join(context_lines),
                    "sources": [
                        {"project_name": r["project_name"], "url": r["url"],
                         "is_winner": bool(r["is_winner"])}
                        for r in results
                    ]
                }
        except Exception:
            return self._execute_semantic_rag(question, plan)
    
    def _execute_hybrid(self, question: str, plan: QueryPlan) -> dict:
        """ハイブリッド戦略を実行（複数を組み合わせ）"""
        results = []
        
        # まずフィルター付きRAGを試行
        rag_results = self._execute_filtered_rag(question, plan)
        
        # フィルターが構造化クエリを示唆する場合、SQLも実行
        if plan.filters and plan.filters.get("is_winner"):
            sql_results = execute_template("winners", edition=plan.filters.get("hackathon_id"))
            if sql_results.get("results"):
                # コンテキストをマージ
                sql_context = "\n### 受賞作品データ\n"
                for r in sql_results["results"][:5]:
                    sql_context += f"- **{r['project_name']}** 🏆 {r.get('award_name', '')}\n"
                rag_results["context"] = sql_context + "\n" + rag_results.get("context", "")
        
        return rag_results
    
    def _format_rag_results(self, docs: list) -> dict:
        """RAG検索結果をフォーマット"""
        if not docs:
            return {
                "context": "関連するドキュメントが見つかりませんでした。",
                "sources": []
            }
        
        context_parts = []
        sources = []
        seen_urls = set()
        
        for doc in docs:
            meta = doc.metadata
            url = meta.get("url")
            
            if url and url not in seen_urls:
                seen_urls.add(url)
                
                header = f"### {meta.get('project_name', 'Unknown')}"
                if meta.get("is_winner"):
                    header += " 🏆"
                
                context_parts.append(f"{header}\n{doc.page_content[:800]}\n")
                
                sources.append({
                    "project_name": meta.get("project_name"),
                    "url": url,
                    "edition": meta.get("edition"),
                    "is_winner": meta.get("is_winner", False)
                })
        
        return {
            "context": "\n---\n".join(context_parts),
            "sources": sources
        }
    
    def _generate_answer(self, question: str, results: dict, plan: QueryPlan) -> str:
        """LLMを使用して最終回答を生成"""
        context = results.get("context", "")
        
        if not context:
            return "申し訳ありません。関連する情報が見つかりませんでした。"
        
        prompt = ANSWER_PROMPT.format(context=context, question=question)
        
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            return f"回答生成中にエラーが発生しました: {str(e)}"
    
    def query_stream(self, question: str):
        """
        クエリを実行し、回答をトークンごとにストリーム。
        
        Yields:
            (イベントタイプ, データ)のタプル。イベントタイプは：
            - "metadata": 戦略、ソース等の初期情報
            - "token": 回答テキストの一部
            - "done": 完了シグナル
            - "error": エラーメッセージ
        """
        try:
            # 1. LLMを使用してクエリをルーティング
            plan = self.router.route(question)
            
            # 2. 戦略に基づいて実行（queryメソッドと同じ）
            if plan.strategy == QueryStrategy.TEXT2SQL.value:
                results = self._execute_text2sql(question, plan)
            elif plan.strategy == QueryStrategy.FILTERED_RAG.value:
                results = self._execute_filtered_rag(question, plan)
            elif plan.strategy == QueryStrategy.SEMANTIC_RAG.value:
                results = self._execute_semantic_rag(question, plan)
            elif plan.strategy == QueryStrategy.KEYWORD_SEARCH.value:
                results = self._execute_keyword_search(question, plan)
            elif plan.strategy == QueryStrategy.HYBRID.value:
                results = self._execute_hybrid(question, plan)
            else:
                results = self._execute_semantic_rag(question, plan)
            
            # 3. まずメタデータをyield
            yield ("metadata", {
                "strategy": plan.strategy,
                "explanation": plan.explanation,
                "sources": results.get("sources", []),
                "sql": results.get("sql")
            })
            
            # 4. 回答をストリーム
            context = results.get("context", "")
            if not context:
                yield ("token", "申し訳ありません。関連する情報が見つかりませんでした。")
                yield ("done", None)
                return
            
            prompt = ANSWER_PROMPT.format(context=context, question=question)
            
            # ストリーミングを使用
            for chunk in self.llm.stream(prompt):
                if chunk.content:
                    yield ("token", chunk.content)
            
            yield ("done", None)
            
        except Exception as e:
            yield ("error", str(e))


# シングルトンインスタンス
_hybrid_executor: Optional[HybridQueryExecutor] = None

def get_hybrid_executor() -> HybridQueryExecutor:
    """シングルトンインスタンスの取得または作成"""
    global _hybrid_executor
    if _hybrid_executor is None:
        _hybrid_executor = HybridQueryExecutor()
    return _hybrid_executor
