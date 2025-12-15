---
title: "【AI Agent Hackathon】WanderLens - あなたの冒険を、もっと鮮やかに。"
url: "https://zenn.dev/yuulin/articles/632e987d8edc73"
author: ""
published_at: "2025-02-10T14:49:41+00:00"
scraped_at: "2025-12-14T13:14:49.807875"
---

#  AIによる次世代お出かけコンパニオン

##  ⭐️ 概要

今回、AI Agent Hackathon with Google Cloudに参加させていただきました。  
WanderLensは、Gemini Multimodal Live APIを活用した次世代のお出かけサポートアプリケーションです。カメラを通じた視覚的なAI解析、リアルタイムな情報提供、そしてパーソナライズされた案内を組み合わせることで、ユーザーにこれまでにない豊かな外出体験を実現します。

<https://youtu.be/vkWUWjnJFMU>

##  📖 背景と解決する問題

###  観光産業における課題

  1. **インバウンド観光の急速な回復と対応の遅れ**

     * 2023年の訪日外国人旅行者数は2,519万人で、コロナ前（2019年）の80%まで回復[1]
     * 2024年は3,500万人、2030年には6,000万人の目標に向けて、受入体制の整備が急務[2]
     * 特に地方部での対応の遅れが顕著[3]
  2. **言語と文化のバリア**

     * 観光庁の調査によると、訪日外国人の約23%が「言語の壁」を課題として挙げている[4]
     * 文化的な背景の理解不足による観光体験の質の低下
  3. **観光産業の構造的課題**

     * ８割の宿泊施設が「人手不足を感じている」[5]
     * 地方部での多言語対応スタッフの確保が困難
     * デジタル化による生産性向上の必要性[6]
  4. **持続可能な観光の実現**

     * 特定の観光地への過度な集中（オーバーツーリズム）
     * 地域文化の保護と観光振興のバランス

###  ターゲットユーザー

  1. **訪日外国人旅行者**

     * 言語の壁に直面している観光客
     * 日本の文化や習慣に不慣れな旅行者
     * 個人旅行（FIT）の増加に伴う、よりパーソナライズされたサポートを求める層
  2. **観光関連事業者**

     * 多言語対応に課題を抱える飲食店・小売店
     * 人手不足に悩む観光施設
     * インバウンド対応の効率化を目指す地域の観光協会
  3. **地域住民・国内旅行者**

     * 新しい観光スポットの発掘に興味がある層
     * 地域の文化や歴史により深く触れたい人々
     * バリアフリー観光を必要とする旅行者

###  現状の課題

  1. **言語と文化のバリア**

     * 海外だけでなく国内のお出かけにおいても、現地の言葉や文化に不慣れな場合、情報収集や交渉が困難
     * 看板や案内の理解が即座に必要な場面での対応
  2. **リアルタイムサポートの不足**

     * 従来の観光アプリでは状況変化への柔軟な対応が困難
     * 複数のアプリを行き来する必要があり、ユーザー体験が分断
  3. **複数機能の統合不足**

     * 翻訳、ナビゲーション、予約、現地情報提供など、複数のサービスが統合されていない
     * アプリ間を行き来する必要があり、ユーザー体験が分断

##  💡ソリューション

WanderLensは、単なる観光アプリではなく、真のAIエージェントとして機能します：

  * **自律的な判断** ：ユーザーの状況を理解し、最適なツールを選択
  * **継続的な学習** ：会話履歴と行動パターンからユーザー理解を深化
  * **マルチエージェント連携** ： 
    * 対話エージェント（Multimodal Live API）
    * セッション分析エージェント（Vertex AI）
    * ツール制御エージェント（Function Calling）

###  主要機能

WanderLensの中核となるのは、Googleが提供するMultimodal Live APIです。

!

Multimodal Live APIは試験中の機能であるため、動作が不安定な時があります。

<https://ai.google.dev/gemini-api/docs/multimodal-live?hl=ja>

  1. **AIカメラガイド**

     * カメラを通じた環境認識とリアルタイム情報提供
     * 建物、看板、メニューなどの即時認識と解説
     * ARオーバーレイによる直感的な情報表示
  2. **インテリジェントナビゲーション**

     * ユーザーの好みを考慮した最適ルート提案
     * 周辺スポットのリアルタイム提案
     * 歩行者に特化した細やかなルート案内[7]
  3. **パーソナライズされた体験**

     * Firestoreを活用した会話履歴の永続化
     * ユーザーの興味・好みに基づく推薦
     * 過去の訪問履歴を活用した提案
  4. **ツール統合による拡張機能**

     * searchNearbyPlaces: ユーザーの現在位置周辺の施設や観光スポットを検索
     * getDirections: 現在位置から目的地までの経路案内を提供
     * translateText: 画像やテキストの翻訳を、ユーザーの使用言語に合わせて実施
     * updateSessionSummary: セッション内の会話内容を要約し、Firestoreに保存
     * googleSearch: 不明点がある場合は、最新情報を取得するために使用
     * 状況にあわせて使用すべきツールをプロンプトで明確に指示

###  技術スタック

![](images/img_000.png)

  * **フロントエンド**

    * Next.js
    * TailwindCSS
    * Framer Motion
  * **バックエンド**

    * Gemini Multimodal Live API（リアルタイムマルチモーダル処理）
    * Firebase Authentication
    * Firestore
    * Cloud Run
  * **ツールの呼び出しによるAPI統合**

    * Google Places API
    * Google Maps JavaScript API
    * Translation API
    * Vertex AI

####  AIエージェントアーキテクチャの特徴

  * リアルタイムセッション管理 
    * WebSocketによる双方向通信
    * 状態管理の最適化
  * マルチモーダル処理パイプライン 
    * 画像/音声/テキストの統合処理
    * コンテキスト考慮型レスポンス生成

##  💪実装における工夫

###  1\. AIエージェントとしての独自性とMultimodal Live APIの活用

  * リアルタイムのマルチモーダル処理による状況理解と画像・音声処理の実現
  * コンテキストを考慮した自律的な判断と文脈理解による応答生成
  * ユーザーとの自然な対話による体験の個人化とストリーミングレスポンスによる低遅延な対話体験

プロンプト
    
    
    You are WanderLens, an Out-and-About Companion to help users enjoy their outings by offering real-time interpretation, local navigation, cultural insights, and practical travel tips. Whether the user is looking for directions, local attractions, or language assistance, provide clear and helpful support.
    
    **Behavior:**
    - **Clear and Accessible Communication:**  
      - Use simple and concise language suitable for travelers who may not be experts in the local language.
      - Speak clearly and at a moderate pace; ensure that responses are brief and to the point.
    - **Image Analysis & Expansion:**  
      When an image is sent—whether it's of a landmark, scenery, or text—analyze it and broaden the discussion by mentioning related topics and offering contextual insights.
    - **Context Awareness and Personalization:**  
      - Incorporate the user's current location and previously stored preferences (e.g., favorite cuisines, interest in historical sites) to tailor recommendations.
      - If the user provides images (e.g., a picture of a station or signboard), analyze and translate them accurately to offer relevant local information.
    - **Interactive Guidance:**  
      - Prompt the user for clarifications when details are ambiguous.
      - Confirm collected information before proceeding.
    - **Real-Time Responsiveness:**  
      - Continuously update recommendations based on new inputs, ensuring that responses remain timely and contextually relevant.
    - **Avoid Hallucination:**  
      - Provide responses based only on verifiable data from the available tools. If uncertain, ask for clarification rather than assuming details.
    - **Cultural Sensitivity:**  
      - Adapt responses to respect local customs and language nuances.
    - **Response Style:**  
      - Keep responses clear, concise, and at a pace that allows the user time to think and reply.  Provide advice and recommendations in a friendly and engaging manner.
      - Do not hallucinate—if uncertain, ask for clarification.  
      - Incorporate contextual cues from previously saved session memories to personalize responses.
    - **Tool Usage Guidelines:**  
      - Use **searchNearbyPlaces** to find local attractions or facilities based on keywords and location data.  User's current location is basically provided, so you don't need to ask for it.
      - Use **getDirections** to provide step-by-step walk or bicycle instructions based on user images or queries. Please note that train or bus transit info is not able at this moment. User's current location is basically provided, so you don't need to ask for it.
      - Use **translateText** to translate any text as needed so that the response is always in the user's language.  
      - Use **updateSessionSummary** to keep track of recent conversation context and ensure continuity across sessions. Use this tool if the user asks you to specifically remember something.
      - Use **googleSearch** proactively when the user's query lacks sufficient detail.
    

###  2\. 技術的革新とUI/UX最適化

  * Gemini Multimodal Live APIの先進的な活用

    * リアルタイムの視覚・音声認識と自然言語処理の統合
    * マルチモーダルな情報提示とARを活用した直感的な情報表示
    * Framer Motionを活用したスムーズなアニメーション実装
  * ツール連携による実用的な機能提供

    * Places APIとの連携による場所検索
    * Maps Platform活用による歩行ナビゲーション
    * Translation APIによる翻訳対応
    * Vertex AIによる切断時Session Reportの生成
    * プログレッシブレンダリングの採用による快適なUX

###  3\. データ管理とパーソナライゼーション

  * セッション管理の最適化

    * Firestoreを活用したセッションデータの永続化
    * updateSessionSummaryツールによる会話履歴の保持
    * コンテキストベースのメモリ検索の実装
  * シームレスな体験の提供

    * リアルタイムフィードバックによる対話性の向上
    * 機能統合による一貫した体験
    * 直感的なUIおよび説明の実装

###  開発過程での課題と解決策

  1. **排他的出力制限**

     * **課題** :

       * Multimodal Live APIの日本語・中国語の発音品質が不十分
       * 音声合成の品質により聞き取れない時がある
       * オーディオ/テキスト出力の片方しか選べない
       * 会話および検索内容のテキスト保存が必要
     * **解決策** :

       * 初期段階: テキスト出力 + 言語検出による各言語のText to Speech API音声合成の自動選択
       * 最終的に: オーディオ出力モード + テキストレスポンス保存するツールを実装
  2. **セッション間の文脈維持**

     * **課題** : 
       * multimodal live apiによるセッション切替時のメモリ消失
       * 会話の連続性が失われる
     * **解決策** : 
       * updateSessionSummaryツールの実装
       * セッション終了前の自動要約機能
       * Firestoreへの会話履歴・関心事項の保存
       * 新セッション開始時の文脈復元
       * セッション切断時GeminiによるSession Reportの生成
  3. **UX最適化**

     * **課題** : 
       * スポット検索結果やナビゲーションを音声形式だけで提供するのはわかりにくい
       * 複雑な機能の直感的なUIを提供するのが必要
     * **解決策** : 
       * ARオーバーレイによる直感的な情報表示
       * プログレッシブUIの実装
       * ユーザーフィードバックに基づく継続的改善

###  学びと気づき

  1. **AI活用の最適化**

     * Gemini APIの特性を活かしたプロンプト設計の重要性
     * マルチモーダル処理におけるパフォーマンスとUXのバランス
     * エッジケースへの対応とエラーハンドリングの重要性
  2. **アーキテクチャ設計**

     * マイクロサービスとモノリスのトレードオフ
     * スケーラビリティを考慮したコンポーネント設計
  3. **ユーザー中心設計**

     * 実際のユースケースに基づく機能設計の重要性
     * フィードバックループの確立
     * アクセシビリティへの配慮

##  🧪 テスト方法

###  デモアプリを試す

  1. デモアプリにアクセス（審査員の方はGithub上でリンクをご確認ください。）
  2. Googleアカウントもしくはメールアドレスでログイン
  3. 「接続する」ボタンをクリックしてWanderLensを起動
  4. 以下の機能を試してみてください：（ユーザーはテキスト入力、音声入力どちらでも可） 
     * 📸 カメラを起動して建物や看板を撮影しながら質問（今日の天気、写っているものについてなど何でもOK）
     * 💬 周辺スポットについて質問（例：渋谷駅近辺のカフェを探して）
     * 🗺️ 行きたい場所までのナビゲーションを依頼（歩行や自転車に限る）

####  🎯 テストのポイント

  * **マルチモーダル機能** : 画像認識と会話の自然な連携
  * **コンテキスト理解** : 会話の文脈を踏まえた応答
  * **Toolの使用** : シームレスの連携およびユーザーの好みや状況に応じた提案

####  デモリンク（Public Use)

下記は一般公開向けのリンクですので、動かなくなった場合、  
審査員の方はGithub上のリンクを使用してください。  
<https://wanderlens-public-291413861120.asia-northeast1.run.app/>

!

現在、一部機能は試験運用中のため、動作が不安定な場合があります。  
エラーが発生した場合は、ページをリロードしてお試しください。

##  🚀 今後の展望

  1. **機能拡張**

     * 音声認識の強化と自然な対話の実現
     * 電話予約代行機能の拡充
     * AR技術の更なる活用
  2. **プラットフォーム展開**

     * iOS/Androidネイティブアプリ化
     * オフライン機能の強化
     * ウェアラブルデバイスへの対応
  3. **ビジネス展開**

     * 地域事業者とのAPI連携
     * プレミアム機能の提供
     * グローバル展開の検討

##  📝 まとめ

WanderLensは、最新のAI技術を活用して、お出かけ時の様々な課題を解決する革新的なソリューションです。単なる情報提供に留まらず、ユーザーの状況を理解し、最適なサポートを提供することで、より豊かな体験を創出します。

開発過程で直面した技術的課題を創造的に解決し、ユーザー体験を最優先に考えた設計により、実用的かつ革新的なアプリケーションを実現することができました。特にmultimodal live apiの可能性を実感しました。multimodal live apiは試験中では無料なので、Tool Callで呼び出すAPIを除くGeminiによる処理は0円です。試験段階ではありますが、今後の発展が楽しみです。

Gemini APIとGoogle Cloud Platformの各種サービスを統合することで、高度な機能を実現しながらも、シンプルで使いやすいUIを提供することができました。

今後は、ユーザーフィードバックを基に機能の改善と拡張を進め、より多くの人々の外出体験をサポートしていきたいと考えています。WanderLensは、AIによる次世代のお出かけ体験を創造し、人々の生活をより豊かにする可能性を秘めています。

皆さんの冒険が、より鮮やかで充実したものになることを心から願っています。  
**WanderLens — あなたの冒険を、もっと鮮やかに。**

脚注

  1. <https://www.travelvoice.jp/20240117-154950> ↩︎

  2. <https://www.kantei.go.jp/jp/singi/kankorikkoku/dai24/siryou1.pdf> ↩︎

  3. <https://obot-ai.com/local-government/gs_column/819/> ↩︎

  4. <https://www.mlit.go.jp/kankocho/news08_00004.html> ↩︎

  5. <https://finance-frontend-pc-dist.west.edge.storage-yahoo.jp/disclosure/20241007/20241007594239.pdf> ↩︎

  6. <https://www.mlit.go.jp/kankocho/content/810001005.pdf> ↩︎

  7. 現時点、日本でのDirectionサービスは交通機関でのルートを提供していません。 ↩︎

