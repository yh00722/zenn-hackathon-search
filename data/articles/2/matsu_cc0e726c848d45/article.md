---
title: "予定が含まれたSlackの投稿に、スタンプを押すだけでGoogleカレンダーに登録できるURLを生成してくれるBot"
url: "https://zenn.dev/matsu/articles/cc0e726c848d45"
author: ""
published_at: "2025-06-29T07:32:04+00:00"
scraped_at: "2025-12-14T13:18:07.593646"
---

!

第2回 AI Agent Hackathon with Google Cloudに応募するために作成しました。また、本記事は項目立てやシーケンス図などはAIに作成してもらいました。文章部分は人間（私）が書いています。もちろん人間の目で最終確認もしています。

Slackメッセージにカレンダー絵文字でリアクションするだけで、AI（Gemini）が自動的に予定情報を抽出し、Google Calendarに追加可能なリンクを生成するボットです。非技術部門の人も一瞬で利用出来るようになる利便性を追求しました。

ソースコードは以下にあります。MITライセンスにしてあるので、お好きにカスタマイズしてご利用ください。  
<https://github.com/matsuvr/calendar-slack-bot>

#  プロジェクトのデモ動画

<https://youtu.be/cAIFGSNcwrU>

##  **アイデアのポイント**

###  **シンプルでＬＬＭ時代ならではの処理フロー**

  1. **絵文字トリガー** : Slackでカレンダー📅絵文字をリアクション
  2. **AI解析** : Vertex AIのGeminiが日時・場所・概要を自動抽出
  3. **URL生成** : 抽出データをURLエンコードしてGoogle Calendar リンク作成
  4. **即座の返信** : 元投稿にスレッドでカレンダーリンクを提供

#  プロジェクトが対象とするユーザー像と課題、課題へのソリューションと特徴

職場でSlackを使っていると、ミーティング予定だったり、社内セミナーの告知だったり、飲み会の連絡だったりがいろいろとやりとりされます。これらは書き手それぞれの表現手段、つまり自然言語で書かれていて、構造化されていません。私たちはこれらの告知を見ながら、自分に関係ある予定だったら、それを自分で手作業でカレンダーに入れていくことがほとんどでしょう。

前々から手作業でカレンダーに入れる作業が煩雑だと思っていたので、LLMを使えば自動化できないかなと思って作成したのが本Botになります。Slackへの設定には管理権限が必要ですが、設定してしまえばそのワークスペースにいる人が全員使えるようになります。対象ユーザーは仕事でSlackを使っている人すべてです。

#  システム アーキテクチャ図（簡易版）

仕組みそのものは単純で、Slackでカレンダー📅のスタンプがついたら、スタンプが付いた投稿文をgemini-2.5-flashに送信して、日時、場所、オンラインミーティングのURL、概要などを抽出させます。その抽出された内容から、Google Calendarに登録できるURLを生成して、元投稿にリプライの形で付けるというものです。

あまり応答時間が長いと体験が良くないのと、API料金に怯えたくなかったので安価で高速な gemini-2.5-flash を使っています。ワンチャンGemma賞を狙いたかったので（笑）、一部はGemma 3n 4bEを使っています。

Slackからの通知を受け取ってGeminiにパスして、帰って来たものをSlackに返す中継役としては、Cloud Runを使っています。中身はNode.jsで作成しました。

ちなみにAIエージェントがプログラムの8割くらいは作ってくれました。実力を実感しています。  
![](images/img_000.png)

#  インストール方法

##  **前提条件**

  * Node.js v20以上
  * Slack APIアカウント
  * Google AI Studio（Gemini API）アクセス権
  * Google Cloud Platform（デプロイ時）

##  **環境変数設定**

Cloud Runの環境変数部分に設定します。ローカル開発時は、OSの環境変数に設定してください。
    
    
    SLACK_BOT_TOKEN=xoxb-your-bot-token
    SLACK_SIGNING_SECRET=your-signing-secret
    GOOGLE_CLOUD_PROJECT=your-project-id
    VERTEX_AI_LOCATION=global
    GEMINI_API_KEY=your-gemini-api-key
    SLACK_TEAM_ID=your-team-id
    GEMINI_LITE_MODEL=gemma-3n-e4b-it
    

![](images/img_001.png)  
_Cloud Runの環境変数設定部分でSlackとの連携やGemini APIのキーなどを設定します_

##  **ローカル開発**
    
    
    # 依存関係インストール
    npm install
    
    # 開発サーバー起動
    npm run dev
    
    # テスト実行
    npm test
    

##  **Cloud Runデプロイ**
    
    
    # Dockerイメージビルド
    gcloud builds submit --tag gcr.io/PROJECT_ID/calendar-slack-bot
    
    # Cloud Runデプロイ
    gcloud run deploy calendar-slack-bot \
      --image gcr.io/PROJECT_ID/calendar-slack-bot \
      --platform managed \
      --region us-central1 \
      --allow-unauthenticated
    

実際は、Githubと連携させて、リポジトリにプッシュする度に、自動的にCloud Buildが走るように設定していました。以下の公式ドキュメント通りにすれば大丈夫です！

<https://cloud.google.com/run/docs/continuous-deployment-with-cloud-build?hl=ja>

##  **Slack API設定**

###  **必要なボットスコープ**

  * `channels:history` \- チャンネル履歴の読み取り
  * `channels:read` \- チャンネル情報の読み取り
  * `chat:write` \- メッセージの投稿
  * `reactions:read` \- リアクションの読み取り
  * `reactions:write` \- リアクションの追加

###  **イベントサブスクリプション**

  * **Request URL** : `https://your-domain.com/slack/events`
  * **Subscribe Events** : `reaction_added`

###  **設定手順**

  1. [Slack API Dashboard](https://api.slack.com/apps)で新しいアプリを作成
  2. 上記のボットスコープを設定
  3. イベントサブスクリプションを有効化
  4. アプリをワークスペースにインストール
  5. Bot User OAuth TokenとSigning Secretを環境変数に設定

###  **対応絵文字リアクション**

  * `:calendar:` \- 標準カレンダー絵文字
  * `:カレンダー:` \- 日本語カスタム絵文字
  * `:calendar_spiral:` \- スパイラルカレンダー
  * `:date:` \- 日付絵文字
  * `:カレンダーに入れる:` \- 日本語説明絵文字

config.js内の以下の部分に、Slackのスタンプを追加することで、任意のスタンプをトリガーに出来ます。

config.js
    
    
      // 対応するカレンダー絵文字
      calendarReactions: [
        'calendar', 
        'カレンダー', 
        'calendar_spiral', 
        'date', 
        'カレンダーに入れる', 
        'calendar-bot'
      ],
    

Slack Botの設定は詳しい記事がたくさんあるのでそれらにゆずりますが、以下の様な部分を色々設定することになります。

![](images/img_002.png)

![](images/img_003.png)

![](images/img_004.png)

![](images/img_005.png)

![](images/img_006.png)
