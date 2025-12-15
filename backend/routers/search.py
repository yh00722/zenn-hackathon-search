"""
Search API ルーター
====================
全文検索・セマンティック検索エンドポイント
"""
from typing import Optional
from fastapi import APIRouter, Query

from services.database import db

router = APIRouter()


@router.get("")
async def search_projects(
    q: str = Query(..., min_length=1, description="検索クエリ"),
    edition: Optional[int] = Query(None, ge=1, le=3, description="ハッカソン回"),
    limit: int = Query(20, ge=1, le=50, description="取得件数")
):
    """
    プロジェクトを名前、説明、コンテンツで検索。
    シンプルなSQL LIKE検索（基本機能用）
    """
    search_term = f"%{q}%"
    
    with db.get_connection() as conn:
        if edition:
            rows = conn.execute("""
                SELECT id, project_name, url, author_name, description, 
                       likes, bookmarks, is_winner, award_name, hackathon_id
                FROM projects 
                WHERE hackathon_id = ? AND (
                    project_name LIKE ? OR 
                    description LIKE ? OR 
                    author_name LIKE ?
                )
                ORDER BY likes DESC
                LIMIT ?
            """, (edition, search_term, search_term, search_term, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT id, project_name, url, author_name, description,
                       likes, bookmarks, is_winner, award_name, hackathon_id
                FROM projects 
                WHERE project_name LIKE ? OR 
                      description LIKE ? OR 
                      author_name LIKE ?
                ORDER BY likes DESC
                LIMIT ?
            """, (search_term, search_term, search_term, limit)).fetchall()
    
    results = [dict(row) for row in rows]
    
    return {
        "query": q,
        "edition": edition,
        "count": len(results),
        "results": results
    }


@router.get("/semantic")
async def semantic_search(
    q: str = Query(..., min_length=1, description="検索クエリ（日本語）"),
    k: int = Query(5, ge=1, le=20, description="取得件数")
):
    """
    ベクトル類似度によるセマンティック検索。
    RAGサービスがインデックス済みドキュメントで初期化されている必要あり。
    """
    try:
        from services.rag import get_rag_service
        rag = get_rag_service()
        results = rag.similarity_search(q, k=k)
        
        return {
            "query": q,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        return {
            "error": str(e),
            "hint": "RAGサービスが初期化されていません。先にインデックスを実行してください。"
        }
