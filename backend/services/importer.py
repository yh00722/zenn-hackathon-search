"""
データインポーター
==================
CSVメタデータと記事コンテンツをSQLiteデータベースにインポート
"""
import csv
import json
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional

from .config import settings
from .database import db


def get_article_slug(url: str) -> str:
    """URLから記事ディレクトリ名を抽出: username_articleid"""
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    if len(path_parts) >= 3 and path_parts[1] == "articles":
        return f"{path_parts[0]}_{path_parts[2]}"
    return None


def find_article_dir(url: str, edition: int) -> Optional[Path]:
    """指定されたURLの記事ディレクトリを検索"""
    slug = get_article_slug(url)
    if not slug:
        return None
    article_dir = settings.DATA_DIR / "articles" / str(edition) / slug
    if article_dir.exists():
        return article_dir
    return None


def load_article_content(article_dir: Path) -> Optional[str]:
    """記事Markdownコンテンツを読み込み"""
    md_path = article_dir / "article.md"
    if md_path.exists():
        return md_path.read_text(encoding="utf-8")
    return None


def import_csv(csv_path: Path, edition: int, load_articles: bool = True) -> dict:
    """
    単一のCSVファイルをデータベースにインポート
    
    Args:
        csv_path: エンリッチされたCSVファイルへのパス
        edition: ハッカソン回数（1, 2, 3）
        load_articles: マークダウンファイルから記事コンテンツを読み込むか
    
    Returns:
        件数を含む統計辞書
    """
    stats = {"total": 0, "imported": 0, "skipped": 0, "articles_loaded": 0}
    
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    stats["total"] = len(rows)
    
    with db.get_connection() as conn:
        for row in rows:
            url = row.get("URL", "")
            if not url:
                stats["skipped"] += 1
                continue
            
            # 既存かチェック
            existing = conn.execute(
                "SELECT id FROM projects WHERE url = ?", (url,)
            ).fetchone()
            
            if existing:
                stats["skipped"] += 1
                continue
            
            # 作者タイプをパース
            author_raw = row.get("Author/Team", "")
            if "チーム:" in author_raw or "チーム: " in author_raw:
                author_type = "チーム"
                author_name = author_raw.replace("チーム: ", "").replace("チーム:", "")
            else:
                author_type = "個人"
                author_name = author_raw
            
            # 記事スラッグとコンテンツを取得
            article_slug = get_article_slug(url)
            content_raw = None
            
            if load_articles:
                article_dir = find_article_dir(url, edition)
                if article_dir:
                    content_raw = load_article_content(article_dir)
                    if content_raw:
                        stats["articles_loaded"] += 1
            
            # 数値フィールドをパース
            def safe_int(val, default=0):
                if val is None or val == "":
                    return default
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return default
            
            def safe_bool(val):
                if isinstance(val, bool):
                    return val
                return str(val).lower() == "true"
            
            # プロジェクトを挿入
            conn.execute("""
                INSERT INTO projects (
                    hackathon_id, no, project_name, url, author_type, author_name,
                    description, content_raw, content_summary, likes, bookmarks, accessible, http_status,
                    is_winner, award_name, award_comment, is_final_pitch, article_slug,
                    tech_stacks, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                edition,
                safe_int(row.get("No")),
                row.get("Project Name", "Unknown"),
                url,
                author_type,
                author_name,
                row.get("Description", ""),
                content_raw,
                row.get("ContentSummary") or None,  # 新規: 要約
                safe_int(row.get("Likes")),
                safe_int(row.get("Bookmarks")),
                1 if safe_bool(row.get("Accessible", True)) else 0,
                safe_int(row.get("Status")) if row.get("Status", "").isdigit() else None,
                1 if safe_bool(row.get("IsWinner", False)) else 0,
                row.get("AwardName") or None,
                row.get("AwardComment") or None,
                1 if safe_bool(row.get("IsFinalPitch", False)) else 0,
                article_slug,
                row.get("TechStacks") or None,  # 新規: 技術スタック
                row.get("Tags") or None,  # 新規: タグ
            ))
            stats["imported"] += 1
        
        conn.commit()
    
    return stats


def import_all_data(load_articles: bool = True) -> dict:
    """
    すべてのハッカソンデータをCSVファイルからインポート
    
    Returns:
        統合された統計
    """
    print("\n🚀 データインポートを開始...")
    print("=" * 50)
    
    # データベースを初期化
    db.init_db()
    
    total_stats = {"total": 0, "imported": 0, "skipped": 0, "articles_loaded": 0}
    
    for edition in [1, 2, 3]:
        csv_path = settings.DATA_DIR / "csv" / f"{edition}_hackathon_enriched.csv"
        
        if not csv_path.exists():
            print(f"⚠️  CSVが見つかりません: {csv_path}")
            continue
        
        print(f"\n📁 第{edition}回をインポート中: {csv_path.name}")
        
        stats = import_csv(csv_path, edition, load_articles)
        
        for key in total_stats:
            total_stats[key] += stats[key]
        
        print(f"   ✅ インポート: {stats['imported']}")
        print(f"   ⏭️  スキップ: {stats['skipped']}")
        if load_articles:
            print(f"   📄 記事: {stats['articles_loaded']}")
    
    print("\n" + "=" * 50)
    print("📊 インポート完了:")
    print(f"   総プロジェクト数: {total_stats['total']}")
    print(f"   インポート済み: {total_stats['imported']}")
    print(f"   スキップ（重複）: {total_stats['skipped']}")
    print(f"   読込み記事数: {total_stats['articles_loaded']}")
    
    return total_stats


if __name__ == "__main__":
    import_all_data()
