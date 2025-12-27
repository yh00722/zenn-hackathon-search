"""
OpenAI 設定（Azure OpenAI と OpenAI 両対応）
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートから.envを読み込み
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")


class Settings:
    """環境変数から読み込むアプリケーション設定"""
    
    # OpenAI プロバイダー選択: "azure" または "openai"
    OPENAI_PROVIDER: str = os.getenv("OPENAI_PROVIDER", "azure")
    
    # Azure OpenAI 設定
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    AZURE_EMBEDDING_DEPLOYMENT: str = os.getenv("AZURE_EMBEDDING_DEPLOYMENT", "text-embedding-3-large")
    AZURE_CHAT_DEPLOYMENT: str = os.getenv("AZURE_CHAT_DEPLOYMENT", "gpt-4o")
    
    # OpenAI 設定（直接 API）
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
    
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
    
    @classmethod
    def is_azure(cls) -> bool:
        """Azure OpenAI を使用するかどうか"""
        return cls.OPENAI_PROVIDER.lower() == "azure"
    
    @classmethod
    def is_openai(cls) -> bool:
        """OpenAI を直接使用するかどうか"""
        return cls.OPENAI_PROVIDER.lower() == "openai"
    
    @classmethod
    def get_api_key(cls) -> str:
        """現在のプロバイダーのAPIキーを取得"""
        if cls.is_azure():
            return cls.AZURE_OPENAI_API_KEY
        return cls.OPENAI_API_KEY
    
    @classmethod
    def validate(cls) -> bool:
        """設定が有効かどうかを確認"""
        if cls.is_azure():
            return bool(cls.AZURE_OPENAI_API_KEY and cls.AZURE_OPENAI_ENDPOINT)
        return bool(cls.OPENAI_API_KEY)


settings = Settings()
