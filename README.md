# Zenn AI Agent Hackathon Search

Zenn AI Agent Hackathon（第1〜3回）の参加作品を検索・閲覧・RAG問答できるWebアプリケーションです。

## 機能

- **RAGチャット** - 日本語での自然言語質問に対してAIが回答
- **プロジェクト検索** - キーワード・届次でフィルタリング
- **ランキング表示** - いいね数順のリーダーボード
- **受賞作品閲覧** - 審査員コメント付きの受賞作品一覧

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| Backend | FastAPI, SQLite, ChromaDB, LangChain |
| Frontend | Next.js 15, shadcn/ui, Tailwind CSS |
| AI | Azure OpenAI |

## クイックスタート

### 1. 環境設定

```bash
cp .env.example .env
# .envにAzure OpenAIの認証情報を設定
```

### 2. バックエンド起動

```bash
cd backend
uv sync
uv run python -m services.importer  # 初回のみ
uv run uvicorn main:app --reload
```

### 3. ベクトルインデックス構築（初回のみ）

```bash
curl -X POST http://localhost:8000/api/chat/index
```

### 4. フロントエンド起動

```bash
cd frontend
npm install
npm run dev
```

アクセス: http://localhost:3000

## API エンドポイント

| メソッド | パス | 説明 |
|---------|------|------|
| POST | `/api/chat` | RAG問答 |
| GET | `/api/projects` | プロジェクト一覧 |
| GET | `/api/search?q=` | 検索 |
| GET | `/api/stats` | 統計情報 |

## ライセンス

MIT
