---
title: "忙しい人のための料理支援アプリ「ストレスフリーに食卓を!」"
url: "https://zenn.dev/namy3242/articles/59abc680d7b6ef"
author: ""
published_at: "2025-06-30T12:35:22+00:00"
scraped_at: "2025-12-14T13:20:00.853442"
---

本記事は「[第2回 AI Agent Hackathon with Google Cloud](https://zenn.dev/hackathons/google-cloud-japan-ai-hackathon-vol2)」の提出記事になります！

##  はじめに

現代の共働き子育て世代にとって、毎日の献立決めは大きな悩みの一つです。「冷蔵庫にある食材で何が作れるだろう？」「子どもが喜ぶ料理を短時間で作りたい」「レシピを考える時間もない...」そんな日常的な困りごとを解決するために、AI技術とクラウドサービスを活用した料理支援アプリ「ストレスフリーに食卓を!」を開発しました。

本記事では、Flutter、Firebase、Google Cloud AIを組み合わせたモダンな?アプリケーション開発をハッカソンネタとして、設計思想から実装まで解説します。

##  プロジェクト概要

###  ⅰ. 対象ユーザーと課題、ソリューション

**対象ユーザー像**

  * 共働きの子育て世代（20代後半〜40代）
  * 平日は時間に余裕がなく、効率的な料理を求める
  * とはいえ、美味しく作りたいという悩みもある
  * 食材の無駄を減らしたいと考えている
  * スマートフォンを日常的に使用している

**ユーザーが抱える課題**

  1. **献立決めの負担** : 毎日「何を作ろう？」と悩む時間的・精神的負担
  2. **料理の上達** : 料理の腕前に自信がない、子どもが喜ぶ料理を作りたい
  3. **レシピ検索の非効率性** : 手持ちの食材に合うレシピを探すのに時間がかかる
  4. **料理のマンネリ化** : 同じような料理ばかりになってしまう

**ソリューションと特徴**

「ストレスフリーに食卓を!」は以下の機能でこれらの課題を解決します：

  * **冷蔵庫管理** : 食材の在庫状況をカテゴリー別にデジタル化し、視覚的に管理
  * **3種類のレシピ生成機能** : 
    * 在庫ありレシピ：現在の冷蔵庫の食材で作れるレシピ
    * 在庫外レシピ：新しい食材を使ったレシピ（必要な材料を買い物リストに自動追加）
    * 献立生成：1〜3回分から選択可能な献立プラン（時短 or じっくりレシピ）
  * **こだわりレシピ生成** : 調理法、料理ジャンル、こだわり条件を組み合わせた柔軟なレシピ提案
  * **よみもの機能** : AI生成による料理関連ブログ記事の作成・閲覧システム
  * **買い物リスト** : 不足食材の自動追加
  * **献立管理機能** : 未調理・調理済みのステータス管理と詳細レシピ表示

##  デモ動画

<https://youtu.be/9lBQt6VWqBY?si=yfebY92WO4VNyjfF>

##  システムアーキテクチャ

###  ⅱ. システムアーキテクチャ図

**アーキテクチャの特徴**

  1. **レイヤード設計** : ユーザー層→フロントエンド→状態管理→バックエンド→データベース層に分離
  2. **サーバーレス** : Cloud Functionsによるマイクロサービス設計
  3. **リアルタイム同期** : FirestoreとRiverpodによるリアクティブな状態管理
  4. **AI統合** : Gemini AIを中核とした3つのレシピ生成パターン
  5. **クロスプラットフォーム** : FlutterによるWeb/Mobile統合開発

※Mobileは構想のみでデバッグはWebベースで実施。

**主要データフロー**

  * **レシピ生成** : 条件選択 → 生成方法選択 → AI処理 → Firestore保存 → リアルタイム更新
  * **献立管理** : 1〜3回分選択 → 時短/じっくり組み合わせ → ステータス管理 → 調理完了更新
  * **買い物リスト** : 在庫外レシピ → AI材料判定 → 自動追加 → 外部ショッピングサイト連携

##  技術選定と実装詳細

###  ⅲ. Google Cloud、AI技術、Flutter/Firebaseの活用

####  Google Cloud AI技術の利用

**Gemini AI APIの多面的活用**

本プロジェクトの中核を担うのがGemini AI APIです。以下の機能で活用しています：

  1. **柔軟なレシピ生成**

    
    
    def recipe_suggest(request):
        data = request.get_json()
        ingredients = data.get('ingredients', [])
        meal_type = data.get('mealType', '気分')
        extra_condition = data.get('extraCondition', '')
        generate_external = data.get('generateExternal', False)
        
        if generate_external:
            # 在庫外レシピ：新しい食材を使った創造的なレシピ
            prompt = f"""
    以下の条件で新しい食材を使った料理レシピを1件、日本語で提案してください。
    条件: {extra_condition}
    在庫にない新しい食材を積極的に使用してください。
            """
        else:
            # 在庫ありレシピ：手持ち食材を活用
            prompt = f"""
    以下の食材を使って{meal_type}レシピを1件、日本語で提案してください。
    食材: {', '.join(ingredients)}
    追加条件: {extra_condition}
            """
    

3つの異なるレシピ生成パターンを実装し、ユーザーの状況に応じた最適な提案を行います。

  2. **献立プラン自動生成**

    
    
    def generate_meal_plan(ingredients, extra_condition, meal_count):
        recipes = []
        
        # 時短レシピの生成
        for i in range(quick_count):
            quick_recipe = generate_recipe_with_conditions(
                ingredients, f"{extra_condition} 時短 簡単 30分以内"
            )
            quick_recipe['category'] = '時短'
            quick_recipe['mealNumber'] = i + 1
            recipes.append(quick_recipe)
        
        # じっくりレシピの生成
        for i in range(slow_count):
            slow_recipe = generate_recipe_with_conditions(
                ingredients, f"{extra_condition} じっくり 本格的 手作り"
            )
            slow_recipe['category'] = 'じっくり'
            slow_recipe['mealNumber'] = quick_count + i + 1
            recipes.append(slow_recipe)
        
        return recipes
    

1〜3回分の献立を「時短」と「じっくり」レシピの組み合わせで自動生成します。

  3. **食材の在庫判定をAIに任せる**

    
    
    def judge_needed_ingredients(request):
        data = request.get_json()
        recipe_ingredients = data.get('recipe_ingredients', [])
        stock_ingredients = data.get('stock_ingredients', [])
        
        prompt = f"""
    以下のレシピ材料のうち、在庫にない材料で買い物が必要なものを判定してください。
    レシピ材料: {recipe_ingredients}
    在庫材料: {stock_ingredients}
    基本調味料（塩、醤油、砂糖等）は除外してください。
    """
    

在庫外レシピ生成時に、本当に購入が必要な材料のみを正確に判定できるか検討してみました。

  4. **AI記事生成機能**

    
    
    def generate_blog_post(request):
        data = request.get_json()
        topic = data.get('topic', '料理のコツ')
        extra_condition = data.get('extraCondition', '')
        stock_ingredients = data.get('stockIngredients', [])
        
        prompt = f"""
    以下のテーマで料理関連のブログ記事を日本語で作成してください。
    テーマ: {topic}
    追加条件: {extra_condition}
    現在の在庫食材: {', '.join(stock_ingredients)}
    
    記事は以下の構成で作成してください：
    1. 魅力的なタイトル
    2. 導入文
    3. 本文（見出し付きで構造化）
    4. まとめ
    5. 実践的なアドバイス
    
    HTML形式で出力し、読みやすい構成にしてください。
    """
    

**主な特徴：**

  1. **料理に役立つ情報表示** : 食材の使い方や保存方法、調理のコツを含む記事を生成
  2. **在庫連携** : 現在の冷蔵庫の食材を考慮した記事内容の生成
  3. **リッチな表示** : HTMLWidgetを使用した読みやすい?記事表示

####  Google Cloud Platformサービスの活用

**Cloud Functions for Firebase**

サーバーレスアーキテクチャを採用し、以下の関数を実装：

  * `recipe_suggest`: 3種類のレシピ生成を処理するHTTPトリガー関数
  * `ingredient_master_on_create`: 食材マスター登録時のFirestoreトリガー関数
  * `judge_ingredients`: 買い物リスト自動生成用の食材の在庫判定関数

    
    
    @functions_framework.http
    def recipe_suggest(request):
        data = request.get_json()
        ingredients = data.get('ingredients', [])
        meal_type = data.get('mealType', '気分')
        extra_condition = data.get('extraCondition', '')
        generate_external = data.get('generateExternal', False)
        
        # レシピ生成処理
        if generate_external:
            # 在庫外レシピ：創造的な新レシピ生成
            recipes = generate_external_recipes(extra_condition)
        else:
            # 在庫ありレシピ：手持ち食材活用
            recipes = generate_recipes_with_stock(ingredients, meal_type, extra_condition)
        
        return jsonify({"recipes": recipes})
    

ユーザーの選択に応じて異なるプロンプトを使い分け、**在庫活用型と創造型の2つのアプローチ** でレシピを生成できるように工夫しました。

####  Flutter/Firebaseの活用

**Flutterによるクロスプラットフォーム開発**

一つのコードベースでWeb版とモバイル版の両方を開発を志しました。  
※Mobileは構想のみでデバッグはWebベースで実施。

**Firebase Servicesの包括的活用**

  1. **Firebase Authentication** : メールアドレスによる簡単ログイン
  2. **Cloud Firestore** : 以下のコレクション構造で効率的にデータ管理 
     * `users/{userId}/ingredient_inventory`: 食材在庫情報
     * `users/{userId}/shopping_list`: 買い物リスト
     * `users/{userId}/recipes`: 生成されたレシピ
     * `users/{userId}/meal_plans`: 献立プラン
     * `ingredient_master`: 食材マスターデータ
  3. **Firebase Storage** : 食材画像(Imagen3により生成)の効率的な管理

##  今後の展開

現在検討している機能拡張：

  * **ビジュルアルよい表示** : 画像を表示してもっとビジュルアルをよくUIを作りこみたくて、食材の画像やレシピの扉絵の画像はImagen3を活用しましたが、プロンプトの調整が難しく、扉絵に関してはよくわからない人物が出たり、表示の処理も疎かになっています💦
  * **冷蔵庫と個配サービスの連携機能** : 冷蔵庫の食材には在庫の有無のステータスがあり、無い食材について注文提案するなど、個配サービスと連携させて、注文を自動化・効率化する機能(一番やりたかった機能であるが、物品購入というところで障壁が高く断念。。。買い物の手間暇を効率化する方をもっと検討したかったです💦)

##  まとめ

「ストレスフリーに食卓を」は、現代の共働き子育て世代が抱える日常的な課題を、最新のAI技術とクラウドサービスで解決するアプリケーションです。Flutter、Firebase、Google Cloud AIを組み合わせることで、単なるレシピアプリを超えた包括的な食材管理・料理支援システムを検討しました。

今回の開発を通じて、AI技術の実用的な活用方法、サーバーレスアーキテクチャの効果的な設計、そしてユーザビリティを重視したUI/UX改善の重要性を実感できました。非Web系の人間でもこれくらいのことができる現代の技術に感謝しかありません。みなさんも素晴らしきエンジニアライフを！
