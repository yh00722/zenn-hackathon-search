"""
Projects API ルーター
======================
ハッカソンプロジェクトの閲覧・フィルタリングエンドポイント
"""
from typing import Optional
from fastapi import APIRouter, Query

from services.database import db

router = APIRouter()


@router.get("")
async def list_projects(
    edition: Optional[int] = Query(None, ge=1, le=3, description="ハッカソン回（1, 2, 3）"),
    limit: int = Query(50, ge=1, le=100, description="取得件数"),
    offset: int = Query(0, ge=0, description="ページネーション用オフセット"),
    winners_only: bool = Query(False, description="受賞作品のみ表示")
):
    """プロジェクト一覧（オプションでフィルタリング可）"""
    if winners_only:
        projects = db.get_winners(edition=edition)
        return {
            "total": len(projects),
            "projects": projects
        }
    
    projects = db.get_projects(edition=edition, limit=limit, offset=offset)
    total = db.get_project_count(edition=edition)
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "projects": projects
    }


@router.get("/winners")
async def get_winners(
    edition: Optional[int] = Query(None, ge=1, le=3, description="ハッカソン回")
):
    """全受賞作品の取得"""
    winners = db.get_winners(edition=edition)
    return {
        "total": len(winners),
        "winners": winners
    }


@router.get("/leaderboard")
async def get_leaderboard(
    edition: Optional[int] = Query(None, ge=1, le=3, description="ハッカソン回"),
    limit: int = Query(20, ge=1, le=50, description="取得件数")
):
    """いいね数ランキングの取得"""
    projects = db.get_projects(edition=edition, limit=limit)
    
    leaderboard = []
    for i, p in enumerate(projects, 1):
        leaderboard.append({
            "rank": i,
            "project_name": p["project_name"],
            "url": p["url"],
            "author_name": p["author_name"],
            "likes": p["likes"],
            "bookmarks": p["bookmarks"],
            "is_winner": bool(p["is_winner"]),
            "award_name": p.get("award_name"),
            "edition": p["hackathon_id"]
        })
    
    return {
        "edition": edition or "all",
        "leaderboard": leaderboard
    }


@router.get("/{project_id}")
async def get_project(project_id: int):
    """IDでプロジェクトを取得"""
    with db.get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        
        if not row:
            return {"error": "プロジェクトが見つかりません"}
        
        return dict(row)
