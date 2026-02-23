# ローカルLLM環境 セットアップガイド
**所要時間: 約30〜45分**（モデルダウンロード含む）

## 対象PC スペック

| 項目 | 仕様 |
|------|------|
| CPU | Intel Core Ultra 7 255H（16コア）以上 |
| GPU | NVIDIA RTX PRO 2000 Blackwell（VRAM 8GB）相当 |
| RAM | 32GB |
| OS | Windows 11 + WSL2（Ubuntu 24.04） |

---

## STEP 1 — WSL2の準備（Windows PowerShell）

```powershell
# WSL2 + Ubuntu をインストール
wsl --install

# インストール後、再起動してからWSL2に設定
wsl --set-default-version 2
```

> 再起動後、スタートメニューから「Ubuntu」を起動してユーザー名・パスワードを設定する。

---

## STEP 2 — WSL2メモリ設定（Windows側）

`C:\Users\<ユーザー名>\.wslconfig` を作成して以下を記述：

```ini
[wsl2]
memory=24GB
processors=12
swap=8GB
localhostForwarding=true
```

設定後、PowerShellで再起動：

```powershell
wsl --shutdown
wsl
```

---

## STEP 3 — Docker Desktop のインストール

1. https://www.docker.com/products/docker-desktop/ からダウンロード・インストール
2. Docker Desktop を起動
3. **Settings → Resources → WSL Integration** で Ubuntu を有効化
4. **Settings → Resources → GPU** で GPU support を有効化

> Docker Desktopが起動している状態でWSL内から`docker`コマンドが使えることを確認する。

---

## STEP 4 — WSL内でGPU・Dockerを確認

WSL（Ubuntu）を開いて実行：

```bash
# NVIDIA GPUドライバーの確認
nvidia-smi

# Docker動作確認
docker info

# GPU + Docker の統合確認（イメージ自動ダウンロードあり・数分かかる）
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu24.04 nvidia-smi
```

最後のコマンドで `nvidia-smi` の出力が表示されれば完了。

---

## STEP 5 — プロジェクトのセットアップ

```bash
# ホームディレクトリにプロジェクトフォルダを作成
mkdir -p ~/llm && cd ~/llm
```

### docker-compose.yml を作成

```bash
cat > docker-compose.yml << 'EOF'
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    environment:
      - OLLAMA_HOST=0.0.0.0:11434
      - OLLAMA_NUM_PARALLEL=4
      - OLLAMA_MAX_LOADED_MODELS=2
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    restart: unless-stopped
    networks:
      - ollama-network

  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open-webui
    ports:
      - "3000:8080"
    volumes:
      - open_webui_data:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - WEBUI_AUTH=true
      - WEBUI_NAME=Local LLM Studio
      - WEBUI_SECRET_KEY=${WEBUI_SECRET_KEY:-change-this-secret}
    depends_on:
      - ollama
    restart: unless-stopped
    networks:
      - ollama-network

volumes:
  ollama_data:
    driver: local
  open_webui_data:
    driver: local

networks:
  ollama-network:
    driver: bridge
EOF
```

### .env ファイルを作成

```bash
cat > .env << EOF
WEBUI_SECRET_KEY=$(openssl rand -base64 32)
OLLAMA_NUM_PARALLEL=4
OLLAMA_MAX_LOADED_MODELS=2
EOF
```

---

## STEP 6 — サービス起動

```bash
cd ~/llm

# コンテナをバックグラウンドで起動
docker compose up -d

# 起動ログの確認（Ctrl+C で抜ける）
docker compose logs -f
```

Ollama と open-webui の2コンテナが `Up` になれば完了：

```bash
docker compose ps
```

---

## STEP 7 — モデルのダウンロード

> 合計約10GB。ネット回線速度によって10〜30分程度かかる。

```bash
# Ollamaの起動を待機してからダウンロード
until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do sleep 2; done

# 3モデルを順番にダウンロード
docker exec ollama ollama pull llama3.2:3b   # 汎用・最速（約2GB）
docker exec ollama ollama pull qwen2.5:7b    # 日本語・高品質（約4.7GB）
docker exec ollama ollama pull gemma3:4b     # マルチモーダル・画像理解（約3.3GB）

# ダウンロード確認
docker exec ollama ollama list
```

---

## STEP 8 — 動作確認

ブラウザで以下にアクセス：

```
http://localhost:3000
```

1. **アカウント作成**（初回のみ。最初に登録したユーザーが管理者になる）
2. 上部のモデル選択から `llama3.2:3b` を選択
3. 「こんにちは」と入力して応答が返れば完了 ✅

---

## 採用モデル一覧

| モデル | サイズ | VRAM | 用途 |
|--------|--------|------|------|
| **llama3.2:3b** | 2.0 GB | ~2GB | 汎用・コード生成・最速 |
| **qwen2.5:7b** | 4.7 GB | ~4.7GB | 日本語・高品質推論 |
| **gemma3:4b** | 3.3 GB | ~3.3GB | マルチモーダル・画像理解 |

### 用途別の使い分け

| やりたいこと | 使うモデル |
|-------------|-----------|
| プログラミング・日常会話 | `llama3.2:3b` |
| 日本語で高品質な回答 | `qwen2.5:7b` |
| 画像をアップロードして質問 | `gemma3:4b` |

---

## 日常的な操作コマンド

```bash
# サービス起動
docker compose -f ~/llm/docker-compose.yml up -d

# サービス停止
docker compose -f ~/llm/docker-compose.yml down

# モデル一覧確認
docker exec ollama ollama list

# GPU使用状況確認
nvidia-smi

# イメージ・モデルの更新
docker compose -f ~/llm/docker-compose.yml pull
docker exec ollama ollama pull llama3.2:3b
docker exec ollama ollama pull qwen2.5:7b
docker exec ollama ollama pull gemma3:4b
```

---

## トラブルシューティング

### `docker: permission denied` が出る場合

```bash
sudo usermod -aG docker $USER
# → WSLを再起動（exit → wsl --shutdown → wsl）
```

### GPUが認識されない場合

1. Docker Desktop の GPU support が有効か確認
2. `nvidia-smi` がWSL内で動作するか確認
3. Docker Desktopを再起動

### Open WebUIにアクセスできない場合

```bash
# コンテナの状態を確認
docker compose ps

# ログでエラーを確認
docker compose logs open-webui
```

### モデルの応答が遅い場合

```bash
# 同時ロードモデル数を1に制限（.envを編集）
echo "OLLAMA_MAX_LOADED_MODELS=1" >> ~/llm/.env
docker compose -f ~/llm/docker-compose.yml up -d
```

---

## 検証済み・非推奨モデル（参考）

以下はこの環境で検証したが、応答速度や品質の問題で不採用：

| モデル | 問題点 |
|--------|--------|
| deepseek-r1:7b | CoT思考トークンが膨大で応答が441秒かかった |
| deepseek-r1:1.5b | 日本語精度が低く中国語で応答 |
| mistral:7b | 旧アーキテクチャで応答が遅い |
| gemma2:9b | VRAM制約（5.4GB）で大幅に遅延 |
| phi3:3.8b | このGPU環境では最適化不十分 |
