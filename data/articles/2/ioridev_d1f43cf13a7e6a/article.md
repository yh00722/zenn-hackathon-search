---
title: "YouTube動画を活用したAI補助語学学習アプリの開発"
url: "https://zenn.dev/ioridev/articles/d1f43cf13a7e6a"
author: ""
published_at: "2025-06-29T04:58:34+00:00"
scraped_at: "2025-12-14T13:17:58.341665"
---

##  はじめに

語学学習において「興味のあるコンテンツで学ぶ」ことと「効率的な復習」の両立は常に大きな課題でした。SwipeLingoは、YouTube動画の字幕を活用して、学習者が興味を持てるコンテンツから語学学習用のフラッシュカードを生成し、科学的な復習システムで効率的な暗記をサポートする新しいタイプの語学学習アプリです。

##  デモ動画

SwipeLingoの実際の使用感をご覧いただけるデモ動画を用意しました：

<https://youtu.be/xdgJHoZ1n9U>

##  開発

コードはすべてAIが実装  
最初のバージョンは RooCode * Gemini がGWの2日間で作ってくれました。

##  対象ユーザーと解決する課題

###  ターゲットユーザー像

  1. **YouTube動画で語学学習をしたい初〜中級者**

     * 日本語⇄英語の学習者がメイン
     * 自分の興味のある分野（料理、ゲーム、テクノロジーなど）で学習したい方
  2. **既存のSRSツール利用者**

     * 効率的な学習方法は知っているが、カード作成の手間に悩んでいる方
     * YouTube動画からの効率的なコンテンツ抽出を求めている方

###  解決する課題とソリューション

**課題1: コンテンツの問題**

  * 教科書的な例文は退屈で実用性に欠ける
  * 興味のある動画から重要フレーズを抽出・整理するのが大変

**ソリューション: AIによる自動センテンスマイニング**

  * YouTube URLを入力するだけで、Firebase AI（Vertex AI Gemini）が字幕から学習価値の高いフレーズを自動抽出
  * 文脈に応じた自然な翻訳を生成

**課題2: 学習効率の問題**

  * 一度学んだ内容を忘れてしまい、定着しない
  * 復習のタイミングが分からず非効率

**ソリューション: 科学的な間隔反復システム（SRS）**

  * エビングハウス忘却曲線に基づいた最適な復習タイミングで通知
  * 個別最適化された復習間隔の自動調整

**課題3: 継続性の問題**

  * 学習が単調で続かない
  * 進捗が見えづらくモチベーション維持が困難

**ソリューション: Tinder風の直感的な学習UI**

  * 右スワイプ（知っている）・左スワイプ（知らない）の簡単操作
  * GitHubスタイルのヒートマップで学習習慣を可視化

###  その他の特徴

  * **TTS音声読み上げ** : ネイティブスピーカーの発音で学習
  * **インタラクティブ字幕** : 動画再生中に字幕の単語をタップしてAI解説を表示

##  システムアーキテクチャ

###  技術スタック

**フロントエンド**

  * Flutter 3.7.2+ / Riverpod / Go Router

**バックエンド**

  * Firebase Suite (Auth, Firestore, Storage, Functions, Analytics)
  * Firebase AI (Vertex AI Gemini) による自然言語処理

**外部連携**

  * YouTube Data API
  * RevenueCat によるサブスクリプション管理

##  実装の工夫点

###  1\. 効率的な字幕処理とAI活用
    
    
    // タイムスタンプ付き字幕データをAIが理解しやすい形式に整形
    final formattedTranscript = captionsWithTimestamps
        .map((caption) {
          final start = caption['start']?.toStringAsFixed(1) ?? '0.0';
          final end = caption['end']?.toStringAsFixed(1) ?? '0.0';
          final text = caption['text'] ?? '';
          return '$start - $end - $text';
        })
        .join('\n');
    
    // JSONスキーマを含むプロンプトでFirebase AI（Vertex AI Gemini）に送信
    final fullPrompt = """
    あなたはプロの言語教育アシスタントです。
    以下のYouTube字幕から、フラッシュカードに適したサイズの1文ペアを作成してください。
    ・カードの表（front）は学習対象言語で、裏（back）はユーザーの母語で生成
    ・難易度をスコアリング（0.0=易～1.0=難）
    ・以下のJSONスキーマに厳密に従った有効なJSONのみを返してください。
    
    JSONスキーマ:
    {
      "videoId": "$videoId",
      "language": "${userTargetLanguageCode.toUpperCase()}",
      "card": [
        {
          "id": "$videoId-XXX",
          "front": "学習対象言語の文",
          "back": "母語への自然な翻訳",
          "start": 12.3,
          "end": 14.1,
          "difficulty": 0.35
        }
      ]
    }
    
    transcript (startSec - endSec - text):
    $formattedTranscript
    """;
    

###  2\. スマートな学習リマインダー

Cloud Functionsを活用し、ユーザーの学習パターンを分析：
    
    
    // 毎日深夜に実行される分析関数
    exports.analyzeUserPattern = functions.pubsub
      .schedule('0 0 * * *')
      .onRun(async (context) => {
        const users = await getUsersWithLearningData();
        
        for (const user of users) {
          const pattern = await analyzeLearningPattern(user);
          const optimalTime = calculateOptimalReminderTime(pattern);
          await updateUserReminderSettings(user.id, optimalTime);
        }
      });
    

###  3\. インタラクティブな字幕学習機能

動画再生中の字幕から単語をタップして、即座に意味やAI解説を取得できます：
    
    
    // 日本語の場合はTinySegmenterで形態素解析
    if (!isTranslated && userModel?.targetLanguageCode == 'ja') {
      words = tinySegmenter.segment(captionText);
    } else {
      // その他の言語はスペースで分割
      words = captionText.split(' ');
    }
    
    // 各単語をタップ可能なウィジェットとして表示
    GestureDetector(
      onTap: () {
        videoPlayerNotifier.selectWord(word);
      },
      child: Text(word, style: subtitleStyle),
    )
    

AI解説生成では、文脈を考慮した詳細な説明を提供：
    
    
    // 単語のAI解説を生成（文脈込み）
    Future<String> getWordExplanation(
      String word,
      String contextSentence, // 前後の字幕を含む文脈
      String wordLanguageCode,
      String userNativeLanguageCode,
    ) async {
      final fullPrompt = """
    あなたはプロの言語教育アシスタントです。
    以下の単語について、文脈を踏まえて解説してください。
    
    - 説明する: この文で単語の使用を説明してください。  
    - 例: この文で使用されている単語の例をさらに挙げてください。
    - 文法: この文で単語の文法を説明してください
    
    単語: "$word"
    文脈: $contextSentence
    """;
      
      return await _callVertexAiApiForPlainText(prompt: fullPrompt);
    }
    

###  4\. SRSアルゴリズムの実装
    
    
    class SRSService {
      // 保持率の計算: R = e^(-t/S)
      double calculateRetention(double timeDays, double strength) {
        return exp(-timeDays / strength);
      }
      
      // 次回復習までの間隔計算
      double calculateNextInterval(double strength, double targetRetention = 0.9) {
        return -strength * log(targetRetention);
      }
      
      // 正解/不正解に基づく強度の更新
      double updateStrength(double currentStrength, bool isCorrect) {
        return isCorrect 
          ? currentStrength * 1.7  // 正解時は間隔を延長
          : currentStrength * 0.6; // 不正解時は間隔を短縮
      }
    }
    

##  まとめ

SwipeLingoは、「楽しく続けられる語学学習」を実現するために、最新のAI技術と科学的な学習理論を組み合わせたアプリケーションです。YouTube動画という身近で豊富なコンテンツソースを活用し、Tinder風の直感的なUIで学習のハードルを下げながら、SRSによる効率的な記憶定着を実現しています。

技術的には、FlutterとFirebaseを中心としたモダンなスタックを採用し、Google CloudのFirebase AIを活用することで、高度な自然言語処理を低コストで実現しています。

今後も、ユーザーフィードバックを基に機能改善を続け、より多くの言語学習者の役に立つサービスへと成長させていく予定です。
