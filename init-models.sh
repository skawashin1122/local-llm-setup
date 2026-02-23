#!/bin/bash
# Ollamaモデル初期化スクリプト（採用3モデル）

set -e

echo "========================================"
echo "Ollama モデル初期化スクリプト"
echo "========================================"
echo ""

# Ollamaが起動するまで待機
echo "Ollamaの起動を待機中..."
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
    sleep 2
done
echo "✓ Ollamaが起動しました"
echo ""

# 採用3モデル（VRAM 8GB検証済み）
declare -a models=(
    "llama3.2:3b"   # 汎用・最速（約2GB VRAM）
    "qwen2.5:7b"    # 日本語・高品質（約4.7GB VRAM）
    "gemma3:4b"     # マルチモーダル・画像理解（約3.3GB VRAM）
)

declare -a descriptions=(
    "Meta Llama 3.2 3B  - 汎用・最速・コード生成"
    "Alibaba Qwen 2.5 7B - 日本語最強・高品質推論"
    "Google Gemma 3 4B  - マルチモーダル・画像理解"
)

TOTAL=${#models[@]}
for i in "${!models[@]}"; do
    model="${models[$i]}"
    desc="${descriptions[$i]}"

    echo "[$((i+1))/${TOTAL}] ${desc}"
    echo "モデル: ${model}"

    if docker exec ollama ollama list | grep -q "^${model}"; then
        echo "✓ インストール済み（スキップ）"
    else
        echo "ダウンロード中..."
        if docker exec ollama ollama pull "${model}"; then
            echo "✓ 完了"
        else
            echo "✗ 失敗"
        fi
    fi
    echo ""
done

echo "========================================"
echo "完了"
echo "========================================"
echo ""
docker exec ollama ollama list
echo ""
echo "Open WebUI: http://localhost:3000"
echo ""
