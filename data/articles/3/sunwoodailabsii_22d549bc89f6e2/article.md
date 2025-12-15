---
title: "【第3回 AI Agent Hackathon】Gemini Baby Monitor - AIが支援するスマート見守りシステム"
url: "https://zenn.dev/sunwoodailabsii/articles/22d549bc89f6e2"
author: ""
published_at: "2025-09-24T14:25:19+00:00"
scraped_at: "2025-12-14T13:25:07.909856"
---

#  プロジェクト概要

本プロジェクトは、第3回 AI Agent Hackathon with Google Cloudへの提出作品として開発した、**Gemini APIを活用したスマートベビーモニターシステム** です。

<https://youtu.be/Ohn3ydnHVYk>

##  対象ユーザー像と課題

###  ターゲットユーザー

  * 新生児・乳幼児を持つ子育て世代
  * 在宅勤務中に赤ちゃんの様子を気にかけたい親
  * 夜間の見守りで安心感を求める家族
  * 遠隔地にいる祖父母など、赤ちゃんの成長を見守りたい親族

###  解決したい課題

  1. **24時間監視の負担** : 赤ちゃんの安全確認のため、親が常に気を配る必要がある
  2. **専門知識不足** : 危険な状況を見逃してしまう可能性
  3. **高価な専用機器** : 市販のベビーモニターは高額で機能が限定的
  4. **リアルタイム性** : 危険な状況への迅速な対応が必要

##  ソリューションの特徴

###  🤖 AI支援による安全チェック

  * **Gemini API** による画像解析で、赤ちゃんの状況を自動判定
  * 危険な状況や異常を検知し、日本語で分かりやすく説明
  * 専門知識がなくても安心して利用可能

###  🌐 クロスプラットフォーム対応

  * ブラウザベースでデバイスを選ばない
  * HLS/WebRTC対応で低遅延・高画質配信
  * スマートフォン、タブレット、PCどこからでもアクセス可能

###  💰 コスト効率

  * 既存のネットワークカメラを活用
  * Google Cloudの従量課金で無駄なコストを削減
  * オープンソースで拡張・カスタマイズが容易

##  システムアーキテクチャ

###  主要コンポーネント

  1. **自宅ミニPCサーバー**

     * ローカルネットワークカメラとの接続
     * Tailscale VPNクライアントによる安全な通信
     * プライバシー保護されたデータ転送
  2. **Tailscale VPN**

     * 自宅とGCP間の暗号化されたセキュアな接続
     * ゼロコンフィグネットワーキング
     * インターネット経由でもプライベートネットワーク並みの安全性
  3. **MediaMTX (Compute Engine)**

     * RTSPストリームをHLS/WebRTCに変換
     * 複数デバイスからの同時視聴をサポート
     * Docker Composeで統合管理
  4. **Gateway API (Compute Engine)**

     * Gemini APIとの連携窓口
     * 画像解析のプロキシとして動作
     * FastAPIによる高速なレスポンス
  5. **Web UI (Compute Engine)**

     * Nginxによる静的コンテンツ配信
     * レスポンシブデザインでマルチデバイス対応
     * 同一オリジンでの安全なAPI連携

##  技術スタック

###  Google Cloud Services

  * **Compute Engine** : 統合アプリケーション実行環境（MediaMTX、Gateway API、Web UI）
  * **Gemini API** : 画像解析とAI支援機能

###  フロントエンド

  * **HTML5 + JavaScript** : シンプルで軽量なUI
  * **HLS.js** : ブラウザでのHLS再生
  * **Tailwind CSS** : モダンで美しいデザイン

###  バックエンド

  * **FastAPI** : 高性能なPython Webフレームワーク
  * **MediaMTX** : RTSP to WebRTC/HLS変換エンジン
  * **Docker Compose** : 開発環境の統合管理

###  インフラストラクチャ

  * **Terraform** : Infrastructure as Code
  * **GitHub Actions** : CI/CD パイプライン
  * **Tailscale** : ゼロコンフィグVPNによるセキュアな接続

##  実装のポイント

###  1\. リアルタイム画像解析
    
    
    async def analyze_image(
        image: UploadFile = File(...),
        prompt: Optional[str] = Form(None),
    ):
        # Gemini APIで画像を解析
        content = await image.read()
        b64 = base64.b64encode(content).decode("ascii")
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
        
        body = {
            "contents": [{
                "role": "user",
                "parts": [
                    {"inline_data": {"mime_type": image.content_type, "data": b64}},
                    {"text": prompt}
                ]
            }]
        }
    

###  2\. RTSP to WebRTC変換

MediaMTXによる効率的なストリーミング配信で、低遅延での映像視聴を実現しています。

###  3\. セキュアなネットワーク構成

Tailscale VPNによる自宅とGCP間の暗号化通信により、プライベートネットワーク同等のセキュリティを実現しています。これにより、ベビーモニターというプライバシーが重要なアプリケーションでも安心して利用できる環境を構築しました。

##  デモ動画

###  1\. 録画機能デモ

<https://youtu.be/XNmE53g6Tl8>

###  2\. AI解析機能デモ

<https://youtu.be/xSC6dFtUFEw>

> **セキュリティ配慮について**  
>  デモアプリケーションでは、プライバシー保護の観点から実際のベビーモニター映像ではなく、サンプル映像を使用しています。本番環境では自宅のネットワークカメラとTailscale VPNによる暗号化通信で安全性を確保しています。

デモでは以下の機能を確認できます：

  * ライブ映像の配信と視聴
  * WebM形式での録画機能
  * リアルタイム画像解析
  * AI による安全コメント生成
  * レスポンシブデザインの動作

##  リポジトリとデプロイ

  * **GitHub リポジトリ** : <https://github.com/Sunwood-ai-labsII/baby-monitor-web-app>
  * **ライブデモ** : <https://sunwood-ai-labsii.github.io/baby-monitor-web-app/>
  * **技術文書** : プロジェクト内のREADMEを参照

##  Google Cloud技術の活用

本プロジェクトは、ハッカソンの必須要件を以下の通り満たしています：

###  Google Cloud アプリケーション実行プロダクト

  * **Compute Engine** : VM上でDocker Composeによる統合環境を構築 
    * MediaMTXサーバーによるRTSP変換処理
    * Gateway API（FastAPI）のホスティング
    * Web UIのNginx配信

###  Google Cloud AI技術

  * **Gemini API** : 画像解析による安全確認機能
  * リアルタイムでの育児支援コメント生成

##  今後の展望

  1. **Gemini Live APIの活用**

     * リアルタイムストリーミング解析による即座の危険検知
     * WebSocketベースの双方向通信で遅延を最小化
     * 音声入力による親の状況報告との連携
  2. **マルチモーダルAIの強化**

     * Gemma等のオープンソースLLMとの組み合わせ
     * 音声・映像・テキストを統合した総合的な状況判断
     * カスタマイズされた育児支援モデルの構築
  3. **通知機能の強化**

     * LINE/Slackとの連携
     * 緊急時の自動アラート
  4. **データ分析機能**

     * 睡眠パターンの分析
     * 成長記録の自動生成

##  まとめ

Gemini Baby Monitorは、Google CloudとAI技術を活用することで、従来のベビーモニターでは実現できなかった「AI支援による安全確認」を実現しました。親の負担を軽減しながら、より安心できる育児環境の提供を目指しています。

第3回 AI Agent Hackathonを通じて、AIと子育てを組み合わせた新しい価値の創造に挑戦できたことを嬉しく思います。今後も継続的な改善を行い、より多くの子育て世代に役立つサービスへと発展させていきたいと考えています。

* * *

**プロジェクト情報**

  * 開発者: maki (Sunwood AI Labs)
  * 開発期間: 2025年9月
  * ライセンス: MIT License
  * 技術スタック: Google Cloud, Gemini API, Python, Docker, JavaScript

