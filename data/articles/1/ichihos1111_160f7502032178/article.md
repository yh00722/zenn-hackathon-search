---
title: "バ先のメニューを多言語化するアプリを作った。"
url: "https://zenn.dev/ichihos1111/articles/160f7502032178"
author: ""
published_at: "2025-02-10T06:58:49+00:00"
scraped_at: "2025-12-14T13:14:24.455679"
---

こちらの記事は[AI Agent Hackathon with Google Cloud](https://zenn.dev/hackathons/2024-google-cloud-japan-ai-hackathon)への応募記事です。

アルバイト先の飲食店での使用を想定して、海外客向けの外国語メニューアプリに生成AIを搭載してみました。初投稿です。

製作したWebアプリ  
<https://anaza-menu.dt.r.appspot.com>

#  はじめに

###  背景

私は大学院生で、学部一回生の頃から続けている飲食店アルバイトがあります。創作料理や名物のシチューなどを提供する居酒屋で、和風の空気を感じられるとても雰囲気の良いお店です。土地柄もありここ数年で海外からの観光客が来店されることも多くなりました。海外の方が苦労されるのはやはり注文で、スムーズな営業には外国語メニューが必要不可欠です。  
以前までは紙媒体の英語メニューをアルバイトが業務時間外にPower Point等で作成し、それを印刷して使用するというアナログ形態で  
・メニュー変更の度に作成→印刷の手順を踏む必要がある  
・作成できる人間が限られている（PCを触れて英語が理解できるアルバイト）  
・対応言語は英語のみ  
・紙媒体のメニューは汚れやすく、管理の手間が増える  
などの課題があり、インバウンドの恩恵を十分に得られているとは言えない状況でした。

###  アプリの概要

外国語メニューをwebアプリの形で作成し、海外からのお客さんにはQRコードを読み取ってもらうことでメニューを表示させます。メニューのデータはfirestoreを使って保管し、店舗用画面からの編集を可能とします。  
メニューの編集には、各言語への翻訳が必要となります。翻訳を行ってくれるAPIは以前より存在したものと思いますが、生成AIを利用することで"わかりやすく"メニューを翻訳することが可能になりました。（例えば、「鰤大根」は直訳では「Yellowtail Radish」だがAIに訳させると「Yellowtail and Daikon Radish Simmered in Soy-Based Sauce」)  
QRコード×飲食店メニューといえば最近目にすることの多くなったセルフオーダーシステムを連想するかも知れませんが、このアプリの目的はオーダーシステムの簡単化ではなく、日本の文化に馴染みのない海外からのお客さんにお店のメニューを効果的に伝えることです。このメニューを使った上で店舗スタッフとお客さんが交流を持つことも、サービス向上の側面から目的にしていることです。

#  システムアーキテクチャ

Flutter Web で構築したフロントエンドを Google Cloud App Engine (GAE) でホスティングし、Firestore や Firebase Storage、Vertex AI といった Google Cloud サービスを利用する構成となっています。ユーザー（海外客・店舗スタッフ）はスマホやPCのブラウザからアプリにアクセスし、メニュー情報の取得・更新や画像のアップロード、翻訳リクエストを行います。

#  アプリの動作

本アプリの主な機能は以下のとおりです。

・メニューの表示  
・言語選択  
・メニューチョイスの保存（お気に入り機能）  
・メニューの追加・編集  
・Vertex AI を使った翻訳  
（未翻訳メニューの一括翻訳、および各メニュー編集画面での翻訳）  
・各メニューの写真のアップロード  
（写真が登録されていない場合はタップで Google 画像検索結果にジャンプ）  
・テーマ色の変更

###  Firestore Databaseからのメニューデータの取得

NoSQL のサーバーレスデータベースである Firestore に保存されているメニューデータを取得し、一覧として表示します。ジャンルごと、ジャンル内でのメニューごとに「表示順」を管理するフィールドを持っており、その順番で上から表示されます。  
各メニューに対応するドキュメントには複数言語のメニュー名が保存されており、ユーザーが選択した言語で表示内容が切り替わります。もし Firestore に該当言語のデータがない場合には、英語メニューを表示する仕様です。  
メニューをタップすると、画像が存在する場合はその画像を表示し、画像が存在しない場合は日本語のメニュー名をキーにして Google の画像検索結果ページにジャンプするようになっています。

###  Firestoreのメニューデータの編集

お客さん用画面の「Food」ボタンを連打するとパスワード画面に遷移し、指定のパスワードを入力すると店舗用編集画面へ進めます。編集画面からはFirestoreへのドキュメントの追加やアップデート、Storageへの画像アップロードが行えます。既存のメニューデータは編集画面に取り込み、TextField のコントローラーに反映しています。画像をアップロードすると、その画像のアクセスURLを Firestore 上の該当ドキュメントに追記する仕組みです。

###  Vertex AIでのメニュー翻訳

Vertex AI API を利用し、メニューを翻訳できるようにしています（モデルは gemini-1.5-flash を想定）。編集画面で言語選択をすると、対象言語に未翻訳のメニューを検索し、一括翻訳処理を実行します。個別のメニューを編集する際には、日本語メニュー名からボタンひとつで直接翻訳できるようになっています。

###  テーマ色変更

おまけ機能として、メニュージャンルを表示する領域のテーマカラーを変更することができます。flutter_color_picker を使って色を選択し、そのカラーコードを Firestore に保存することでアプリ内のテーマ色を変更可能にしています。

<https://youtu.be/FTkpPxY_d3g>

#  工夫ポイント

###  スクロール

本アプリでは、各ジャンルのメニューを ListView にまとめ、それらを更に大きなリストとして配置しているため、スクロール制御に工夫が必要でした。以下の点を調整し、スマホでの自然なスクロールを実現しています。

・レンダラー  
モバイル表示時に、スクロールにともなって画面がちらつく問題がありましたが、  
flutter build --web-renderer canvaskit --no-tree-shake-icons  
を指定して Webレンダラーを canvaskit にすることで解消しました。

・cacheExtent  
リストの入れ子構造が原因でキャッシュ不足が起き、上部へ戻るときに飛びが生じていたので、ジャンル数に応じて cacheExtent を適切に設定し、快適にスクロールできるようにしました。  
参考: <https://qiita.com/umechanhika/items/aad5cb3c32ea39de4355>

・子スクロール→親スクロール  
ジャンル内のリストが下端まで来たとき、同じ指の位置ではこれ以上スクロールできなくなる問題があったため、リスト下端でさらに下へスクロールしようとした場合、親リストのスクロールに処理を譲渡するようにしました。以下のように NotificationListener でスクロールイベントをフックし、Scrollable.ensureVisible で親ビューを動かしています。
    
    
    child: NotificationListener<ScrollNotification>(
            onNotification: (notification) {
              // 上端での下方向スクロールを無視する
              if (notification.metrics.pixels ==
                      notification.metrics.minScrollExtent &&
                  notification is ScrollUpdateNotification &&
                  notification.scrollDelta! > 0) {
                return true; // イベントを消費して親に伝搬させない
              }
              // 下端でさらに下方向にスクロールした場合、親ビューをスクロール
              if (notification.metrics.pixels ==
                      notification.metrics.maxScrollExtent &&
                  notification is OverscrollNotification) {
                Scrollable.ensureVisible(
                  context,
                  duration: const Duration(milliseconds: 1500),
                  alignment: 0.1, // 親ビューのスクロール位置を調整
                );
                return true; // イベントを消費
              }
              // 上端で上方向スクロールした場合、親ビューをスクロール
              if (notification.metrics.pixels ==
                      notification.metrics.minScrollExtent &&
                  notification is OverscrollNotification) {
                Scrollable.ensureVisible(
                  context,
                  duration: const Duration(milliseconds: 1500),
                  alignment: 0.9, // 親ビューのスクロール位置を調整
                );
                return true; // イベントを消費
              }
              return false; // 他のリスナーにも通知を伝える
            },
            child: ListView.builder(
             ...
    

###  CORSエラー回避

flutter web で canvaskit を使う場合、外部サーバーからの画像読み込み時に CORS (オリジン間リソース共有) エラーが発生することがあります。そこで、プロジェクトのルートディレクトリにcors.json ファイルを配置し、  
gsutil cors set cors.json gs://<your-cloud-storage-bucket>  
を実行して CORS を許可するように設定しました。  
<https://firebase.google.com/docs/storage/web/download-files?hl=ja#cors_configuration>

###  生成AIクオート制限に関して

未翻訳メニューの一括翻訳を行う際、gemini API へのリクエストによって generate content のクォータ制限（単一リージョン・単一モデルに対して5回/分）に抵触する場合があります。そこで、3秒間隔でアクセスし、エラー発生時に待機・リトライする仕組みを設け、全件の翻訳完了まで処理を継続するようにしました。  
（複数リージョンへのリクエストをローテーションさせようと試みましたが、Firebase SDK がリージョン情報をキャッシュしているらしく、実現は難しいようです。）

#  今後

現状は1店舗限定のメニューアプリですが、データモデルを拡張して単一のサービス化を図り、様々な店舗に対応できる形にすることで、多くの方に利用していただけるのではないかと考えています。
