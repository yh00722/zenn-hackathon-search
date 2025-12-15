"""
SQLite データベースモデルと接続
"""
import sqlite3
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
from contextlib import contextmanager

from .config import settings


# SQLスキーマ
SCHEMA_SQL = """
-- ハッカソンイベントテーブル
CREATE TABLE IF NOT EXISTS hackathons (
    id              INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    edition         INTEGER NOT NULL UNIQUE,
    start_date      TEXT,
    end_date        TEXT,
    source_url      TEXT
);

-- プロジェクトテーブル（コア）
CREATE TABLE IF NOT EXISTS projects (
    id              INTEGER PRIMARY KEY,
    hackathon_id    INTEGER NOT NULL,
    no              INTEGER,
    project_name    TEXT NOT NULL,
    url             TEXT NOT NULL UNIQUE,
    author_type     TEXT,
    author_name     TEXT,
    description     TEXT,
    content_raw     TEXT,
    content_summary TEXT,
    
    -- ソーシャル指標
    likes           INTEGER DEFAULT 0,
    bookmarks       INTEGER DEFAULT 0,
    accessible      INTEGER DEFAULT 1,
    http_status     INTEGER,
    
    -- 受賞情報
    is_winner       INTEGER DEFAULT 0,
    award_name      TEXT,
    award_comment   TEXT,
    is_final_pitch  INTEGER DEFAULT 0,
    
    -- タグ（JSON配列）
    tags            TEXT,
    tech_stacks     TEXT,
    
    -- メタデータ
    article_slug    TEXT,
    created_at      TEXT DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (hackathon_id) REFERENCES hackathons(id)
);

-- インデックス
CREATE INDEX IF NOT EXISTS idx_projects_hackathon ON projects(hackathon_id);
CREATE INDEX IF NOT EXISTS idx_projects_winner ON projects(is_winner);
CREATE INDEX IF NOT EXISTS idx_projects_final ON projects(is_final_pitch);
CREATE INDEX IF NOT EXISTS idx_projects_likes ON projects(likes DESC);
CREATE INDEX IF NOT EXISTS idx_projects_url ON projects(url);
"""


@dataclass
class Project:
    """プロジェクトデータモデル"""
    id: Optional[int]
    hackathon_id: int
    no: int
    project_name: str
    url: str
    author_type: str
    author_name: str
    description: str
    content_raw: Optional[str]
    content_summary: Optional[str]
    likes: int
    bookmarks: int
    accessible: bool
    http_status: Optional[int]
    is_winner: bool
    award_name: Optional[str]
    award_comment: Optional[str]
    is_final_pitch: bool
    tags: Optional[str]
    tech_stacks: Optional[str]
    article_slug: Optional[str]


class Database:
    """SQLiteデータベースマネージャー"""
    
    def __init__(self, db_path: Path = None):
        self.db_path = db_path or settings.SQLITE_DB_PATH
        settings.ensure_dirs()
    
    @contextmanager
    def get_connection(self):
        """データベース接続のコンテキストマネージャー取得"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        """データベーススキーマの初期化"""
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)
            
            # ハッカソンレコードが存在しない場合は挿入
            hackathons = [
                (1, "AI Agent Hackathon Vol.1", 1, None, None, "https://zenn.dev/hackathons/and-and-and-and-and-and-and-and-and-and-and-and-and-and-and"),
                (2, "AI Agent Hackathon Vol.2", 2, None, None, None),
                (3, "AI Agent Hackathon Vol.3", 3, None, None, None),
            ]
            for h in hackathons:
                conn.execute("""
                    INSERT OR IGNORE INTO hackathons (id, name, edition, start_date, end_date, source_url)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, h)
            conn.commit()
        print(f"✅ データベース初期化完了: {self.db_path}")
    
    def get_project_count(self, edition: int = None) -> int:
        """プロジェクト数を取得"""
        with self.get_connection() as conn:
            if edition:
                result = conn.execute(
                    "SELECT COUNT(*) FROM projects WHERE hackathon_id = ?", (edition,)
                ).fetchone()
            else:
                result = conn.execute("SELECT COUNT(*) FROM projects").fetchone()
            return result[0]
    
    def get_projects(self, edition: int = None, limit: int = 100, offset: int = 0) -> list[dict]:
        """プロジェクト取得（オプションでフィルタリング可）"""
        with self.get_connection() as conn:
            if edition:
                rows = conn.execute("""
                    SELECT * FROM projects 
                    WHERE hackathon_id = ? 
                    ORDER BY likes DESC
                    LIMIT ? OFFSET ?
                """, (edition, limit, offset)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM projects 
                    ORDER BY likes DESC
                    LIMIT ? OFFSET ?
                """, (limit, offset)).fetchall()
            return [dict(row) for row in rows]
    
    def get_winners(self, edition: int = None) -> list[dict]:
        """受賞プロジェクトを取得"""
        with self.get_connection() as conn:
            if edition:
                rows = conn.execute("""
                    SELECT * FROM projects 
                    WHERE is_winner = 1 AND hackathon_id = ?
                    ORDER BY likes DESC
                """, (edition,)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM projects 
                    WHERE is_winner = 1
                    ORDER BY hackathon_id, likes DESC
                """).fetchall()
            return [dict(row) for row in rows]


# グローバルデータベースインスタンス
db = Database()
