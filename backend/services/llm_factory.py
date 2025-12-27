"""
LLM/Embeddings ファクトリー
Azure OpenAI と OpenAI の両方をサポートする統一インターフェース
"""
from langchain_openai import (
    AzureChatOpenAI,
    AzureOpenAIEmbeddings,
    ChatOpenAI,
    OpenAIEmbeddings,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings

from .config import settings


def get_chat_llm(temperature: float = 0) -> BaseChatModel:
    """
    チャット用LLMを取得
    
    Args:
        temperature: 生成の温度（0-1）
    
    Returns:
        設定されたプロバイダーのLLMインスタンス
    
    Raises:
        ValueError: APIキーが設定されていない場合
    """
    if settings.is_azure():
        if not settings.AZURE_OPENAI_API_KEY:
            raise ValueError("AZURE_OPENAI_API_KEYが設定されていません")
        
        return AzureChatOpenAI(
            azure_deployment=settings.AZURE_CHAT_DEPLOYMENT,
            openai_api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            temperature=temperature,
        )
    else:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEYが設定されていません")
        
        return ChatOpenAI(
            model=settings.OPENAI_CHAT_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=temperature,
        )


def get_embeddings() -> Embeddings:
    """
    埋め込みモデルを取得
    
    Returns:
        設定されたプロバイダーの埋め込みモデルインスタンス
    
    Raises:
        ValueError: APIキーが設定されていない場合
    """
    if settings.is_azure():
        if not settings.AZURE_OPENAI_API_KEY:
            raise ValueError("AZURE_OPENAI_API_KEYが設定されていません")
        
        return AzureOpenAIEmbeddings(
            azure_deployment=settings.AZURE_EMBEDDING_DEPLOYMENT,
            openai_api_key=settings.AZURE_OPENAI_API_KEY,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )
    else:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEYが設定されていません")
        
        return OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )


def check_llm_available() -> bool:
    """
    LLMが利用可能かどうかを確認
    
    Returns:
        True if LLM is configured and available
    """
    return settings.validate()


def get_provider_info() -> dict:
    """
    現在のプロバイダー情報を取得
    
    Returns:
        プロバイダー情報の辞書
    """
    if settings.is_azure():
        return {
            "provider": "azure",
            "chat_model": settings.AZURE_CHAT_DEPLOYMENT,
            "embedding_model": settings.AZURE_EMBEDDING_DEPLOYMENT,
            "configured": bool(settings.AZURE_OPENAI_API_KEY),
        }
    else:
        return {
            "provider": "openai",
            "chat_model": settings.OPENAI_CHAT_MODEL,
            "embedding_model": settings.OPENAI_EMBEDDING_MODEL,
            "configured": bool(settings.OPENAI_API_KEY),
        }

