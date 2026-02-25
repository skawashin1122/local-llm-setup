"""
title: 日南情報高校 入力フィルター
author: nichinan-info-hs
version: 1.0.0
description: 不適切な入力をフィルタリングし、学校チャットボットとして安全な利用を確保する
"""

from typing import Optional
from pydantic import BaseModel, Field
import re


class Pipeline:
    class Valves(BaseModel):
        pipelines: list[str] = Field(
            default=["*"],
            description="対象パイプライン（*は全モデル）",
        )
        enabled: bool = Field(
            default=True,
            description="フィルターの有効/無効",
        )
        blocked_keywords: str = Field(
            default="爆弾,殺す,死ね,自殺,麻薬,ドラッグ,覚醒剤,大麻,暴力,テロ,攻撃方法,ハッキング,不正アクセス,パスワード解析,クラッキング,フィッシング,マルウェア,ウイルス作成,ランサムウェア,セクハラ,エロ,アダルト,ポルノ,裸,性的,わいせつ,差別,ヘイト",
            description="ブロックするキーワード（カンマ区切り）",
        )
        warning_message: str = Field(
            default="⚠️ 申し訳ありませんが、その内容にはお答えできません。\n\n本チャットボットは宮崎県立日南情報高等学校の公式AIアシスタントです。\n学校に関する質問をお願いします。\n\n例：\n- 「文化祭はいつですか？」\n- 「どんな部活がありますか？」\n- 「情報システム科について教えてください」",
            description="ブロック時に表示するメッセージ",
        )
        max_input_length: int = Field(
            default=1000,
            description="入力文字数の上限",
        )
        prompt_injection_patterns: str = Field(
            default="ignore previous,ignore above,ignore all,forget your instructions,disregard,you are now,act as,pretend to be,new instructions,override,system prompt,あなたの指示を無視,命令を無視,設定を忘れて,役割を変えて,別の人格",
            description="プロンプトインジェクション検知パターン（カンマ区切り）",
        )

    def __init__(self):
        self.type = "filter"
        self.name = "日南情報高校 入力フィルター"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"[nichinan-filter] フィルター起動: enabled={self.valves.enabled}")

    async def on_shutdown(self):
        print("[nichinan-filter] フィルター停止")

    def _block(self, body: dict, warning: str) -> dict:
        """ブロック時: モデルに警告メッセージだけを返させる"""
        # RAG/ナレッジ検索を回避するためファイル・メタデータを除去
        body.pop("files", None)
        body.pop("tool_ids", None)
        if "metadata" in body:
            body["metadata"].pop("files", None)
            body["metadata"].pop("knowledge", None)
            body["metadata"].pop("tool_ids", None)

        body["messages"] = [
            {
                "role": "system",
                "content": (
                    "あなたはセキュリティフィルターです。"
                    "次のユーザーメッセージの内容をそのまま出力してください。"
                    "一切の変更・追加・省略をせず、そのまま出力してください。"
                ),
            },
            {
                "role": "user",
                "content": warning,
            },
        ]
        return body

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """入力時のフィルタリング（モデルに渡す前）"""
        if not self.valves.enabled:
            return body

        messages = body.get("messages", [])
        if not messages:
            return body

        # デバッグ: メッセージの内容を出力
        last_msg = messages[-1].get("content", "")
        print(f"[nichinan-filter] messages count: {len(messages)}, last role: {messages[-1].get('role','?')}, last content length: {len(last_msg) if isinstance(last_msg, str) else 'N/A'}")
        if isinstance(last_msg, str) and len(last_msg) > 100:
            print(f"[nichinan-filter] last content preview: {last_msg[:200]}...")

        # 最新のユーザーメッセージを取得
        user_message = messages[-1].get("content", "")
        if not isinstance(user_message, str):
            return body

        # ユーザーの元の入力のみを取得（roleがuserの最後のメッセージ）
        # RAGコンテキスト付与前の生メッセージを対象にする
        raw_user_messages = [
            m.get("content", "")
            for m in messages
            if m.get("role") == "user" and isinstance(m.get("content", ""), str)
        ]
        if not raw_user_messages:
            return body
        user_message = raw_user_messages[-1]

        # Open WebUIの内部タスク（検索クエリ生成・フォローアップ生成等）はスキップ
        if user_message.strip().startswith("### Task:"):
            return body

        user_message_lower = user_message.lower().strip()

        # 1. 空メッセージチェック
        if not user_message_lower:
            return self._block(body, "メッセージを入力してください。")

        # 2. 文字数制限チェック
        if len(user_message) > self.valves.max_input_length:
            return self._block(
                body,
                f"⚠️ 入力が長すぎます（{len(user_message)}文字）。"
                f"{self.valves.max_input_length}文字以内でお願いします。",
            )

        # 3. 不適切キーワードチェック
        blocked = [
            kw.strip()
            for kw in self.valves.blocked_keywords.split(",")
            if kw.strip()
        ]
        for keyword in blocked:
            if keyword in user_message_lower:
                return self._block(body, self.valves.warning_message)

        # 4. プロンプトインジェクション検知
        injection_patterns = [
            p.strip()
            for p in self.valves.prompt_injection_patterns.split(",")
            if p.strip()
        ]
        for pattern in injection_patterns:
            if pattern.lower() in user_message_lower:
                return self._block(
                    body,
                    "⚠️ 不正な操作が検出されました。\n通常の質問をお願いします。",
                )

        # 5. 過度な繰り返し文字の検出
        if re.search(r"(.)\1{20,}", user_message):
            return self._block(
                body, "⚠️ 入力内容に問題があります。通常の質問をお願いします。"
            )

        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """出力時のフィルタリング（ユーザーに返す前）"""
        # 出力側は現状パススルー（必要に応じて追加可能）
        return body
