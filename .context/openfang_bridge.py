import asyncio
import httpx
import magic  # 需要 pip install python-magic
from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import logging

# ==========================================
# 1. 核心数据结构 (复刻 types.rs)
# ==========================================

class ChannelType(str, Enum):
    TELEGRAM = "Telegram"
    WHATSAPP = "WhatsApp"
    SLACK = "Slack"
    DISCORD = "Discord"
    FEISHU = "Feishu"
    DINGTALK = "DingTalk"
    WEBCHAT = "WebChat"
    CLI = "CLI"
    CUSTOM = "Custom"

class ChannelUser(BaseModel):
    platform_id: str
    display_name: str
    openfang_user: Optional[str] = None

class ChannelContent(BaseModel):
    text: Optional[str] = None
    image_url: Optional[str] = None
    file_url: Optional[str] = None
    command: Optional[Dict[str, Any]] = None  # {"name": str, "args": list}

class ChannelMessage(BaseModel):
    channel: ChannelType
    platform_message_id: str
    sender: ChannelUser
    content: ChannelContent
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_group: bool = False
    thread_id: Optional[str] = None
    metadata: Dict[str, Any] = {}

# ==========================================
# 2. 核心调度与 Dify 适配 (复刻 bridge.rs)
# ==========================================

class OpenFangBridge:
    def __init__(self, dify_api_key: str, dify_base_url: str = "https://api.dify.ai/v1"):
        self.dify_api_key = dify_api_key
        self.dify_base_url = dify_base_url
        # 限制并发，防止 Dify API 或本地内存过载 (对应 Rust 的 Semaphore 32)
        self.semaphore = asyncio.Semaphore(32)
        self.client = httpx.AsyncClient(timeout=60.0)

    async def handle_incoming(self, message_json: Dict[str, Any]):
        """处理来自 Rust 触角端转发过来的原始消息"""
        try:
            message = ChannelMessage(**message_json)
            # 异步非阻塞处理，对应 Rust 的 tokio::spawn
            asyncio.create_task(self._dispatch_with_semaphore(message))
        except Exception as e:
            logging.error(f"Failed to parse OpenFang message: {e}")

    async def _dispatch_with_semaphore(self, message: ChannelMessage):
        async with self.semaphore:
            await self._dispatch(message)

    async def _dispatch(self, message: ChannelMessage):
        """核心分发逻辑"""
        # 1. 指令检查 (复刻 bridge.rs 的 handle_command)
        if message.content.command:
            response_text = await self._handle_internal_command(message)
            await self._send_back(message, response_text)
            return

        # 2. 准备 Dify 输入
        query = self._prepare_query(message)
        files = self._prepare_files(message)

        # 3. 调用 Dify 大脑
        print(f"🧠 [Dify] Thinking for {message.sender.display_name} via {message.channel}...")
        try:
            dify_response = await self._call_dify_api(query, files, message.sender.platform_id)
            # 4. 回发给通道
            await self._send_back(message, dify_response)
        except Exception as e:
            logging.error(f"Dify processing error: {e}")
            await self._send_back(message, "⚠️ AI 思考过程中出现错误，请稍后再试。")

    # ==========================================
    # 3. 辅助逻辑 (复刻 Rust 内部函数)
    # ==========================================

    def _prepare_query(self, message: ChannelMessage) -> str:
        """复刻 Rust 的前缀逻辑，确保 AI 知道是谁在说话"""
        text = message.content.text or ""
        if message.is_group:
            # 群聊中加上发送者名称前缀
            return f"[From: {message.sender.display_name}] {text}"
        return text

    def _prepare_files(self, message: ChannelMessage) -> List[Dict]:
        """多模态支持：将 OpenFang 图片转换为 Dify 格式"""
        if message.content.image_url:
            return [{
                "type": "image",
                "transfer_method": "remote_url",
                "url": message.content.image_url
            }]
        return []

    async def _call_dify_api(self, query: str, files: List[Dict], user_id: str) -> str:
        """调用 Dify Chat 接口"""
        headers = {"Authorization": f"Bearer {self.dify_api_key}"}
        data = {
            "inputs": {},
            "query": query,
            "response_mode": "blocking",
            "conversation_id": "", # 实际应用中应从本地数据库/缓存获取
            "user": user_id,
            "files": files
        }
        resp = await self.client.post(f"{self.dify_base_url}/chat-messages", json=data, headers=headers)
        resp.raise_for_status()
        return resp.json().get("answer", "")

    async def _send_back(self, original_msg: ChannelMessage, response_text: str):
        """
        这里需要调用你 Rust 暴露出的 Webhook 或具体的平台 SDK。
        例如回发给钉钉或飞书的逻辑。
        """
        print(f"📤 [Reply] -> {original_msg.sender.display_name}: {response_text[:50]}...")
        # 实现具体的发送逻辑...

    async def _handle_internal_command(self, message: ChannelMessage) -> str:
        """复刻 Rust 的指令系统，如 /start, /new"""
        cmd_name = message.content.command['name']
        if cmd_name == "start":
            return "Welcome! I am your OpenFang AI assistant powered by Dify."
        if cmd_name == "new":
            return "Session reset. Let's start over!"
        return f"Command /{cmd_name} executed."

# ==========================================
# 使用示例
# ==========================================
if __name__ == "__main__":
    bridge = OpenFangBridge(dify_api_key="app-your-key-here")
    
    # 模拟一条来自 Rust 端的 JSON 消息 (飞书/钉钉)
    mock_raw_msg = {
        "channel": "Feishu",
        "platform_message_id": "msg_888",
        "sender": {
            "platform_id": "u_123",
            "display_name": "张三"
        },
        "content": {
            "text": "分析一下这个图",
            "image_url": "https://example.com/photo.jpg"
        },
        "is_group": True
    }
    
    asyncio.run(bridge.handle_incoming(mock_raw_msg))