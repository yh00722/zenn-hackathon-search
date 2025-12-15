"""
FastAPI アプリケーション
=======================
バックエンドAPIのメインエントリーポイント
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import projects, search, chat
from services.database import db

app = FastAPI(
    title="Zenn Hackathon API",
    description="Zenn AI Agent ハッカソン作品の閲覧・検索API",
    version="1.0.0"
)

# フロントエンド用CORSミドルウェア
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.get("/")
async def root():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "ok",
        "message": "Zenn Hackathon API is running"
    }


@app.get("/api/stats")
async def get_stats():
    """データベース統計情報の取得"""
    return {
        "total_projects": db.get_project_count(),
        "edition_1": db.get_project_count(edition=1),
        "edition_2": db.get_project_count(edition=2),
        "edition_3": db.get_project_count(edition=3),
        "winners": len(db.get_winners())
    }
