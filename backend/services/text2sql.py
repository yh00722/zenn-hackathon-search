"""
Text2SQL
========
構造化データベースクエリのためのLLMベースSQL生成
"""
import json
import re
import sqlite3
from typing import Optional

from langchain_openai import AzureChatOpenAI
from .config import settings
from .database import db


TEXT2SQL_PROMPT = """
あなたはSQLクエリ生成アシスタントです。ユーザーの質問に基づいてSQLiteクエリを生成してください。

## データベーステーブル構造

projects テーブル:
- id: INTEGER (主キー)
- project_name: TEXT (プロジェクト名)
- url: TEXT (Zenn記事URL)
- author_type: TEXT ('個人' または 'チーム')
- author_name: TEXT (作者名)
- description: TEXT (説明)
- likes: INTEGER (いいね数)
- bookmarks: INTEGER (ブックマーク数)
- is_winner: INTEGER (1=受賞, 0=非受賞)
- award_name: TEXT (賞の名前、NULLの場合あり)
- award_comment: TEXT (審査員コメント、NULLの場合あり)
- hackathon_id: INTEGER (1=第1回, 2=第2回, 3=第3回)
- is_final_pitch: INTEGER (1=最終選考進出, 0=それ以外)
- content_summary: TEXT (記事要約、NULLの場合あり)

hackathons テーブル:
- id: INTEGER (1, 2, 3)
- name: TEXT (ハッカソン名)
- edition: INTEGER (回数)

## ルール

1. SELECTクエリのみ生成可能
2. DELETE, UPDATE, INSERT, DROP は絶対に禁止
3. 日本語のカラム値は正確に（例：'チーム', '個人'）
4. 結果は最大50件に制限 (LIMIT 50)
5. NULL値の可能性を考慮

## よく使うパターン

- いいね数ランキング: ORDER BY likes DESC
- 受賞作品: WHERE is_winner = 1
- 特定の回: WHERE hackathon_id = N
- チーム作品: WHERE author_type = 'チーム'

## 出力形式 (JSON のみ)

{{
  "sql": "SELECT ...",
  "explanation": "このクエリの説明"
}}

ユーザーの質問：{question}
"""


class Text2SQLGenerator:
    """LLMベースのSQLクエリジェネレーター"""
    
    # 禁止されているSQLキーワード
    FORBIDDEN_KEYWORDS = ["DELETE", "UPDATE", "INSERT", "DROP", "ALTER", "CREATE", "TRUNCATE", "EXEC", "--"]
    
    def __init__(self, llm: AzureChatOpenAI = None):
        if llm is None:
            if not settings.AZURE_OPENAI_API_KEY:
                raise ValueError("AZURE_OPENAI_API_KEYが設定されていません")
            self.llm = AzureChatOpenAI(
                azure_deployment=settings.AZURE_CHAT_DEPLOYMENT,
                openai_api_key=settings.AZURE_OPENAI_API_KEY,
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_version=settings.AZURE_OPENAI_API_VERSION
            )
        else:
            self.llm = llm
    
    def generate_sql(self, question: str) -> dict:
        """
        自然言語の質問からSQLクエリを生成
        
        Args:
            question: 日本語のユーザー質問
        
        Returns:
            sqlとexplanationを含む辞書
        """
        prompt = TEXT2SQL_PROMPT.format(question=question)
        response = self.llm.invoke(prompt)
        content = response.content.strip()
        
        # JSONを抽出
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            content = json_match.group()
        
        try:
            result = json.loads(content)
            sql = result.get("sql", "")
            explanation = result.get("explanation", "")
        except json.JSONDecodeError:
            return {"error": "SQLレスポンスのパースに失敗しました", "sql": None}
        
        # SQLを検証
        if not self._is_safe_sql(sql):
            return {"error": "生成されたSQLは安全性チェックに失敗しました", "sql": None}
        
        return {
            "sql": sql,
            "explanation": explanation
        }
    
    def _is_safe_sql(self, sql: str) -> bool:
        """SQLクエリが安全か確認（SELECTのみ）"""
        if not sql:
            return False
        
        sql_upper = sql.upper().strip()
        
        # SELECTで始まる必要がある
        if not sql_upper.startswith("SELECT"):
            return False
        
        # 禁止キーワードをチェック
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in sql_upper:
                return False
        
        return True
    
    def execute(self, question: str) -> dict:
        """
        SQLクエリを生成して実行
        
        Args:
            question: ユーザー質問
        
        Returns:
            結果とメタデータを含む辞書
        """
        # SQLを生成
        gen_result = self.generate_sql(question)
        
        if gen_result.get("error"):
            return gen_result
        
        sql = gen_result["sql"]
        
        # クエリを実行
        try:
            with db.get_connection() as conn:
                cursor = conn.execute(sql)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                # 辞書のリストに変換
                results = []
                for row in rows:
                    results.append(dict(zip(columns, row)))
                
                return {
                    "sql": sql,
                    "explanation": gen_result.get("explanation"),
                    "columns": columns,
                    "row_count": len(results),
                    "results": results
                }
        except sqlite3.Error as e:
            return {
                "error": f"SQL実行エラー: {str(e)}",
                "sql": sql
            }


# よく使うクエリ用のクイックSQLテンプレート
SQL_TEMPLATES = {
    "top_likes": """
        SELECT id, project_name, url, author_name, likes, bookmarks, 
               is_winner, award_name, hackathon_id
        FROM projects 
        ORDER BY likes DESC 
        LIMIT {limit}
    """,
    "winners": """
        SELECT id, project_name, url, author_name, likes,
               award_name, award_comment, hackathon_id
        FROM projects 
        WHERE is_winner = 1
        {edition_filter}
        ORDER BY hackathon_id, likes DESC
    """,
    "winner_comments": """
        SELECT project_name, award_name, award_comment, url
        FROM projects
        WHERE is_winner = 1 AND award_comment IS NOT NULL
        {edition_filter}
        ORDER BY hackathon_id
    """,
    "count_by_edition": """
        SELECT hackathon_id, COUNT(*) as count
        FROM projects
        GROUP BY hackathon_id
        ORDER BY hackathon_id
    """,
    "teams": """
        SELECT id, project_name, url, author_name, likes, hackathon_id
        FROM projects
        WHERE author_type = 'チーム'
        ORDER BY likes DESC
    """
}


def execute_template(template_name: str, **kwargs) -> dict:
    """定義済みSQLテンプレートを実行"""
    if template_name not in SQL_TEMPLATES:
        return {"error": f"不明なテンプレート: {template_name}"}
    
    sql = SQL_TEMPLATES[template_name]
    
    # パラメータを適用
    edition = kwargs.get("edition")
    edition_filter = f"AND hackathon_id = {int(edition)}" if edition else ""
    limit = kwargs.get("limit", 10)
    
    sql = sql.format(limit=limit, edition_filter=edition_filter)
    
    try:
        with db.get_connection() as conn:
            cursor = conn.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            results = [dict(zip(columns, row)) for row in rows]
            
            return {
                "template": template_name,
                "row_count": len(results),
                "results": results
            }
    except sqlite3.Error as e:
        return {"error": str(e)}
