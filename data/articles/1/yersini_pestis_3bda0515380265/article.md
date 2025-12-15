---
title: "AIがアイデアを育てる！GeminiとClaudeによる自動ブレインストーミングアプリの開発"
url: "https://zenn.dev/yersini_pestis/articles/3bda0515380265"
author: ""
published_at: "2025-02-10T14:59:09+00:00"
scraped_at: "2025-12-14T13:16:59.777285"
---

##  🎯 プロジェクトの概要

AIエージェントハッカソンへの参加作品として、アイデア発想支援アプリ「アイデアの会議室」を開発しました。このアプリは、2つのAI（GeminiとClaude）を組み合わせることで、あなたのアイデアを自動的に分析・発展させる画期的なソリューションです。

###  デモ動画

[![アイデアの会議室 デモ](images/img_000.jpg)](https://youtu.be/Zou3DBi6TDI)

##  🌟 主な特徴

  1. **デュアルAI解析システム**

     * Gemini: 初期アイデアの分析と具体化
     * Claude: Mermaid.jsを活用した図解付き考察の提供
  2. **インタラクティブな対話機能**

     * リアルタイムのアイデア発展支援
     * AIによる自動図解生成
     * 複数の視点からの分析提供
  3. **最適化されたUX**

     * 直感的な操作フロー
     * モダンで使いやすいUI設計
     * レスポンシブな画面レイアウト

##  🛠 技術スタック

###  フロントエンド

  * React + Vite
  * TailwindCSS
  * Mermaid.js（図解生成）

###  バックエンド/インフラ

  * Google Cloud Run
  * Firebase Authentication
  * Firebase Realtime Database

###  AI/ML統合

  * Google Cloud Vertex AI (Gemini)
  * AWS Bedrock (Claude)

##  💡 開発の背景と動機

Zennというプラットフォームは、技術者による技術者のための知識共有の場です。この場でアイデアの共有と発展を支援するツールがあれば、より活発なナレッジ共有が実現できるのではないか。この考えが開発の原点となりました。

##  📊 システムアーキテクチャ

🚀 実装のポイント  
主要な実装のソースコードはGitHubリポジトリ(<https://github.com/YersiniaPestis899/mindmeld>)  
で公開しています。

##  💻 技術的な実装の詳細

###  1\. AIエージェントの連携設計

アプリケーションの核となるAIエージェントの連携は、以下のような構造で実装しています：
    
    
    // AIサービスの統合インターフェース
    interface AIService {
      generateResponse(prompt: string): Promise<string>;
      generateDiagram(context: string): Promise<string>;
    }
    
    // Gemini AIサービスの実装
    class GeminiService implements AIService {
      async generateResponse(prompt: string) {
        const model = genAI.getGenerativeModel({ model: "gemini-pro" });
        const result = await model.generateContent(prompt);
        return result.response.text();
      }
      
      async generateDiagram(context: string) {
        // 図解生成のロジック
        return await this.generateResponse(context + "\nMermaid形式で図解化してください");
      }
    }
    
    // Claude AIサービスの実装
    class ClaudeService implements AIService {
      async generateResponse(prompt: string) {
        const response = await client.send(new InvokeModelCommand({
          modelId: "anthropic.claude-3-sonnet",
          prompt: prompt
        }));
        return response.completion;
      }
    }
    

  2. 状態管理とデータフロー  
Firebaseを活用した状態管理の実装例：

    
    
    Copyconst IdeaContext = createContext<IdeaContextType | null>(null);
    
    export const IdeaProvider: React.FC = ({ children }) => {
      const [ideas, setIdeas] = useState<Idea[]>([]);
      const [currentIdea, setCurrentIdea] = useState<Idea | null>(null);
    
      // リアルタイムデータ同期
      useEffect(() => {
        const db = getDatabase();
        const ideasRef = ref(db, 'ideas');
        
        onValue(ideasRef, (snapshot) => {
          const data = snapshot.val();
          if (data) {
            const ideaList = Object.entries(data).map(([id, idea]) => ({
              id,
              ...idea as Idea
            }));
            setIdeas(ideaList);
          }
        });
      }, []);
    
      return (
        <IdeaContext.Provider value={{ ideas, currentIdea, setCurrentIdea }}>
          {children}
        </IdeaContext.Provider>
      );
    };
    

##  🔄 開発プロセスとチャレンジ

###  1\. AIレスポンスの最適化

開発初期に直面した主要な課題は、AIレスポンスの品質と一貫性でした。特に以下の問題に注力して解決を図りました：

  1. **プロンプトエンジニアリング**

    
    
    const SYSTEM_PROMPT = `
    あなたは以下の制約条件に従って回答してください：
    1. 必ずMermaid記法による図解を含める
    2. 図解は複雑すぎず、理解しやすいものにする
    3. 実装可能な具体的な提案を含める
    
    回答構造：
    1. アイデアの分析（3-4文）
    2. 図解による可視化
    3. 実装提案と課題解決
    `;
    
    const enhancePrompt = (userInput: string) => {
      return `${SYSTEM_PROMPT}\n\nユーザーの入力：${userInput}`;
    };
    

2.応答品質の検証システム
    
    
    Copyinterface ResponseQuality {
      hasMermaid: boolean;
      hasImplementation: boolean;
      hasConcreteSuggestions: boolean;
    }
    
    const validateAIResponse = (response: string): ResponseQuality => {
      return {
        hasMermaid: response.includes('```mermaid'),
        hasImplementation: /実装|実現方法|手順/.test(response),
        hasConcreteSuggestions: /提案|改善点|解決策/.test(response)
      };
    };
    
    const needsRegeneration = (quality: ResponseQuality): boolean => {
      return !Object.values(quality).every(Boolean);
    };
    

🎁 今後の展望

・AIモデルの拡張

  * より多様なAIモデルの統合
  * 特定分野に特化した分析機能

・コラボレーション機能

  * チーム開発向け機能の実装
  * リアルタイム共同編集機能

・分析機能の強化

  * より高度な図解生成
  * カスタマイズ可能な分析フロー

📝 まとめ  
本プロジェクトを通じて、最新のAIエージェント技術を活用することで、アイデア発想のプロセスを効率化・高度化できることが実証できました。ぜひGitHubリポジトリをチェックしていただき、フィードバックをお待ちしています！
