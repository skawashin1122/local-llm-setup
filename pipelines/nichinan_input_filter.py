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

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """入力時のフィルタリング（モデルに渡す前）"""
        if not self.valves.enabled:
            return body

        messages = body.get("messages", [])
        if not messages:
            return body

        # 最新のユーザーメッセージを取得
        user_message = messages[-1].get("content", "")
        if not isinstance(user_message, str):
            return body

        user_message_lower = user_message.lower().strip()

        # 1. 空メッセージチェック
        if not user_message_lower:
            raise Exception("メッセージを入力してください。")

        # 2. 文字数制限チェック
        if len(user_message) > self.valves.max_input_length:
            raise Exception(
                f"⚠️ 入力が長すぎます（{len(user_message)}文字）。"
                f"{self.valves.max_input_length}文字以内でお願いします。"
            )

        # 3. 不適切キーワードチェック
        blocked = [
            kw.strip()
            for kw in self.valves.blocked_keywords.split(",")
            if kw.strip()
        ]
        for keyword in blocked:
            if keyword in user_message_lower:
                raise Exception(self.valves.warning_message)

        # 4. プロンプトインジェクション検知
        injection_patterns = [
            p.strip()
            for p in self.valves.prompt_injection_patterns.split(",")
            if p.strip()
        ]
        for pattern in injection_patterns:
            if pattern.lower() in user_message_lower:
                raise Exception(
                    "⚠️ 不正な操作が検出されました。\n"
                    "通常の質問をお願いします。"
                )

        # 5. 過度な繰り返し文字の検出
        if re.search(r"(.)\1{20,}", user_message):
            raise Exception("⚠️ 入力内容に問題があります。通常の質問をお願いします。")

        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """出力時のフィルタリング（ユーザーに返す前）"""
        # 出力側は現状パススルー（必要に応じて追加可能）
        return body
