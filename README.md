# LLM環境構築（Ollama + Open WebUI + Docker Compose）

WSL環境でローカルLLMを動かすための環境設定です。

## システム要件

- **CPU**: Intel Core Ultra 7 255H（16コア）
- **GPU**: NVIDIA RTX PRO 2000 Blackwell（VRAM 8GB）
- **RAM**: 32GB
- **OS**: Windows + WSL2（Ubuntu推奨）

## 推奨モデル（VRAM 8GB最適化）

### ⭐ 検証済み - 推奨モデル

| モデル | サイズ | VRAM使用量 | 速度 | 特徴 |
|--------|--------|------------|------|------|
| **llama3.2:3b** | 3B | ~2GB | ⚡⚡⚡ | Meta最新、**最速・汎用**、コーディング支援に最適 |
| **qwen2.5:7b** | 7B | ~4.7GB | ⚡⚡⚡ | Alibaba最新、**日本語最強**、高品質推論 |
| **gemma3:4b** | 4B | ~3.3GB | ⚡⚡⚡ | Google最新2025年、**マルチモーダル**、日本語対応・画像理解 |
| **qwen2.5:3b** | 3B | ~2GB | ⚡⚡⚡ | 軽量高速版、日本語対応、バランス良好 |
| **llama3.2:1b** | 1B | ~700MB | ⚡⚡⚡⚡ | 超軽量、瞬時応答、簡単なタスク向け |

### 📝 検証済み - 非推奨モデル（このPC環境では遅い）

| モデル | サイズ | 理由 |
|--------|--------|-----------|
| deepseek-r1:7b | 7B | CoT思考トークンが膨大で応答が遅い |
| deepseek-r1:1.5b | 1.5B | 日本語精度が低く実用性に欠ける |
| mistral:7b | 7B | 旧アーキテクチャで応答が遅い |
| gemma2:9b | 9B | サイズ大、VRAM制約で大幅に遅延 |
| phi3:3.8b | 3.8B | このGPU環境では最適化不十分 |

> **重要**: このPC環境（VRAM 8GB）では **llama3.2:3b** と **qwen2.5:7b** がベストプラクティスです。

## セットアップ

> **新規PC への環境構築は [SETUP-GUIDE.md](SETUP-GUIDE.md) を参照してください。**
> （WSL2 → Docker Desktop → モデルダウンロードまで STEP 1〜8 で完結します）

## セットアップ手順（既存環境）

### 1. 環境変数の設定

```bash
# .envファイルのWEBUI_SECRET_KEYを変更（セキュリティのため）
nano .env
# または
echo "WEBUI_SECRET_KEY=$(openssl rand -base64 32)" > .env
```

### 2. サービスの起動

```bash
# Docker Composeでサービスを起動
docker compose up -d

# ログの確認
docker compose logs -f
```

### 3. モデルのダウンロード

```bash
# モデルを一括ダウンロード（10〜30分程度かかります）
./init-models.sh
```

個別にモデルをダウンロードする場合：

```bash
# 推奨モデル（検証済み・高速）
docker exec ollama ollama pull llama3.2:3b    # 最速バランス型（メイン）
docker exec ollama ollama pull qwen2.5:7b     # 日本語最強（メイン）
docker exec ollama ollama pull gemma3:4b      # Google最新・マルチモーダル
docker exec ollama ollama pull qwen2.5:3b     # 軽量日本語対応
docker exec ollama ollama pull llama3.2:1b    # 超軽量・瞬時応答
```

## 使用方法

### Open WebUIへのアクセス

1. ブラウザで `http://localhost:3000` にアクセス
2. 初回ログイン時にアカウントを作成
3. チャット画面でモデルを選択して使用開始

### モデル選択ガイド

**✅ 推奨（検証済み・高速）：**
- **日常会話・コード生成**: `llama3.2:3b` - 最速バランス型
- **日本語・高品質応答**: `qwen2.5:7b` - 7Bクラス最高効率
- **マルチモーダル・新機能検証**: `gemma3:4b` - Google最新・画像理解対応
- **超高速実験**: `llama3.2:1b` - 瞬時応答
- **軽量日本語**: `qwen2.5:3b` - 軽量高速版

**🎯 用途別の推奨モデル:**
- **プログラミング・汎用**: `llama3.2:3b`
- **日本語会話・高品質**: `qwen2.5:7b`
- **画像・マルチモーダル**: `gemma3:4b`
- **軽量日本語**: `qwen2.5:3b`
- **超高速確認用**: `llama3.2:1b`

**⚠️ 非推奨（このPC環境では遅い・削除済み）：**
- `deepseek-r1:7b`, `deepseek-r1:1.5b` - CoT思考トークンが膨大で応答遅延
- `mistral:7b`, `gemma2:9b`, `phi3:3.8b` - 旧アーキテクチャ・VRAM制約

### CLIでの使用

```bash
# Ollama CLIで直接対話
docker exec -it ollama ollama run llama3.2:3b

# APIエンドポイント
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "こんにちは、日本語で自己紹介してください。"
}'
```

## 管理コマンド

### サービス管理

```bash
# サービス起動
docker compose up -d

# サービス停止
docker compose down

# ログ確認
docker compose logs -f

# サービス再起動
docker compose restart
```

### モデル管理

```bash
# インストール済みモデル一覧
docker exec ollama ollama list

# モデルの削除
docker exec ollama ollama rm <model-name>

# モデルの更新
docker exec ollama ollama pull <model-name>
```

### リソース監視

```bash
# GPU使用状況
nvidia-smi

# コンテナリソース使用状況
docker stats

# ディスク使用量
docker system df
```

## トラブルシューティング

### GPUが認識されない場合

```bash
# NVIDIA Docker Toolkitの確認
docker run --rm --gpus all nvidia/cuda:12.0.0-base-ubuntu22.04 nvidia-smi

# Docker daemonの再起動
sudo systemctl restart docker
```

### メモリ不足の場合

Docker Composeの環境変数を調整：

```yaml
environment:
  - OLLAMA_MAX_LOADED_MODELS=1  # 同時ロードモデル数を減らす
```

### ポート競合の場合

`docker-compose.yml`のポート設定を変更：

```yaml
ports:
  - "13000:8080"  # Open WebUI
  - "11435:11434" # Ollama
```

## パフォーマンスチューニング

### WSL2メモリ設定

`C:\Users\<ユーザー名>\.wslconfig`を作成：

```ini
[wsl2]
memory=24GB          # RAMの75%程度を割り当て
processors=12        # CPUコアの75%程度を割り当て
swap=8GB
localhostForwarding=true
```

設定後、PowerShellで再起動：

```powershell
wsl --shutdown
```

## セキュリティ注意事項

- `.env`ファイルの`WEBUI_SECRET_KEY`を必ず変更してください
- ローカルネットワーク外からのアクセスを許可しないでください
- 本番環境での使用は追加のセキュリティ設定が必要です

## 更新方法

```bash
# イメージの更新
docker compose pull

# サービスの再起動
docker compose up -d
```

## アンインストール

```bash
# サービス停止とコンテナ削除
docker compose down

# ボリュームも削除（モデルデータも削除されます）
docker compose down -v
```

## 参考リンク

- [Ollama公式ドキュメント](https://ollama.ai/docs)
- [Open WebUI GitHub](https://github.com/open-webui/open-webui)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

## プロジェクト内ドキュメント

- **[SETUP-GUIDE.md](SETUP-GUIDE.md)** - 別PCへの環境構築手順（最短セットアップ）
- [PERFORMANCE-REPORT.md](PERFORMANCE-REPORT.md) - モデル性能比較・検証レポート

## ライセンス

各モデルのライセンスは提供元に準拠します。商用利用の際は各モデルのライセンスを確認してください。
