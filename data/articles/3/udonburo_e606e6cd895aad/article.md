---
title: "動きで語る。Cloud Run × Keypoints-only で作る低遅延・倫理的な動作評価基盤〈Picca〉"
url: "https://zenn.dev/udonburo/articles/e606e6cd895aad"
author: ""
published_at: "2025-09-24T14:44:49+00:00"
scraped_at: "2025-12-14T13:25:53.148060"
---

Picca は、生の画像や動画をクラウドに送らず、骨格キーポイントだけを送信して評価します。Cloud Run（東京）で約1秒、総合スコア＋左右差・出力・一貫性を返し、Gemini 2.5 Flash-Lite で一言コーチングを生成。評価器は ONNXRuntime と DCV（Dynamic Consistency Vector：姿勢列から抽出した動作特徴）に基づく決定論です。Face-less / Keypoints-only を貫く、低遅延・低コスト・倫理的な動作評価の基盤です。

TL;DR

Face-less / Keypoints-only：画像/動画は送らず端末で破棄、クラウドは座標列のみ  
約1秒応答：Cloud Run × ONNXRuntime（東京、min-instances=1）  
短い助言：Gemini 2.5 Flash-Lite（Vertex AI）で要点を日本語化（Explain β）  
拡張性：Intent→Policy、匿名 Episodes、非同期 Coach、Multi-signal IF を先回りで設計  
ユースケース：個人練習支援／リハ／教育／HRの適性確認・安全指導の下支えへ

  1. 課題とユーザー像（ⅰ）

現場課題：主観のブレ、プライバシー配慮、評価の即時性。  
対象：アスリート・コーチ・理学療法士・教員・現場安全担当・HR。  
要件：映像持ち出しなしですぐ返る客観スコア、次の一手が一言で分かる。

  2. なぜ「Face-less / Keypoints-only」か

不変性（Invariance）：外観（顔/服/背景）という撹乱要因を入力から排除 → 運動力学の同値類に近づく。  
因果性（Causality）：スコアの原因でない変数（顔・服）は入れないのが合理的。  
汎化（Generalization）：スパリアス相関を断ち、ドメイン間安定性が上がる。  
運用性（Ops）：帯域≒1/100、レイテンシ≒1/10、コスト≒1/10（概念比較）

  3. ソリューション概要（ⅰ）

ブラウザで動画から34キーポイント抽出 → JSON送信  
Cloud Run（東京）で FastAPI + ONNX が決定論で推論（p95≒1s目安）  
総合100点と symmetry / power / consistency を返却  
/api/v1/explain は Vertex AI 経由の Gemini 2.5 Flash-Lite で日本語コーチング（本番スコアから分離）  
画像/動画は長期保存せず、一時データは24hパージ方針

  4. デモ（ⅲ）

<https://youtu.be/F68sJA6Rw4Q?si=MsXUIizffmIRKUbL>

  5. アーキテクチャ（ⅱ：現在＋拡張フック）  
flowchart LR  
U[Web /demo\nKeypoints JSON] -->|POST /api/v1/score| GW[Go Gateway]  
GW --> AI[FastAPI (ONNX/DCV)]  
AI -->|score JSON| GW --> U  
GW -->|POST /api/v1/explain| VX[Vertex AI\nGemini 2.5 Flash-Lite]  
%% 拡張フック  
AI -. opt-in .-> EP[(Episodes Log\nGCS Parquet)]  
GW -. intent .-> POL[Intent→Policy\n(YAML)]  
GW -. async .-> AGT[Coach Agent(非同期)\nTools+Cache]  
U -. multi-signal IF .-> MS[(signals[]: IMU/Audio/Depth)]

Episodes Log：匿名・同意の**(Keypoints, Language, Action)** を1行で収集 → 将来の学習素体  
Intent→Policy：言葉で配点を切替（推論は決定論のまま）  
Coach Agent：非同期にツール連携で説明や練習計画（本線から分離）  
Multi-signal IF：IMU/Audio/Depth を特徴のみに還元して受け、生データは送らない

  6. 評価設計の“筋”

再現性（Reliability）  
テスト–再テスト：短期反復で ICC(2,1) ≥ 0.8 を目標  
決定論：モデル/依存の SHA-256 pin、ゴールデン3件で ±0.1 一致（CIログ公開）  
妥当性（Validity）  
収束的：左右対称課題など既存指標との相関  
弁別的：難度ステップ間の有意差（t/ANOVA）  
ロバスト性（Robustness）  
擬似シフト診断：スケール/角度/欠損に対するスコア差→Robustness Index  
不確実性：軽量TTAの P10–P90 を返し、UIに要再撮影サイン  
Goodhart対策  
テンポゆらぎ/周波数で“ゲーム化”検知 → フラグ付与  
毎夜 SHAPドリフト監査 と 閾値レビュー（匿名ログのみ）

  7. Data Thesis：次のLLM/ロボティクスに“効く”データ

結論：今はデモでもよい。重要なのは、正しく設計されたエピソードを集め続けること。  
これが、巨大LLMの“怪力”を目的特化の外科医に変え、スコアラーを実世界の制御器に近づける。

7.1 Episode（最小単位）

入力：signals[]（現状は keypoints）  
文脈：intent（言葉→配点のヒント）  
出力：score / symmetry / power / consistency（決定論）＋ band（フレーム帯）  
不確実性：score_p10 / p90（任意）  
弱ラベル：テンポ不安定 など自動フラグ  
強ラベル：ペア比較 / 区間タグ（専門家少量）  
GCS/Parquet → BigQuery。匿名・同意、画像は収集しない。保持期間・用途は SYSTEM_CARD に明記。

7.2 スコアは“仮説”（ただし修正可能性を内在）

現状のスコアは w·dcv + bias の初期仮説。ここからはデータで直す段階。  
Weak→Strong を積層（テンポ不安定などの自動フラグ → ペア比較/区間タグ）、Iaa ≥ 0.7 を監視。  
言語×動作 のコントラスト学習で「意図→配点」をデータ駆動に。  
オフラインRL/逆強化で「次に何を練習すべきか」を本番と分離して提案。  
改良ごとに SHA更新＋ゴールデン±0.1＋SLO合格を通す（再現性＞一時的な精度上振れ）。

7.3 応用先（ロボティクス / ゲーム / HR）

ロボティクス：Keypoints列→模倣学習(BC/DT)→言語条件付き方策→安全制約付きRL。  
指標は追従誤差・安定度(DMD/Koopman)・エネルギ効率をDCVに拡張。  
ゲーム/CG：モーションマッチングのインデックスにDCVを採用、IK/リターゲットで自然な遷移を誘導。  
HR/安全：繰り返し動作の左右差・ゆらぎを定点モニタ、1秒応答＋短い助言で現場可用を担保。

7.4 ロボティクスへの射線

接合：signals.keypoints(2D) に IMU / End-Effector など行為トレースを追記できるIF  
学習：模倣（BC/DT）→ CLIP的言語条件 → 安全枠付きRL  
指標：追従誤差・エネルギ効率・安定度（DMD/Koopman）を DCV拡張軸に  
倫理：ロボ側もオンデバイス推論＋非可逆特徴のみ送信

  8. 多モーダルの可能性

IMU：局所/全身の加速度で「爆発力」「安定」を補助  
Audio：端末内 MFCC→特徴のみ送信でテンポ/リズム計測  
Depth：距離/関節角度の精度向上（RGBは送らない）  
Edge：WASM/ORT-web/TFLite で完全オンデバイスへ  
ルールは一つ。「特徴は送っても、生データは送らない」。

  9. 運用・SLO・再現

SLO：/api/v1/score p95 < 1.2s、5xx < 1%（Cloud Run, Tokyo, min=1）  
ロールバック：gcloud run services update-traffic <svc> \--to-revisions STABLE=100  
再現：モデルCMEK + GCSバージョニング + SHA照合（不一致なら起動失敗）  
監査：匿名ログ、7日間の説明追跡（将来SHAP可視化）

  10. 使い方（最小 API）

* * *

POST /api/v1/score  
Content-Type: application/json  
{  
"fps": 30,  
"keypoints": [  
[[0.10, 0.20], [0.30, 0.40]],  
[[0.15, 0.25], [0.35, 0.45]]  
]  
}

* * *

POST /api/v1/score  
Content-Type: application/json  
{  
"fps": 30,  
"keypoints": [  
[[0.10, 0.20], [0.30, 0.40]],  
[[0.15, 0.25], [0.35, 0.45]]  
]  
}

* * *

成果物のURLは記事には記載しません（運用コスト観点から）。

  11. FAQ（想定問答）

Q. なぜ Vision（画像/動画）でやらない？  
A. 目的は動きの評価。外観は撹乱・コスト・遅延・法的リスクを増やす。Keypoints-onlyが最も倫理的かつ実用的。

Q. 生成AIはどこで使う？  
A. 助言文の生成（Explain β）のみ。本番スコアは決定論で分離。

Q. データは保存する？  
A. 画像/動画は長期保存しません。匿名・同意のエピソードを研究目的で保持。

  12. 免責

本デモは医療用途ではありません。  
本記事は Idea としての公開です。実装は公開リポジトリ参照（URL記載は任意）。

いまは仮値で走らせ、データで較正していく段階です。匿名・同意のエピソードを版管理で積み上げ、弱→強ラベルと対比較、必要なら独自モデルへ。Face-lessの原則を守りつつ、ロボティクスやゲームにも接続できるMotion Data Bankとして育てます。

* * *

最後までお付き合いいただき、ありがとうございます。  
このプロジェクトは、AIの力を借りながら進めた、実質初めての個人開発です。動画のBGMは数年前の自作（非AI）です、音量が大きすぎましたら申し訳ありません。🔊  
あらゆる方面に至らない点も多いかと思いますので、どんな些細なことでもご指摘やご感想をいただけますと、ものすごく喜びます。

追記：

解像度が低く文字がつぶれていたので、高画質を添付しています。

<https://www.youtube.com/watch?v=cwatVPfCeDA>
