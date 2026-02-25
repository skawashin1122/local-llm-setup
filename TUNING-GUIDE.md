# 回答精度チューニングガイド
**環境**: Ollama + Open WebUI / NVIDIA RTX PRO 2000 (VRAM 8GB)

このガイドでは、プロンプトエンジニアリングとRAGを活用して、ローカルLLMの回答精度を向上させる具体的な手順を説明します。

---

## 目次

1. [プロンプトエンジニアリング（システムプロンプト設定）](#1-プロンプトエンジニアリングシステムプロンプト設定)
2. [カスタムモデル（Modelfile）の作成](#2-カスタムモデルmodelfileの作成)
3. [RAG（検索拡張生成）の設定](#3-rag検索拡張生成の設定)
4. [パラメータチューニング](#4-パラメータチューニング)
5. [用途別テンプレート集](#5-用途別テンプレート集)

---

## 1. プロンプトエンジニアリング（システムプロンプト設定）

### 1-1. グローバルシステムプロンプトの設定

すべてのチャットに適用されるデフォルトのシステムプロンプトを設定します。

**手順:**

1. Open WebUI (`http://localhost:3000`) にログイン
2. 左下の **ユーザーアイコン** → **設定 (Settings)** をクリック
3. **一般 (General)** タブを選択
4. **システムプロンプト (System Prompt)** 欄に以下を入力：

```
あなたは優秀な日本語アシスタントです。以下のルールに従って回答してください：

1. 必ず日本語で回答する
2. 回答は正確かつ簡潔にする
3. 不明な場合は「わかりません」と正直に答える
4. 専門用語は必要に応じて補足説明を加える
5. コードを含む場合は適切なコメントを付ける
```

5. **保存 (Save)** をクリック

### 1-2. モデル別システムプロンプトの設定

モデルごとに異なるシステムプロンプトを設定できます。

**手順:**

1. 左サイドバー上部の **ワークスペース (Workspace)** → **モデル (Models)** をクリック
2. 設定したいモデル（例: `qwen2.5:7b`）の **鉛筆アイコン（編集）** をクリック
3. **システムプロンプト (System Prompt)** 欄に用途に合ったプロンプトを入力
4. **保存 (Save)** をクリック

### 1-3. 効果的なシステムプロンプトの書き方

#### 基本原則

| テクニック | 説明 | 例 |
|-----------|------|-----|
| **役割の指定** | AIに具体的な役割を与える | 「あなたはシニアPythonエンジニアです」|
| **制約の明示** | やるべきこと・やらないことを列挙 | 「推測で回答しないでください」|
| **出力形式の指定** | 応答のフォーマットを指示 | 「箇条書きで回答してください」|
| **Few-shot例示** | 期待する入出力の例を提示 | 質問→回答の例を2〜3個含める |
| **Chain-of-Thought** | 段階的な思考を促す | 「ステップバイステップで説明してください」|

#### 悪い例 vs 良い例

**❌ 悪い例（曖昧）:**
```
いい回答をしてください。
```

**✅ 良い例（具体的）:**
```
あなたはシニアソフトウェアエンジニアです。以下のルールに従ってください：

- プログラミングに関する質問には、実行可能なコード例を含めて回答する
- コードにはコメントを付けて説明する
- セキュリティやパフォーマンスの注意点があれば必ず言及する
- 回答言語は日本語とする
- 不確かな情報は「確認が必要」と明示する
```

---

## 2. カスタムモデル（Modelfile）の作成

Ollamaの Modelfile を使って、プロンプトとパラメータを組み込んだカスタムモデルを作成できます。

### 2-1. 日本語特化カスタムモデル

```bash
# Modelfileを作成
cat << 'EOF' > ~/llm/modelfiles/japanese-assistant.modelfile
FROM qwen2.5:7b

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.1

SYSTEM """
あなたは「日本語アシスタント」です。以下のルールに厳密に従ってください：

【基本ルール】
1. 必ず日本語で回答する（コード内コメントも日本語）
2. 回答は正確かつ簡潔にする（冗長な前置きは不要）
3. 不明な場合は「この情報は確認が必要です」と明示する
4. 専門用語には括弧で簡単な説明を添える

【回答フォーマット】
- 長い回答は見出しと箇条書きで構造化する
- コードブロックには言語名を明記する
- 重要なポイントは太字やリストで強調する

【禁止事項】
- 推測による断定的な回答
- 英語での長文回答（英語の専門用語は可）
- 不必要な謝罪や前置き
"""
EOF
```

```bash
# モデルを作成
docker exec -i ollama ollama create japanese-assistant -f - < ~/llm/modelfiles/japanese-assistant.modelfile
```

### 2-2. コーディング特化カスタムモデル

```bash
cat << 'EOF' > ~/llm/modelfiles/code-assistant.modelfile
FROM llama3.2:3b

PARAMETER temperature 0.3
PARAMETER top_p 0.85
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.1

SYSTEM """
You are an expert software engineer. Follow these rules strictly:

【Rules】
1. Always provide working, complete code examples
2. Add inline comments explaining key logic (in Japanese)
3. Follow best practices and design patterns
4. Mention security considerations when relevant
5. Suggest performance optimizations when applicable

【Output Format】
- Start with a brief summary of the approach (in Japanese)
- Provide the complete code with comments
- End with usage examples and notes

【Languages】
- Respond in Japanese for explanations
- Use English for code and technical terms
"""
EOF
```

```bash
docker exec -i ollama ollama create code-assistant -f - < ~/llm/modelfiles/code-assistant.modelfile
```

### 2-3. カスタムモデルの一括作成スクリプト

```bash
cat << 'SCRIPT' > ~/llm/create-custom-models.sh
#!/bin/bash
# カスタムモデル一括作成スクリプト

set -e

MODELFILE_DIR="$HOME/llm/modelfiles"
mkdir -p "$MODELFILE_DIR"

echo "========================================"
echo "カスタムモデル作成スクリプト"
echo "========================================"

# --- 日本語アシスタント ---
cat << 'EOF' > "$MODELFILE_DIR/japanese-assistant.modelfile"
FROM qwen2.5:7b

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.1

SYSTEM """
あなたは「日本語アシスタント」です。以下のルールに厳密に従ってください：

【基本ルール】
1. 必ず日本語で回答する（コード内コメントも日本語）
2. 回答は正確かつ簡潔にする（冗長な前置きは不要）
3. 不明な場合は「この情報は確認が必要です」と明示する
4. 専門用語には括弧で簡単な説明を添える

【回答フォーマット】
- 長い回答は見出しと箇条書きで構造化する
- コードブロックには言語名を明記する
- 重要なポイントは太字やリストで強調する

【禁止事項】
- 推測による断定的な回答
- 英語での長文回答（英語の専門用語は可）
- 不必要な謝罪や前置き
"""
EOF

echo "[1/3] 日本語アシスタント作成中..."
docker exec -i ollama ollama create japanese-assistant -f - < "$MODELFILE_DIR/japanese-assistant.modelfile"
echo "✓ japanese-assistant 作成完了"

# --- コーディングアシスタント ---
cat << 'EOF' > "$MODELFILE_DIR/code-assistant.modelfile"
FROM llama3.2:3b

PARAMETER temperature 0.3
PARAMETER top_p 0.85
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.1

SYSTEM """
You are an expert software engineer. Follow these rules strictly:

【Rules】
1. Always provide working, complete code examples
2. Add inline comments explaining key logic (in Japanese)
3. Follow best practices and design patterns
4. Mention security considerations when relevant
5. Suggest performance optimizations when applicable

【Output Format】
- Start with a brief summary of the approach (in Japanese)
- Provide the complete code with comments
- End with usage examples and notes

【Languages】
- Respond in Japanese for explanations
- Use English for code and technical terms
"""
EOF

echo "[2/3] コーディングアシスタント作成中..."
docker exec -i ollama ollama create code-assistant -f - < "$MODELFILE_DIR/code-assistant.modelfile"
echo "✓ code-assistant 作成完了"

# --- 翻訳アシスタント ---
cat << 'EOF' > "$MODELFILE_DIR/translator.modelfile"
FROM qwen2.5:7b

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_ctx 4096

SYSTEM """
あなたはプロフェッショナルな翻訳者です。以下のルールに従ってください：

【翻訳ルール】
1. 入力が日本語なら英語に翻訳する
2. 入力が英語なら日本語に翻訳する
3. その他の言語が検出された場合は日本語に翻訳する
4. 翻訳は自然で読みやすい文体にする
5. 技術用語は文脈に合った訳語を選択する

【出力フォーマット】
- まず翻訳結果を提示する
- 必要に応じて翻訳上の注意点を補足する
- 複数の訳がある場合は候補を示す

【禁止事項】
- 原文の意味を変える意訳（特に技術文書）
- 翻訳以外の余計な解説（求められない限り）
"""
EOF

echo "[3/3] 翻訳アシスタント作成中..."
docker exec -i ollama ollama create translator -f - < "$MODELFILE_DIR/translator.modelfile"
echo "✓ translator 作成完了"

echo ""
echo "========================================"
echo "全カスタムモデル作成完了！"
echo "========================================"
echo ""
echo "利用可能なカスタムモデル:"
echo "  - japanese-assistant : 日本語アシスタント (qwen2.5:7bベース)"
echo "  - code-assistant     : コーディング支援 (llama3.2:3bベース)"
echo "  - translator         : 翻訳アシスタント (qwen2.5:7bベース)"
echo ""
echo "Open WebUI のモデル選択画面に以下が追加されます。"
SCRIPT

chmod +x ~/llm/create-custom-models.sh
```

**実行方法:**

```bash
cd ~/llm
./create-custom-models.sh
```

---

## 3. RAG（検索拡張生成）の設定

RAG（Retrieval Augmented Generation）を使うと、アップロードした文書の内容に基づいてモデルが回答できるようになります。Open WebUI にはRAG機能が組み込まれています。

### 3-1. RAG管理設定（管理者）

**手順:**

1. Open WebUI にログイン
2. 左下の **ユーザーアイコン** → **管理パネル (Admin Panel)** をクリック
3. **設定 (Settings)** → **ドキュメント (Documents)** を選択
4. 以下を設定：

| 設定項目 | 推奨値 | 説明 |
|---------|--------|------|
| **Embedding Model** | `sentence-transformers/all-MiniLM-L6-v2`（デフォルト） | 文書のベクトル化モデル（変更不要） |
| **Chunk Size** | `1000` | 文書を分割するトークン数 |
| **Chunk Overlap** | `200` | チャンク間の重複トークン数 |
| **Top K** | `5` | 検索で取得するチャンク数 |
| **Hybrid Search** | `ON` | BM25 + ベクトル検索のハイブリッド（推奨） |
| **Relevance Threshold** | `0.3` | 関連度のしきい値（低いほど多くのチャンクを返す） |

5. **保存 (Save)** をクリック

> **注意**: Embedding Model はOpen WebUI内蔵のため追加VRAMは不要です。Ollamaモデルに変更する場合はVRAM消費が増えます。

### 3-2. ナレッジベースの作成

ナレッジベースは、関連ドキュメントをコレクションとしてまとめる機能です。

**手順:**

1. 左サイドバーの **ワークスペース (Workspace)** → **ナレッジ (Knowledge)** をクリック
2. **「+ 作成」** ボタンをクリック
3. 以下を入力：
   - **名前**: 例）`社内マニュアル`
   - **説明**: 例）`社内の技術マニュアル・ハンドブック集`
4. **作成** をクリック
5. 作成されたナレッジをクリックして開く
6. **「+ ファイル追加」** ボタンから文書をアップロード

**対応ファイル形式:**
- PDF (.pdf)
- テキスト (.txt)
- Markdown (.md)
- Word (.docx)
- Excel (.xlsx)
- PowerPoint (.pptx)
- CSV (.csv)
- HTML (.html)

### 3-3. チャットでRAGを使う

#### 方法A: ファイルを直接アップロード

1. チャット画面で **入力欄の左にある「+」ボタン** をクリック
2. **ファイルをアップロード** を選択
3. 参照したいファイルを選ぶ
4. ファイルがアタッチされた状態で質問を入力

#### 方法B: ナレッジベースを指定（`#` コマンド）

1. チャット入力欄に **`#`** を入力
2. ナレッジベースの一覧が表示される
3. 使用したいナレッジベースを選択
4. 質問を入力して送信

```
例: #社内マニュアル このプロジェクトのデプロイ手順を教えてください
```

#### 方法C: URLを参照

1. チャット入力欄に **`#`** を入力し、続けてURLを入力
2. WebページのコンテンツがRAGに取り込まれる

```
例: #https://docs.python.org/3/tutorial/ Pythonのリスト内包表記について教えてください
```

### 3-4. モデルにナレッジを紐付ける

特定のモデルに常時ナレッジベースを紐付けることができます。

**手順:**

1. **ワークスペース** → **モデル** をクリック
2. 対象モデルの **編集（鉛筆アイコン）** をクリック
3. **ナレッジ (Knowledge)** セクションで紐付けたいナレッジベースを選択
4. **保存** をクリック

> これにより、そのモデルを使用する際に自動でナレッジベースが参照されます。

### 3-5. RAGの効果を最大化するコツ

| ポイント | 説明 |
|---------|------|
| **文書の品質** | 整形されたテキスト・正確な情報の文書を使用する |
| **適切なチャンク分割** | 長すぎると関連性が下がり、短すぎると文脈が失われる |
| **ナレッジ名の工夫** | わかりやすい名前を付けて `#` で素早く指定できるようにする |
| **システムプロンプトとの併用** | RAGコンテキストの活用方法をシステムプロンプトに含める |
| **定期的な更新** | 情報が古くならないよう文書を定期的に差し替える |

#### RAG対応システムプロンプトの例

```
あなたは社内ドキュメントに基づいて回答するアシスタントです。

【ルール】
1. 提供されたコンテキスト（参考文書）に基づいて回答する
2. コンテキストに答えがない場合は「提供された文書には該当情報がありません」と回答する
3. 情報の出典（どの文書に記載されていたか）を必ず示す
4. コンテキストの情報と自身の知識を明確に区別する
```

---

## 4. パラメータチューニング

### 4-1. チャットごとのパラメータ調整

**手順:**

1. チャット画面の上部にある **モデル名の横のスライダーアイコン** をクリック
2. 以下のパラメータを調整：

| パラメータ | デフォルト | 推奨範囲 | 用途 |
|-----------|-----------|---------|------|
| **Temperature** | 0.8 | 0.1〜1.0 | 低い＝正確・決定的、高い＝創造的・多様 |
| **Top P** | 0.9 | 0.7〜0.95 | 確率上位P%のトークンから選択 |
| **Top K** | 40 | 10〜100 | 上位K個のトークンから選択 |
| **Repeat Penalty** | 1.1 | 1.0〜1.3 | 繰り返しのペナルティ（高い＝繰り返し抑制） |
| **Context Length** | 4096 | 2048〜8192 | 入力コンテキストの最大長 |

### 4-2. 用途別の推奨パラメータ

#### 正確な回答が必要な場合（FAQ・技術Q&A）
```
Temperature: 0.3
Top P: 0.85
Top K: 20
Repeat Penalty: 1.1
```

#### 創造的な文章生成（ブレスト・アイデア出し）
```
Temperature: 0.9
Top P: 0.95
Top K: 60
Repeat Penalty: 1.0
```

#### コード生成
```
Temperature: 0.2
Top P: 0.85
Top K: 30
Repeat Penalty: 1.15
```

#### 翻訳
```
Temperature: 0.3
Top P: 0.9
Top K: 40
Repeat Penalty: 1.1
```

---

## 5. 用途別テンプレート集

### 5-1. プロンプトプリセットの登録

Open WebUI では `/` コマンドでプロンプトプリセットを呼び出せます。

**手順:**

1. **ワークスペース** → **プロンプト (Prompts)** をクリック
2. **「+ 作成」** ボタンをクリック
3. 以下を入力：
   - **タイトル**: プリセット名
   - **コマンド**: `/` のあとに続ける文字列（例: `review`）
   - **内容**: プロンプトテンプレート

### 5-2. おすすめプリセット

#### コードレビュー（コマンド: `/review`）
```
以下のコードをレビューしてください。
観点：バグ、セキュリティ、パフォーマンス、可読性

```コード
{{CLIPBOARD}}
```

【出力形式】
1. 重大な問題（あれば）
2. 改善提案
3. 良い点
```

#### 要約（コマンド: `/summary`）
```
以下の文章を日本語で簡潔に要約してください。

- 3〜5個の箇条書きでまとめる
- 重要なキーワードは保持する
- 200文字以内

文章:
{{CLIPBOARD}}
```

#### エラー解析（コマンド: `/debug`）
```
以下のエラーメッセージを分析してください。

エラー:
{{CLIPBOARD}}

【出力形式】
1. エラーの原因（簡潔に）
2. 解決方法（手順付き）
3. 再発防止策
```

#### 日英翻訳（コマンド: `/translate`）
```
以下のテキストを翻訳してください。
- 日本語の場合は英語に翻訳
- 英語の場合は日本語に翻訳
- 技術用語は原語を括弧で併記

テキスト:
{{CLIPBOARD}}
```

---

## クイックスタート

### すぐに始める場合の最小手順

```bash
# 1. カスタムモデルを作成
cd ~/llm
./create-custom-models.sh

# 2. モデル一覧を確認
docker exec ollama ollama list
```

その後 Open WebUI (`http://localhost:3000`) で：

1. **設定 → 一般** でシステムプロンプトを設定
2. **ワークスペース → ナレッジ** でドキュメントをアップロード
3. チャットで `#ナレッジ名` を使ってRAG検索
4. **ワークスペース → プロンプト** でプリセットを登録
5. チャットで `/コマンド名` でプリセットを呼び出し

---

## 手法別 効果比較

| 手法 | 精度向上 | 導入コスト | VRAM影響 | 即効性 |
|------|---------|-----------|---------|--------|
| システムプロンプト | ⭐⭐⭐ | 0分 | なし | ✅ 即時 |
| カスタムモデル (Modelfile) | ⭐⭐⭐⭐ | 10分 | なし | ✅ 即時 |
| プロンプトプリセット | ⭐⭐⭐ | 5分 | なし | ✅ 即時 |
| パラメータ調整 | ⭐⭐ | 1分 | なし | ✅ 即時 |
| RAG (ナレッジベース) | ⭐⭐⭐⭐⭐ | 15分〜 | 最小限 | ✅ 即時 |
| ファインチューニング | ⭐⭐⭐⭐⭐ | 数時間〜 | 不可（8GB） | ❌ 不可 |

> **推奨**: まず「システムプロンプト」＋「カスタムモデル」で基礎を固め、特定ドメインの精度が必要になったら「RAG」を追加してください。

---

*作成日: 2026-02-24*
*環境: Ollama + Open WebUI / NVIDIA RTX PRO 2000 Blackwell (8GB VRAM)*
