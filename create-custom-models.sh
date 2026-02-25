#!/bin/bash
# カスタムモデル一括作成スクリプト

set -e

MODELFILE_DIR="$HOME/llm/modelfiles"
mkdir -p "$MODELFILE_DIR"

echo "========================================"
echo "カスタムモデル作成スクリプト"
echo "========================================"
echo ""

# Ollamaが起動するまで待機
echo "Ollamaの接続を確認中..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
done
echo "✓ Ollama接続OK"
echo ""

# ヘルパー関数: Modelfileをコンテナにコピーしてモデル作成
create_model() {
    local model_name="$1"
    local modelfile_path="$2"
    local container_path="/tmp/${model_name}.modelfile"

    docker cp "$modelfile_path" "ollama:${container_path}"
    docker exec ollama ollama create "$model_name" -f "$container_path"
    docker exec ollama rm -f "$container_path" 2>/dev/null || true
}

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
create_model "japanese-assistant" "$MODELFILE_DIR/japanese-assistant.modelfile"
echo "✓ japanese-assistant 作成完了"
echo ""

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
create_model "code-assistant" "$MODELFILE_DIR/code-assistant.modelfile"
echo "✓ code-assistant 作成完了"
echo ""

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
create_model "translator" "$MODELFILE_DIR/translator.modelfile"
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
echo "Open WebUI (http://localhost:3000) のモデル選択画面に追加されます。"
echo ""
echo "現在のモデル一覧:"
docker exec ollama ollama list
