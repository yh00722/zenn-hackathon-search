"""
Azure OpenAI 設定
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートから.envを読み込み
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")


class Settings:
    """環境変数から読み込むアプリケーション設定"""
    
    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_EMBEDDING_DEPLOYMENT: str = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
    AZURE_CHAT_DEPLOYMENT: str = os.getenv("AZURE_CHAT_DEPLOYMENT", "gpt-4o")
    
    # パス
    PROJECT_ROOT: Path = project_root
    DATA_DIR: Path = project_root / "data"
    DB_DIR: Path = Path(__file__).parent.parent / "db"
    
    # データベース
    SQLITE_DB_PATH: Path = DB_DIR / "hackathon.db"
    CHROMA_DB_PATH: Path = DB_DIR / "chroma"
    
    @classmethod
    def ensure_dirs(cls):
        """必要なディレクトリの存在を確認"""
        cls.DB_DIR.mkdir(parents=True, exist_ok=True)
        cls.CHROMA_DB_PATH.mkdir(parents=True, exist_ok=True)


settings = Settings()
