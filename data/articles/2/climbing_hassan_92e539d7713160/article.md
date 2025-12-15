---
title: "AI Climbing Tokyo — ボルダリング落下解析で次トライのヒントを生成【第2回 AI Agent Hackathon】"
url: "https://zenn.dev/climbing_hassan/articles/92e539d7713160"
author: ""
published_at: "2025-06-30T00:49:27+00:00"
scraped_at: "2025-12-14T13:18:56.064971"
---

#  はじめに

> 「落ちた原因がわかれば、次は登れるはず」

そんなクライマーの思いを形にしたのが **AI Climbing Tokyo** です。  
スマホで撮った自分のトライ動画をアップロードし、**落下シーン直前後の区間** を指定すると、次トライ時に役立つ一言アドバイスを生成します。

<https://aiclimbingtokyo.com/>

* * *

##  🎥 デモ動画

<https://www.youtube.com/watch?v=MK9hLt7ik-4>

* * *

##  🌍 Bouldering Landscape — なぜ今クライマー向け AI が必要か

###  1\. Olympic Boost & 爆発的な競技人口

  * スポーツクライミングは **東京 2020** から五輪正式競技となり、世界のクライマー人口は **約 4,450 万人** （IFSC 2019 推計）。
  * IFSC の登録競技者（大会出場レベル）は **約 14 万人** 、世界 50 か国超でワールドカップが開催されるまでに拡大しています。

###  2\. 日本は“クライミング大国”

  * 国内の競技者＋愛好家人口は **約 279 万人** 、全国に **約 800 施設** のジムが存在。
  * IFSC ワールドカップでは日本選手が **毎大会ファイナル常連** 。一時は表彰台を独占するほど「世界最強国」と評価されています。

###  3\. “聖地”と呼ばれる日本のジム文化

  * 難度設定とホールド品質の高さで、**海外クライマーが日本遠征でジム巡り** をするケースが多数。
  * **世界のトップ選手が海外から日本へ** 足を運び，練習に励む姿を見かけることも多々ある

###  4\. 動画 × 休憩ルーチンの親和性

  * ボルダリングは 1 トライごとに数分休憩する競技特性があり、その「待ち時間」に動画を振り返る文化が浸透。
  * スマホ三脚撮影 → すぐフォームチェック、が日常のルーチンになっています。

###  5\. トレーニング手法はまだ発展途上

  * 歴史が浅く科学的メソッドや指導体制は手探り段階。
  * 一方で **日本トップ選手はテクニックや Tips を積極発信** 。これらを **RAG** で取り込めば **「日本人プロが隣で解説してくれる」** 体験を作れると考えました。
  * **“Climbing × Japan” ブランド** は世界的に信頼が厚く、本プロジェクトも **海外展開を前提** に開発しています。

> **Why short & fast advice?**  
>  休憩中にサッと読めるよう “一言アドバイス” を重視。Cloud Run + **Gemini 2.0 Flash-lite** で **解析 30 秒以内** を目標にチューニングしています。

* * *

##  ⭐TL;DR（3 行まとめ）

  1. **ユーザー指定の落下区間** を RAG 解析し“一言アドバイス”を生成
  2. Cloud Run × Cloud Storage × Vertex AI (Gemini 2.0 Flash-lite) で **サーバレス & クイックデプロイ**
  3. OSS 公開 → <https://github.com/Hassan-python/Hackathon_aiclimbingtokyo>

* * *

##  🌐システム構成

* * *

##  🛠️ Tech Stack — 技術選定のポイント

レイヤ | 採用技術 | 採用理由・補足  
---|---|---  
**Frontend** | React + TypeScript + Vite + TailwindCSS + PWA | ドラッグ＆ドロップやモバイル撮影動画を直接扱えるレスポンシブ UI  
**Backend** | FastAPI + Hypercorn + FFmpeg |  `async` \+ 型ヒントで高速。FFmpeg で指定区間のみ抽出し通信量を最小化  
**AI / ML** |  **Gemini 2.0 Flash-lite** (Vertex AI) + ChromaDB | Flash‑lite は最速・最廉価。RAG ベクトル DB に ChromaDB  
**Cloud Infra** | Cloud Run / Cloud Build / Cloud Storage / Secret Manager | 最小スケール 0 → **従量ほぼ 0 円**  
**Delivery** | Netlify CDN | フロントを 1 クリックで世界配信  
**DevOps** | GitHub Actions → Cloud Build → Artifact Registry → Cloud Run |  `main` push で自動ビルド & ロールアウト  
**Security** | HTTPS, IAM‑scoped SA, CORS AllowList, Size Quota | 100 MB 超動画はフロントで弾き、Run `--memory 1 Gi` で OOM 防止  
  
> **Design Philosophy** — _“最小コンポーネント × 全自動”_

* * *

##  🔄 CI/CD & サービス連携フロー
    
    
                +-----------+                  +-----------------+
                | Developer |  git push       |   GitHub        |
                +-----------+ --------------->+  Repository     |
                                                 +--------------+
                                                        | trigger
                                                        v
                +-----------+  build/pack   +-----------------+
                | Secret    |-------------->|   Cloud Build   |
                | Manager   |   inject      +-----------------+
                +-----------+                      |
                                                   v  docker image
                                             +-----------------+
                                             | Artifact        |
                                             | Registry        |
                                             +-----------------+
                                                   |
                                                   v  deploy
                                             +-----------------+
                                             |  Cloud Run      |
                                             |  (FastAPI)      |
                                             +-----------------+
                                                   |
                                 REST API & signed URL |
                                                   v
                 +---------+   HTTPS   +-----------------+
                 |  SPA    |<--------- |  End Users      |
                 |(Netlify)|           +-----------------+
                 +---------+  serve static assets
                        ^
                        |
            build -> +-----------------+
                     |   Netlify CI    |
                     +-----------------+
    

###  🧗‍♂️ユーザーフロー（インプット → アウトプット）
    
    
    サイトを開く
       ↓ ① 区間指定モードを選択
       ↓ ② 動画をドラッグ＆ドロップ
       ↓ ③ /upload → Cloud Storage
       ↓ ④ /analyze → Gemini 2.0 Flash‑lite + ChromaDB
       ↓ ⑤ JSON レスポンス
       ↓ ⑥ “一言アドバイス” 表示
    

##  🚀今後の展望

プロジェクトのさらなる発展のため、以下の機能拡張を計画しています：

###  モバイルアプリ展開 📱

  * **iOS・Android アプリ化** : ネイティブアプリとして App Store・Google Play Store でリリース予定
  * スマートフォンでの動画撮影から解析までのシームレスな体験を提供

###  AI 解析機能の強化 🤖

  * **骨格推定機能の追加** : クライマーの関節・筋肉の動きをリアルタイムで解析
  * より詳細な動作分析と改善提案の精度向上
  * 3D 姿勢推定による立体的な動作解析

###  MCP サーバーを用いた RAG 検索技術の高度化 🔍

  * **Model Context Protocol（MCP）サーバーの統合** : クライミング知識ベースへの高速・高精度な検索機能
  * ChromaDB との連携によるより効率的な情報検索とコンテキスト理解
  * 外部クライミング関連データソースとの統合による知識ベースの拡張

これらの機能により、クライミングトレーニングの効果を最大化し、より多くのクライマーの上達をサポートしていきます。
