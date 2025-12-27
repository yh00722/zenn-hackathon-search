"""
RAG (Retrieval Augmented Generation) サービス
==============================================
ベクトルストレージにChromaDB、埋め込みとチャットにOpenAI/Azure OpenAIを使用
"""
from pathlib import Path
from typing import Optional

from langchain_chroma import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import settings
from .database import db
from .llm_factory import get_chat_llm, get_embeddings, check_llm_available


# 日本語RAGプロンプト
RAG_PROMPT_JA = PromptTemplate(
    template="""あなたはZenn AI Agent Hackathonの作品に詳しいアシスタントです。
以下のコンテキスト（検索された関連記事）を参考に、ユーザーの質問に日本語で回答してください。

コンテキスト:
{context}

質問: {question}

回答（具体的なプロジェクト名を挙げながら説明してください）:""",
    input_variables=["context", "question"]
)


class RAGService:
    """ハッカソンプロジェクトクエリ用RAGサービス"""
    
    def __init__(self):
        settings.ensure_dirs()
        
        # APIキーが設定されているか確認
        if not check_llm_available():
            raise ValueError("OpenAI APIキーが設定されていません。.envファイルを設定してください。")
        
        # 埋め込みの初期化（Azure/OpenAI 自動選択）
        self.embeddings = get_embeddings()
        
        # LLMの初期化（Azure/OpenAI 自動選択）
        self.llm = get_chat_llm()
        
        # ベクトルストアの初期化（content_raw 用）
        self.vectorstore = Chroma(
            persist_directory=str(settings.CHROMA_DB_PATH),
            embedding_function=self.embeddings,
            collection_name="hackathon_projects"
        )
        
        # 2段階検索用: content_summary ベクトルストア
        self.summary_vectorstore = Chroma(
            persist_directory=str(settings.CHROMA_DB_PATH) + "_summary",
            embedding_function=self.embeddings,
            collection_name="project_summaries"
        )
        
        # retriever は summary を使用、k=8 に変更
        self.retriever = self.summary_vectorstore.as_retriever(search_kwargs={"k": 8})
    
    def index_projects(self, edition: Optional[int] = None) -> int:
        """
        データベースからベクトルストアにプロジェクトをインデックス
        
        Args:
            edition: フィルタリングするハッカソン回（オプション）
        
        Returns:
            インデックスされたドキュメント数
        """
        print("🔄 プロジェクトをChromaDBにインデックス中...")
        
        # コンテンツを含むプロジェクトを取得
        projects = db.get_projects(edition=edition, limit=1000)
        
        # 長い記事用のテキストスプリッター
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200,
            separators=["\n\n", "\n", "。", ".", " "]
        )
        
        documents = []
        for project in projects:
            # コンテンツがない場合はスキップ
            content = project.get("content_raw") or project.get("description") or ""
            if not content or len(content) < 50:
                continue
            
            # メタデータを作成
            metadata = {
                "project_id": project["id"],
                "project_name": project["project_name"],
                "url": project["url"],
                "edition": project["hackathon_id"],
                "author_name": project["author_name"],
                "likes": project["likes"],
                "is_winner": bool(project["is_winner"]),
                "award_name": project.get("award_name") or "",
            }
            
            # 長いコンテンツを分割
            chunks = text_splitter.split_text(content)
            
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={**metadata, "chunk_index": i}
                )
                documents.append(doc)
        
        if documents:
            # ベクトルストアに追加
            self.vectorstore.add_documents(documents)
            print(f"✅ {len(projects)}プロジェクトから{len(documents)}ドキュメントチャンクをインデックスしました")
        else:
            print("⚠️ インデックスするドキュメントがありません")
        
        return len(documents)
    
    def index_summaries(self, edition: Optional[int] = None) -> int:
        """
        content_summary を別のベクトルストアにインデックス（2段階検索用）
        
        Args:
            edition: フィルタリングするハッカソン回（オプション）
        
        Returns:
            インデックスされたドキュメント数
        """
        print("🔄 要約をChromaDBにインデックス中...")
        
        projects = db.get_projects(edition=edition, limit=1000)
        
        documents = []
        for project in projects:
            summary = project.get("content_summary") or ""
            if not summary or len(summary) < 20:
                continue
            
            metadata = {
                "project_id": project["id"],
                "project_name": project["project_name"],
                "url": project["url"],
                "edition": project["hackathon_id"],
                "author_name": project["author_name"],
                "likes": project["likes"],
                "bookmarks": project.get("bookmarks", 0),
                "is_winner": bool(project["is_winner"]),
                "award_name": project.get("award_name") or "",
            }
            
            doc = Document(
                page_content=summary,
                metadata=metadata
            )
            documents.append(doc)
        
        if documents:
            self.summary_vectorstore.add_documents(documents)
            print(f"✅ {len(documents)}件の要約をインデックスしました")
        else:
            print("⚠️ インデックスする要約がありません")
        
        return len(documents)
    
    def query(self, question: str) -> dict:
        """
        2段階検索でRAGクエリを実行
        
        Stage 1: content_summary でセマンティック検索（精度重視）
        Stage 2: content_raw を取得してLLMコンテキストに使用（情報量重視）
        
        Args:
            question: 日本語のユーザー質問
        
        Returns:
            回答とソースドキュメントを含む辞書
        """
        # Stage 1: summary で関連プロジェクトを検索
        summary_docs = self.retriever.invoke(question)
        
        # Stage 2: 関連プロジェクトの content_raw を取得
        project_ids = [doc.metadata.get("project_id") for doc in summary_docs]
        
        # content_raw を取得
        full_contents = []
        with db.get_connection() as conn:
            for pid in project_ids:
                if pid:
                    row = conn.execute(
                        "SELECT project_name, content_raw FROM projects WHERE id = ?",
                        (pid,)
                    ).fetchone()
                    if row and row[1]:
                        # 長すぎる場合はトランケート
                        content = row[1][:2000] if len(row[1]) > 2000 else row[1]
                        full_contents.append(f"## {row[0]}\n\n{content}")
        
        # コンテキストを構築（content_raw から）
        if full_contents:
            context = "\n\n---\n\n".join(full_contents)
        else:
            # フォールバック: summary を使用
            context = "\n\n---\n\n".join([doc.page_content for doc in summary_docs])
        
        docs = summary_docs  # sources 用に保持
        
        # プロンプトをフォーマット
        prompt = RAG_PROMPT_JA.format(context=context, question=question)
        
        # LLMレスポンスを取得
        response = self.llm.invoke(prompt)
        
        sources = []
        for doc in docs:
            sources.append({
                "project_name": doc.metadata.get("project_name"),
                "url": doc.metadata.get("url"),
                "edition": doc.metadata.get("edition"),
                "is_winner": doc.metadata.get("is_winner"),
            })
        
        # URLで重複除去
        seen_urls = set()
        unique_sources = []
        for src in sources:
            if src["url"] not in seen_urls:
                seen_urls.add(src["url"])
                unique_sources.append(src)
        
        return {
            "answer": response.content,
            "sources": unique_sources
        }
    
    def similarity_search(self, query: str, k: int = 5) -> list[dict]:
        """
        LLM生成なしの類似度検索を実行
        
        Args:
            query: 検索クエリ
            k: 結果数
        
        Returns:
            メタデータ付きのマッチするドキュメントリスト
        """
        docs = self.vectorstore.similarity_search(query, k=k)
        
        results = []
        for doc in docs:
            results.append({
                "content": doc.page_content[:500],
                "metadata": doc.metadata
            })
        
        return results


# 遅延初期化
_rag_service: Optional[RAGService] = None

def get_rag_service() -> RAGService:
    """RAGサービスシングルトンの取得または作成"""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
