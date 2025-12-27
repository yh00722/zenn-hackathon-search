"""
Zenn Hackathon MCP Server
=========================
FastMCP 2.0 を使用した Hackathon データ検索・分析サーバー

既存の services モジュールを全て活用し、5つの検索戦略をサポート:
- TEXT2SQL: 自然言語からSQL生成
- FILTERED_RAG: 条件付きセマンティック検索
- SEMANTIC_RAG: 純粋なセマンティック検索
- KEYWORD_SEARCH: キーワードベース検索
- HYBRID: 複数戦略の組み合わせ
"""
import json
from typing import Optional
from pathlib import Path

from fastmcp import FastMCP

# 既存サービスをインポート
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.database import db
from services.config import settings


# FastMCP サーバーを作成
mcp = FastMCP(
    "Zenn Hackathon",
    instructions="""
このサーバーは Zenn AI Agent Hackathon（第1〜3回）の
約400作品を検索・分析するためのツールを提供します。

## 検索戦略

質問の種類に応じて最適な検索方法が自動選択されます:

1. **数値・ランキング系** → Text2SQL（SQL生成）
2. **分析・傾向系** → Filtered RAG（条件付き意味検索）
3. **探索・アイデア系** → Semantic RAG（意味検索）
4. **技術名検索** → Keyword Search
5. **複合クエリ** → Hybrid（複数戦略併用）

## 利用可能なツール

### 基本ツール（LLM不要）
- search_projects: キーワード検索
- get_winners: 受賞作品取得
- get_leaderboard: いいね数ランキング
- get_project: プロジェクト詳細
- get_statistics: 統計情報

### 高度なツール（Azure OpenAI必要）
- intelligent_query: インテリジェント検索（自動戦略選択）
- semantic_search: セマンティック検索
- analyze_query: クエリ分析（戦略のみ判定）
"""
)


# ============================================================
# 基本ツール（LLM不要、SQLiteのみ）
# ============================================================

@mcp.tool
def search_projects(
    query: str = "",
    edition: int | None = None,
    winner_only: bool = False,
    team_only: bool = False,
    limit: int = 20
) -> list[dict]:
    """
    プロジェクトをキーワードで検索します。
    
    SQLiteのLIKE検索を使用。プロジェクト名と説明文から検索します。
    
    Args:
        query: 検索キーワード（空の場合は全件）
        edition: ハッカソン届次 (1, 2, 3)
        winner_only: 受賞作品のみ
        team_only: チーム作品のみ
        limit: 最大取得件数
    
    Returns:
        マッチしたプロジェクトのリスト（いいね順）
    
    Examples:
        - search_projects("RAG") → RAG関連プロジェクト
        - search_projects("", edition=3, winner_only=True) → 第3回受賞作品
    """
    sql = """
        SELECT 
            id, project_name, url, author_name, author_type,
            description, likes, bookmarks,
            is_winner, award_name, hackathon_id
        FROM projects
        WHERE 1=1
    """
    params = []
    
    if query:
        sql += " AND (project_name LIKE ? OR description LIKE ?)"
        search_term = f"%{query}%"
        params.extend([search_term, search_term])
    
    if edition is not None:
        sql += " AND hackathon_id = ?"
        params.append(edition)
    
    if winner_only:
        sql += " AND is_winner = 1"
    
    if team_only:
        sql += " AND author_type = 'チーム'"
    
    sql += " ORDER BY likes DESC LIMIT ?"
    params.append(limit)
    
    with db.get_connection() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [dict(row) for row in rows]


@mcp.tool
def get_winners(edition: int | None = None) -> list[dict]:
    """
    受賞作品の一覧を取得します。
    
    審査員コメント（award_comment）付きで返します。
    
    Args:
        edition: ハッカソン届次 (1, 2, 3)。省略で全届
    
    Returns:
        受賞作品リスト（賞名、審査員コメント含む）
    """
    return db.get_winners(edition)


@mcp.tool
def get_leaderboard(
    edition: int | None = None,
    limit: int = 10,
    include_content: bool = False
) -> list[dict]:
    """
    いいね数ランキングを取得します。
    
    Args:
        edition: ハッカソン届次（省略で全体）
        limit: 取得件数
        include_content: 記事本文を含めるか
    
    Returns:
        いいね数順のプロジェクトリスト
    """
    select_cols = """
        id, project_name, url, author_name, author_type,
        description, likes, bookmarks,
        is_winner, award_name, hackathon_id
    """
    if include_content:
        select_cols += ", content_summary, content_raw"
    
    if edition is not None:
        sql = f"""
            SELECT {select_cols}
            FROM projects
            WHERE hackathon_id = ?
            ORDER BY likes DESC
            LIMIT ?
        """
        params = (edition, limit)
    else:
        sql = f"""
            SELECT {select_cols}
            FROM projects
            ORDER BY likes DESC
            LIMIT ?
        """
        params = (limit,)
    
    with db.get_connection() as conn:
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


@mcp.tool
def get_project(project_id: int) -> dict | None:
    """
    特定のプロジェクトの詳細情報を取得します。
    
    記事本文（content_raw）を含む完全な情報を返します。
    
    ⚠️ 注意: このツールは大量のデータ（記事全文）を返すため、
    本当に詳細が必要な場合のみ使用してください。
    複数のプロジェクトを連続して取得しないでください。
    概要だけが必要な場合は semantic_search_summary を使用してください。
    
    Args:
        project_id: プロジェクトID
    
    Returns:
        プロジェクト詳細。見つからない場合は None
    """
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ?",
            (project_id,)
        ).fetchone()
        return dict(row) if row else None


@mcp.tool
def get_project_by_name(name: str) -> dict | None:
    """
    プロジェクト名でプロジェクトを検索して詳細を取得します。
    
    部分一致で検索し、最もいいね数が多いものを返します。
    
    Args:
        name: プロジェクト名（部分一致）
    
    Returns:
        プロジェクト詳細。見つからない場合は None
    """
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE project_name LIKE ? ORDER BY likes DESC LIMIT 1",
            (f"%{name}%",)
        ).fetchone()
        return dict(row) if row else None


@mcp.tool
def get_statistics() -> dict:
    """
    ハッカソン全体の統計情報を取得します。
    
    Returns:
        - total_projects: 総プロジェクト数
        - by_edition: 届次別プロジェクト数
        - total_winners: 総受賞者数
        - total_likes: 総いいね数
        - average_likes: 平均いいね数
        - team_count: チーム参加数
    """
    return _get_statistics_impl()


def _get_statistics_impl() -> dict:
    """統計情報取得の内部実装"""
    with db.get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        winners = conn.execute("SELECT COUNT(*) FROM projects WHERE is_winner = 1").fetchone()[0]
        likes = conn.execute("SELECT SUM(likes), AVG(likes) FROM projects").fetchone()
        teams = conn.execute("SELECT COUNT(*) FROM projects WHERE author_type = 'チーム'").fetchone()[0]
        
        by_edition = {}
        for e in [1, 2, 3]:
            count = conn.execute(
                "SELECT COUNT(*) FROM projects WHERE hackathon_id = ?",
                (e,)
            ).fetchone()[0]
            by_edition[e] = count
        
        return {
            "total_projects": total,
            "by_edition": by_edition,
            "total_winners": winners,
            "total_likes": likes[0] or 0,
            "average_likes": round(likes[1] or 0, 1),
            "team_count": teams
        }


@mcp.tool
def get_award_comments(edition: int | None = None) -> list[dict]:
    """
    受賞作品の審査員コメントを取得します。
    
    審査員がどのような点を評価したかを確認できます。
    
    Args:
        edition: ハッカソン届次（省略で全届）
    
    Returns:
        プロジェクト名、賞名、審査員コメントのリスト
    """
    sql = """
        SELECT project_name, url, award_name, award_comment, hackathon_id, likes
        FROM projects
        WHERE is_winner = 1 AND award_comment IS NOT NULL
    """
    params = []
    
    if edition is not None:
        sql += " AND hackathon_id = ?"
        params.append(edition)
    
    sql += " ORDER BY hackathon_id, likes DESC"
    
    with db.get_connection() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [dict(row) for row in rows]


@mcp.tool
def search_content(
    query: str,
    edition: int | None = None,
    winner_only: bool = False,
    limit: int = 20
) -> list[dict]:
    """
    記事全文からキーワードを検索します。
    
    プロジェクト名や説明文だけでなく、記事本文（content_raw）からも検索します。
    技術名（LangChain, OpenAI等）を検索する場合に有効です。
    
    Args:
        query: 検索キーワード
        edition: ハッカソン届次 (1, 2, 3)
        winner_only: 受賞作品のみ
        limit: 最大取得件数
    
    Returns:
        マッチしたプロジェクトのリスト
    
    Examples:
        - search_content("LangChain") → LangChain使用プロジェクト
        - search_content("RAG", edition=3) → 第3回のRAG関連作品
    """
    sql = """
        SELECT 
            id, project_name, url, author_name, author_type,
            description, likes, bookmarks,
            is_winner, award_name, hackathon_id
        FROM projects
        WHERE content_raw LIKE ?
    """
    params = [f"%{query}%"]
    
    if edition is not None:
        sql += " AND hackathon_id = ?"
        params.append(edition)
    
    if winner_only:
        sql += " AND is_winner = 1"
    
    sql += " ORDER BY likes DESC LIMIT ?"
    params.append(limit)
    
    with db.get_connection() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [dict(row) for row in rows]


# 技術スタック検出用のキーワードリスト
KNOWN_TECH_KEYWORDS = [
    # LLM/AIサービス
    "OpenAI", "GPT-4", "GPT-3.5", "ChatGPT", "Claude", "Gemini", "Anthropic",
    "Azure OpenAI", "Vertex AI", "Bedrock", "Cohere", "Mistral",
    # フレームワーク
    "LangChain", "LlamaIndex", "Semantic Kernel", "AutoGen", "CrewAI",
    "Dify", "Flowise",
    # ベクトルDB
    "ChromaDB", "Pinecone", "Weaviate", "Qdrant", "Milvus", "FAISS",
    "Supabase", "pgvector",
    # Webフレームワーク
    "Next.js", "React", "Vue", "Nuxt", "Svelte", "Angular",
    "FastAPI", "Flask", "Django", "Express", "NestJS",
    # インフラ/クラウド
    "Vercel", "Firebase", "Supabase", "AWS", "GCP", "Azure",
    "Cloudflare", "Railway", "Render",
    # 言語
    "Python", "TypeScript", "JavaScript", "Go", "Rust",
    # その他
    "Streamlit", "Gradio", "Chainlit", "LangGraph", "LangSmith",
    "Whisper", "DALL-E", "Stable Diffusion", "Notion", "Slack",
]


@mcp.tool
def analyze_tech_stacks(edition: int | None = None) -> dict:
    """
    技術スタックのトレンドを分析します。
    
    記事本文から技術キーワードを検出し、使用頻度を集計します。
    
    Args:
        edition: ハッカソン届次（省略で全体）
    
    Returns:
        - top_technologies: 技術使用頻度Top20
        - total_analyzed: 分析したプロジェクト数
        - by_category: カテゴリ別集計
    """
    sql = "SELECT id, content_raw FROM projects WHERE content_raw IS NOT NULL"
    params = []
    
    if edition is not None:
        sql += " AND hackathon_id = ?"
        params.append(edition)
    
    with db.get_connection() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    
    from collections import Counter
    tech_counter = Counter()
    
    for row in rows:
        content = (row[1] or "").lower()
        for tech in KNOWN_TECH_KEYWORDS:
            if tech.lower() in content:
                tech_counter[tech] += 1
    
    # カテゴリ別に分類
    categories = {
        "LLM/AI": ["OpenAI", "GPT-4", "GPT-3.5", "ChatGPT", "Claude", "Gemini", 
                   "Anthropic", "Azure OpenAI", "Vertex AI", "Bedrock"],
        "Framework": ["LangChain", "LlamaIndex", "Semantic Kernel", "AutoGen", 
                      "CrewAI", "Dify", "Flowise"],
        "VectorDB": ["ChromaDB", "Pinecone", "Weaviate", "Qdrant", "FAISS", 
                     "Supabase", "pgvector"],
        "Web": ["Next.js", "React", "Vue", "FastAPI", "Flask", "Streamlit"],
    }
    
    by_category = {}
    for cat, techs in categories.items():
        by_category[cat] = sum(tech_counter.get(t, 0) for t in techs)
    
    return {
        "top_technologies": dict(tech_counter.most_common(20)),
        "total_analyzed": len(rows),
        "by_category": by_category
    }


@mcp.tool
def get_all_tags() -> dict:
    """
    全タグとその使用頻度を取得します。
    
    プロジェクトに付与されているタグを集計し、使用頻度順に返します。
    
    Returns:
        - tags: タグと使用頻度の辞書（上位50件）
        - total_unique: ユニークなタグの総数
    """
    sql = "SELECT tags FROM projects WHERE tags IS NOT NULL AND tags != '' AND tags != '[]'"
    
    with db.get_connection() as conn:
        rows = conn.execute(sql).fetchall()
    
    from collections import Counter
    tag_counter = Counter()
    
    for row in rows:
        try:
            tags = json.loads(row[0])
            if isinstance(tags, list):
                tag_counter.update(tags)
        except (json.JSONDecodeError, TypeError):
            continue
    
    return {
        "tags": dict(tag_counter.most_common(50)),
        "total_unique": len(tag_counter)
    }


@mcp.tool
def get_bookmarks_ranking(
    edition: int | None = None,
    limit: int = 10
) -> list[dict]:
    """
    ブックマーク数ランキングを取得します。
    
    いいね数とは異なる角度での人気度を確認できます。
    
    Args:
        edition: ハッカソン届次（省略で全体）
        limit: 取得件数
    
    Returns:
        ブックマーク数順のプロジェクトリスト
    """
    sql = """
        SELECT 
            id, project_name, url, author_name,
            likes, bookmarks, hackathon_id, is_winner
        FROM projects
        WHERE bookmarks > 0
    """
    params = []
    
    if edition is not None:
        sql += " AND hackathon_id = ?"
        params.append(edition)
    
    sql += " ORDER BY bookmarks DESC LIMIT ?"
    params.append(limit)
    
    with db.get_connection() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
        return [dict(row) for row in rows]


# ============================================================
# 高度なツール（Azure OpenAI 必要）
# ============================================================

def _check_azure_config() -> bool:
    """OpenAI/Azure OpenAI が設定されているか確認"""
    return settings.validate()



@mcp.tool
def semantic_search_summary(
    query: str,
    k: int = 6,
    edition: int | None = None,
    winner_only: bool = False
) -> list[dict]:
    """
    【推奨】プロジェクト単位の主題検索
    
    ユーザーが「〇〇関連のプロジェクト」「△△を使った作品」など
    主題・テーマで類似プロジェクトを探したい場合に使用。
    
    各プロジェクトの要約（ContentSummary）から検索するため、
    プロジェクト単位で1件ずつ返し、重複なく関連作品を見つけやすい。
    
    Args:
        query: 検索クエリ（自然言語）
        k: 取得件数（デフォルト10）
        edition: ハッカソン届次フィルタ（1, 2, 3）
        winner_only: 受賞作品のみに絞る
    
    Returns:
        類似度順のプロジェクトリスト（要約含む）
    
    Requires:
        Azure OpenAI の設定、ChromaDB 要約インデックス
    
    Examples:
        - "ヘルスケア関連のプロジェクト" → 医療・健康系プロジェクトを発見
        - "RAGを活用した作品" → RAG実装プロジェクトを一覧
        - "教育支援ツール" → 学習・教育系プロジェクトを検索
    """
    if not _check_azure_config():
        return [{"error": "Azure OpenAI が設定されていません"}]
    
    try:
        from services.rag import get_rag_service
        rag = get_rag_service()
        
        # フィルター構築
        chroma_filter = {}
        if edition is not None:
            chroma_filter["edition"] = edition
        if winner_only:
            chroma_filter["is_winner"] = True
        
        # 要約ベクトルストアで検索
        if chroma_filter:
            docs = rag.summary_vectorstore.similarity_search(
                query=query,
                k=k,
                filter=chroma_filter
            )
        else:
            docs = rag.summary_vectorstore.similarity_search(query=query, k=k)
        
        # 結果をフォーマット
        results = []
        for doc in docs:
            results.append({
                "project_name": doc.metadata.get("project_name"),
                "url": doc.metadata.get("url"),
                "author_name": doc.metadata.get("author_name"),
                "edition": doc.metadata.get("edition"),
                "is_winner": doc.metadata.get("is_winner", False),
                "award_name": doc.metadata.get("award_name"),
                "summary": doc.page_content  # 完整摘要
            })
        
        return results
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool
def semantic_search_content(
    query: str,
    k: int = 6,
    edition: int | None = None,
    winner_only: bool = False
) -> list[dict]:
    """
    記事本文からの詳細フラグメント検索
    
    ユーザーが「〇〇の実装方法」「具体的なコード例」「詳細な手順」など
    記事内の特定段落・技術実装の詳細を探したい場合に使用。
    
    記事本文（content_raw）のチャンクから検索するため、
    具体的なコードスニペットや実装詳細を見つけるのに適している。
    
    ※ プロジェクト探索には semantic_search_summary を推奨
    
    Args:
        query: 検索クエリ（自然言語）
        k: 取得件数
        edition: 届次フィルタ
        winner_only: 受賞作品のみ
    
    Returns:
        類似度順のプロジェクトリスト（記事抜粋含む）
    
    Requires:
        Azure OpenAI の設定、ChromaDB インデックス
    
    Examples:
        - "LangGraphの実装方法" → 具体的な実装コードを発見
        - "認証フローの詳細" → 認証実装の段落を検索
    """
    if not _check_azure_config():
        return [{"error": "Azure OpenAI が設定されていません"}]
    
    try:
        from services.rag import get_rag_service
        rag = get_rag_service()
        
        # フィルター構築
        chroma_filter = {}
        if edition is not None:
            chroma_filter["edition"] = edition
        if winner_only:
            chroma_filter["is_winner"] = True
        
        # 検索実行
        if chroma_filter:
            docs = rag.vectorstore.similarity_search(
                query=query,
                k=k,
                filter=chroma_filter
            )
        else:
            docs = rag.vectorstore.similarity_search(query=query, k=k)
        
        # 結果をフォーマット
        results = []
        seen_urls = set()
        for doc in docs:
            url = doc.metadata.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                results.append({
                    "project_name": doc.metadata.get("project_name"),
                    "url": url,
                    "author_name": doc.metadata.get("author_name"),
                    "edition": doc.metadata.get("edition"),
                    "is_winner": doc.metadata.get("is_winner", False),
                    "content_excerpt": doc.page_content
                })
        
        return results
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool
def text_to_sql(question: str, execute: bool = True) -> dict:
    """
    自然言語の質問からSQLクエリを生成・実行します。
    
    ランキング、統計、一覧など構造化されたデータ取得に適しています。
    
    Args:
        question: 自然言語の質問
        execute: Trueの場合は実行結果も返す
    
    Returns:
        - sql: 生成されたSQL
        - explanation: SQLの説明
        - results: 実行結果（executeがTrueの場合）
    
    Requires:
        Azure OpenAI の設定
    
    Examples:
        - "チームで参加した作品は？" → author_type='チーム' で検索
        - "第3回で最もいいねが多い5作品" → hackathon_id=3, ORDER BY likes DESC LIMIT 5
    """
    if not _check_azure_config():
        return {"error": "Azure OpenAI が設定されていません"}
    
    try:
        from services.text2sql import Text2SQLGenerator
        generator = Text2SQLGenerator()
        
        if execute:
            return generator.execute(question)
        else:
            return generator.generate_sql(question)
    except Exception as e:
        return {"error": str(e)}



@mcp.tool
def agentic_query(question: str, max_iterations: int = 3) -> dict:
    """
    Agentic RAG でマルチターン検索を実行します。
    
    LLMが自律的にツールを選択・実行し、十分な情報が集まるまで
    繰り返し検索を行います。通常の intelligent_query より深い分析が可能です。
    
    Args:
        question: 自然言語の質問
        max_iterations: 最大ツール呼び出し回数（デフォルト3、最大5）
    
    Returns:
        - answer: 生成された回答
        - iterations: 実際のイテレーション数
        - tool_calls: 使用されたツール数
    
    Requires:
        Azure OpenAI の設定
    
    Examples:
        - 「受賞作品でRAGを使っているものの技術詳細」 → 複数ツールで深掘り
        - 「第3回の傾向を分析して」 → 統計 + 意味検索を組み合わせ
    """
    if not _check_azure_config():
        return {"error": "Azure OpenAI が設定されていません"}
    
    # 上限を制限
    max_iterations = min(max(1, max_iterations), 3)
    
    try:
        from services.agentic_rag import get_agentic_rag
        agent = get_agentic_rag(max_iterations=max_iterations)
        return agent.query(question)
    except Exception as e:
        return {"error": str(e)}


# ============================================================
# リソース
# ============================================================

@mcp.resource("hackathon://overview")
def hackathon_overview() -> str:
    """Zenn AI Agent Hackathon の概要"""
    stats = _get_statistics_impl()
    
    return f"""# Zenn AI Agent Hackathon

Zenn主催のAIエージェント開発ハッカソンです。
第1回〜第3回まで開催され、累計 **{stats['total_projects']}** 作品が参加しました。

## 各回の参加数

| 届次 | プロジェクト数 |
|------|---------------|
| 第1回 | {stats['by_edition'].get(1, 0)} |
| 第2回 | {stats['by_edition'].get(2, 0)} |
| 第3回 | {stats['by_edition'].get(3, 0)} |

## 統計サマリー

- 🏆 総受賞作品: {stats['total_winners']}
- ❤️ 総いいね数: {stats['total_likes']}
- 📊 平均いいね数: {stats['average_likes']}
- 👥 チーム参加: {stats['team_count']}

## 利用可能なツール

### 基本ツール
- `search_projects`: キーワード検索
- `search_content`: 記事全文検索（技術名検索に最適）
- `get_winners`: 受賞作品一覧
- `get_leaderboard`: いいねランキング
- `get_project`: プロジェクト詳細
- `get_statistics`: 統計情報
- `get_award_comments`: 審査員コメント
- `analyze_tech_stacks`: 技術トレンド

### 高度なツール（Azure OpenAI必要）
- `intelligent_query`: インテリジェント検索
- `semantic_search`: セマンティック検索
- `text_to_sql`: 自然言語→SQL
- `analyze_query`: クエリ分析
"""


@mcp.resource("hackathon://editions/{edition}")
def hackathon_edition(edition: int) -> str:
    """特定届のハッカソン情報"""
    with db.get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM projects WHERE hackathon_id = ?",
            (edition,)
        ).fetchone()[0]
        
        winners = conn.execute("""
            SELECT project_name, author_name, award_name, likes, url
            FROM projects
            WHERE hackathon_id = ? AND is_winner = 1
            ORDER BY likes DESC
        """, (edition,)).fetchall()
        
        top5 = conn.execute("""
            SELECT project_name, author_name, likes, is_winner
            FROM projects
            WHERE hackathon_id = ?
            ORDER BY likes DESC
            LIMIT 5
        """, (edition,)).fetchall()
    
    winner_text = "\n".join([
        f"- 🏆 **[{w[0]}]({w[4]})** by {w[1]} ({w[2]}, {w[3]} likes)"
        for w in winners
    ]) if winners else "（データなし）"
    
    top5_text = "\n".join([
        f"{i+1}. **{t[0]}** by {t[1]} - {t[2]} likes {'🏆' if t[3] else ''}"
        for i, t in enumerate(top5)
    ])
    
    return f"""# Zenn AI Agent Hackathon Vol.{edition}

## 概要

- 参加プロジェクト数: **{count}**
- 受賞者数: **{len(winners)}**

## 受賞作品

{winner_text}

## いいね数 Top 5

{top5_text}
"""


def _get_edition_info(edition: int) -> str:
    """エディション情報取得の内部関数"""
    return hackathon_edition(edition)


# 明示的に各回のリソースを登録
@mcp.resource("hackathon://editions/1")
def hackathon_edition_1() -> str:
    """第1回ハッカソン情報"""
    return _get_edition_info(1)


@mcp.resource("hackathon://editions/2")
def hackathon_edition_2() -> str:
    """第2回ハッカソン情報"""
    return _get_edition_info(2)


@mcp.resource("hackathon://editions/3")
def hackathon_edition_3() -> str:
    """第3回ハッカソン情報"""
    return _get_edition_info(3)


# ============================================================
# プロンプトテンプレート
# ============================================================

@mcp.prompt
def analyze_hackathon(focus: str = "全般") -> str:
    """
    ハッカソン分析用のプロンプトテンプレート
    
    Args:
        focus: 分析の焦点（技術トレンド、受賞傾向、アイデア発想など）
    """
    return f"""以下のハッカソンデータを分析してください。

分析の焦点: **{focus}**

## 推奨する分析手順

1. まず `get_statistics()` で全体像を把握
2. `get_winners()` で受賞作品を確認
3. 焦点に応じて詳細を調査:
   - 技術トレンド → `analyze_tech_stacks()`
   - 人気作品 → `get_leaderboard()`
   - 深掘り → `intelligent_query()` または `semantic_search()`

## 分析観点

- 受賞作品に共通する特徴は？
- 人気作品と受賞作品の違いは？
- 届次ごとのトレンド変化は？
- 成功するプロジェクトの条件は？

必ず具体的なプロジェクト名を挙げながら分析してください。
"""


@mcp.prompt
def ideation_helper(theme: str) -> str:
    """
    新規アイデア発想サポート用プロンプト
    
    Args:
        theme: アイデアのテーマ（例: "教育×AI", "ヘルスケア"）
    """
    return f"""テーマ「{theme}」に関連するAIエージェントのアイデアを探しています。

## 調査手順

1. `search_projects("{theme}")` で関連プロジェクトを検索
2. `semantic_search("{theme}")` で意味的に関連する作品も探索
3. `get_award_comments()` で評価ポイントを確認

## 分析観点

- 既存の類似プロジェクトはあるか？
- それらの技術スタックは？
- 差別化できるポイントは？
- 受賞作品から学べることは？

## 出力形式

1. 関連する既存プロジェクトのサマリー
2. 技術的なアプローチの選択肢
3. 新規アイデアの提案（3つ程度）
4. 差別化戦略の提案
"""


@mcp.prompt
def compare_projects(project_names: str) -> str:
    """
    複数プロジェクトの比較分析用プロンプト
    
    Args:
        project_names: 比較するプロジェクト名（カンマ区切り）
    """
    return f"""以下のプロジェクトを比較分析してください。

対象プロジェクト: {project_names}

## 分析手順

各プロジェクトについて `get_project_by_name()` で詳細を取得してください。

## 比較観点

1. **目的・解決する課題**
2. **技術スタック**
3. **ユーザー体験の特徴**
4. **いいね数・評価**
5. **受賞有無と評価コメント**

## 出力形式

表形式で比較し、各プロジェクトの強み・弱みをまとめてください。
"""


# ============================================================
# エントリーポイント
# ============================================================

def main():
    """CLI エントリーポイント"""
    mcp.run()


if __name__ == "__main__":
    main()
