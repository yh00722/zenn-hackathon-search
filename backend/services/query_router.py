"""
クエリルーター
==============
インテリジェントな検索戦略選択のための純粋LLMベースのクエリ分類とルーティング。
すべてのルーティング決定は多様なユーザー表現を処理するためにLLMによって行われる。
"""
import json
import re
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from .config import settings
from .llm_factory import get_chat_llm, check_llm_available


class QueryStrategy(Enum):
    """利用可能なクエリ戦略"""
    TEXT2SQL = "text2sql"
    FILTERED_RAG = "filtered_rag"
    SEMANTIC_RAG = "semantic_rag"
    KEYWORD_SEARCH = "keyword_search"
    HYBRID = "hybrid"


@dataclass
class QueryPlan:
    """クエリ実行プラン"""
    strategy: str
    rewritten_query: str
    filters: Optional[dict] = None
    sql_hint: Optional[str] = None
    explanation: Optional[str] = None
    
    @property
    def strategy_enum(self) -> QueryStrategy:
        return QueryStrategy(self.strategy)


ROUTER_PROMPT = """
あなたはZenn AI Agent Hackathonデータベースのクエリルーティングアシスタントです。
ユーザーの質問を分析し、最適な検索戦略を選択してください。

## データベース情報

Zenn AI Agent Hackathonは3回開催され、約400のプロジェクトがあります。
各プロジェクトには以下の情報が含まれています：
- プロジェクト名、URL、説明
- 作者名、作者タイプ（個人/チーム）
- いいね数、ブックマーク数
- 受賞フラグ、賞の名前、審査員コメント
- 開催回（第1回、第2回、第3回）
- 最終選考進出フラグ

## 検索戦略

1. **text2sql**: 数値データや正確な情報が必要な場合
   - ランキング（人気順、いいね数順）
   - 統計・集計（件数、合計）
   - 一覧表示（受賞者リスト、コメント一覧）
   - 特定条件の完全一致検索
   例: 「人気作品は？」「評価が高いプロジェクト」「受賞者のコメントを見せて」「チームで参加した作品」

2. **filtered_rag**: 特定グループについて深い理解が必要な場合
   - 受賞作品の分析
   - 特定回の傾向・技術トレンド
   - 特定グループの共通点・特徴
   例: 「受賞作品に共通する点」「第3回で評価された技術」「優勝作品の特徴」

3. **semantic_rag**: オープンな探索・技術的な質問
   - 特定分野のプロジェクト探索
   - 技術的な実装方法
   - アイデア・インスピレーション
   例: 「ヘルスケア関連のプロジェクト」「LangChainの使い方」「面白いアイデアは？」

4. **keyword_search**: 特定の技術名・キーワードで検索
   - 特定技術を使ったプロジェクト
   - 特定キーワードを含む作品
   例: 「Firebase使用例」「RAGを実装した作品」

5. **hybrid**: 複数の条件が組み合わさる場合
   例: 「受賞作品でRAGを使ったものの詳細」

## フィルター条件の検出

質問から以下の条件を検出してfiltersに設定してください：
- 受賞・入賞・優勝 → {{"is_winner": true}}
- 第1回・Vol.1・1回目 → {{"hackathon_id": 1}}
- 第2回・Vol.2・2回目 → {{"hackathon_id": 2}}
- 第3回・Vol.3・3回目 → {{"hackathon_id": 3}}
- 決勝・最終選考・ファイナル → {{"is_final_pitch": true}}
- チーム・チーム参加 → {{"author_type": "チーム"}}

## 重要なポイント

- ユーザーは様々な言い方で同じ意図を表現する可能性があります
- 「人気」「評価が高い」「いいね多い」は全て text2sql でランキング
- 「どんな」「どういう」「傾向」「共通点」は分析が必要なので filtered_rag または semantic_rag
- 曖昧な場合は semantic_rag を選択

## 出力形式 (JSON のみ)

{{
  "strategy": "text2sql|filtered_rag|semantic_rag|keyword_search|hybrid",
  "rewritten_query": "検索に最適化されたクエリ",
  "filters": {{"is_winner": true, "hackathon_id": 3}},
  "sql_hint": "必要なSQLの種類（text2sqlの場合）",
  "explanation": "この戦略を選択した理由"
}}

ユーザーの質問：{question}
"""


class QueryRouter:
    """
    純粋LLMベースのクエリルーター。
    
    すべてのルーティング決定はLLMによって行われ、
    多様なユーザー表現と自然言語の変化に対応。
    """
    
    def __init__(self, llm = None):
        if llm is None:
            if not check_llm_available():
                raise ValueError("OpenAI APIキーが設定されていません")
            # LLMの初期化（Azure/OpenAI 自動選択）
            self.llm = get_chat_llm()
        else:
            self.llm = llm
    
    def route(self, question: str) -> QueryPlan:
        """
        LLMを使用して質問を分析し、実行プランを生成。
        
        LLMはユーザーが同じ意図を表現する様々な方法を理解し、
        キーワードマッチングよりも堅牢なルーティングを実現。
        
        Args:
            question: 任意の自然な表現によるユーザー質問
        
        Returns:
            戦略、フィルター、実行パラメータを含むQueryPlan
        """
        if not question or not question.strip():
            return QueryPlan(
                strategy="semantic_rag",
                rewritten_query=question or "",
                explanation="空の質問のため、デフォルトのセマンティック検索を使用"
            )
        
        prompt = ROUTER_PROMPT.format(question=question)
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            # レスポンスからJSONを抽出
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                content = json_match.group()
            
            plan_dict = json.loads(content)
            
            return QueryPlan(
                strategy=plan_dict.get("strategy", "semantic_rag"),
                rewritten_query=plan_dict.get("rewritten_query", question),
                filters=plan_dict.get("filters"),
                sql_hint=plan_dict.get("sql_hint"),
                explanation=plan_dict.get("explanation")
            )
        
        except json.JSONDecodeError:
            # パース失敗時はセマンティックRAGにフォールバック
            return QueryPlan(
                strategy="semantic_rag",
                rewritten_query=question,
                explanation="LLMレスポンスのパースに失敗、セマンティックRAGにフォールバック"
            )
        except Exception as e:
            # LLMエラーを適切に処理
            return QueryPlan(
                strategy="semantic_rag",
                rewritten_query=question,
                explanation=f"LLMエラー: {str(e)}、セマンティックRAGにフォールバック"
            )
