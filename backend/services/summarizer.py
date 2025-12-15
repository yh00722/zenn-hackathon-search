"""
LLM Content Summarizer
======================
Uses Azure OpenAI gpt-4o Vision to analyze articles and images.
"""
import json
import base64
from pathlib import Path
from typing import Optional

from openai import AzureOpenAI

from .config import settings


SYSTEM_PROMPT_JA = """あなたはハッカソン作品を分析する技術アシスタントです。
日本語の記事と画像を分析し、構造化された情報を抽出してください。
画像にはアプリのスクリーンショット、アーキテクチャ図、デモ動画のサムネイルなどが含まれることがあります。"""

USER_PROMPT_JA = """以下のハッカソン作品記事と画像を分析し、JSON形式で以下の情報を抽出してください：

1. summary: プロジェクト概要（2-3文）
2. problem: 解決しようとしている課題
3. solution: 技術的なアプローチ・ソリューション
4. tech_stack: 使用技術（配列形式、例: ["Firebase", "Flutter", "Gemini API"]）
5. domain_tags: 分野タグ（配列形式、例: ["教育", "ヘルスケア", "生産性向上"]）
6. target_users: 想定ユーザー（例: "高齢者", "学生", "開発者"）
7. ui_description: 画像から読み取れるUI/UXの特徴（オプショナル）

記事内容：
{content}
"""


def encode_image_to_base64(image_path: Path) -> str:
    """Encode image to base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_image_media_type(image_path: Path) -> str:
    """Get image MIME type"""
    suffix = image_path.suffix.lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp"
    }.get(suffix, "image/png")


class ArticleSummarizer:
    """Multimodal article summarizer using Azure OpenAI gpt-4o"""
    
    def __init__(self):
        if not settings.AZURE_OPENAI_API_KEY:
            raise ValueError("AZURE_OPENAI_API_KEY not configured")
        
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment = settings.AZURE_CHAT_DEPLOYMENT
    
    def summarize(
        self, 
        content: str, 
        images_dir: Optional[Path] = None, 
        max_images: int = 3
    ) -> dict:
        """
        Analyze article and images, generate structured data
        
        Args:
            content: Article markdown text
            images_dir: Path to images directory (optional)
            max_images: Maximum number of images to send (cost control)
        
        Returns:
            Structured analysis result
        """
        # Build multimodal user message
        user_content = []
        
        # Text content
        user_content.append({
            "type": "text",
            "text": USER_PROMPT_JA.format(content=content[:8000])
        })
        
        # Image content (if exists)
        if images_dir and images_dir.exists():
            image_files = list(images_dir.glob("*"))
            image_files = [
                f for f in image_files 
                if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".gif", ".webp"]
            ]
            
            for img_path in image_files[:max_images]:
                try:
                    base64_image = encode_image_to_base64(img_path)
                    media_type = get_image_media_type(img_path)
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{base64_image}",
                            "detail": "low"  # Use low detail to reduce cost
                        }
                    })
                except Exception as e:
                    print(f"Warning: Failed to load image {img_path}: {e}")
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_JA},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        return json.loads(response.choices[0].message.content)
