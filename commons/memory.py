from __future__ import annotations

from pathlib import Path
import os
from typing import Any, Iterable

from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.llms import ChatMessage, MessageRole


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


_MEMORY_DIR = Path(os.getenv("KITTY_MEMORY_DIR", str(_repo_root() / "memory")))
_CHAT_STORE_PATH = Path(
    os.getenv("KITTY_CHAT_STORE_PATH", str(_MEMORY_DIR / "chat_store.json"))
)
_TOKEN_LIMIT = _int_env("KITTY_MEMORY_TOKEN_LIMIT", 3000)
_MAX_BYTES = _int_env("KITTY_CHAT_STORE_MAX_BYTES", 1024 * 1024 * 1024)
_TRIM_BATCH = _int_env("KITTY_CHAT_STORE_TRIM_BATCH", 200)
_GLOBAL_KEY = "__global__"


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


class JsonChatMemory:
    def __init__(self) -> None:
        _ensure_parent(_CHAT_STORE_PATH)
        if _CHAT_STORE_PATH.exists():
            self._chat_store = SimpleChatStore.from_persist_path(str(_CHAT_STORE_PATH))
        else:
            self._chat_store = SimpleChatStore()

        self._buffers: dict[str, ChatMemoryBuffer] = {}

    def _buffer(self, key: str) -> ChatMemoryBuffer:
        if key not in self._buffers:
            self._buffers[key] = ChatMemoryBuffer.from_defaults(
                token_limit=_TOKEN_LIMIT,
                chat_store=self._chat_store,
                chat_store_key=key,
            )
        return self._buffers[key]

    def _persist(self) -> None:
        self._chat_store.persist(str(_CHAT_STORE_PATH))
        self._enforce_size_limit()

    def _store_dict(self) -> dict[str, Any] | None:
        for attr in ("store", "_store", "chat_store", "_chat_store"):
            store = getattr(self._chat_store, attr, None)
            if isinstance(store, dict):
                return store
        return None

    @staticmethod
    def _as_message_list(value: Any) -> list[Any] | None:
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for key in ("messages", "chat_history"):
                candidate = value.get(key)
                if isinstance(candidate, list):
                    return candidate
        return None

    def _enforce_size_limit(self) -> None:
        if _MAX_BYTES <= 0:
            return
        try:
            size = _CHAT_STORE_PATH.stat().st_size
        except FileNotFoundError:
            return
        if size <= _MAX_BYTES:
            return

        store = self._store_dict()
        if not store:
            return

        message_lists: dict[str, list[Any]] = {}
        for key, value in store.items():
            messages = self._as_message_list(value)
            if messages is not None:
                message_lists[key] = messages

        if not message_lists:
            return

        trimmed = 0
        while size > _MAX_BYTES and message_lists:
            key = max(message_lists, key=lambda k: len(message_lists[k]))
            messages = message_lists[key]
            if not messages:
                message_lists.pop(key, None)
                continue
            messages.pop(0)
            trimmed += 1
            if trimmed % _TRIM_BATCH == 0:
                self._chat_store.persist(str(_CHAT_STORE_PATH))
                try:
                    size = _CHAT_STORE_PATH.stat().st_size
                except FileNotFoundError:
                    return

        if trimmed:
            self._chat_store.persist(str(_CHAT_STORE_PATH))
            self._buffers = {}

    @staticmethod
    def _role_from_str(role: str) -> MessageRole:
        role_lc = role.strip().lower()
        if role_lc == "user":
            return MessageRole.USER
        if role_lc == "assistant":
            return MessageRole.ASSISTANT
        if role_lc == "system":
            return MessageRole.SYSTEM
        return MessageRole.TOOL

    @staticmethod
    def _format_messages(messages: Iterable[ChatMessage]) -> str:
        lines: list[str] = []
        for message in messages:
            role = getattr(message.role, "value", str(message.role))
            lines.append(f"{role}: {message.content}")
        return "\n".join(lines)

    def add_message(self, key: str, role: str, content: str) -> None:
        msg = ChatMessage(role=self._role_from_str(role), content=content)
        self._buffer(key).put(msg)

    def add_turn(self, user: str, user_text: str, assistant_text: str) -> None:
        self.add_message(user, "user", user_text)
        self.add_message(user, "assistant", assistant_text)
        self.add_message(_GLOBAL_KEY, "user", user_text)
        self.add_message(_GLOBAL_KEY, "assistant", assistant_text)
        self._persist()

    def get_user_context(self, user: str) -> str:
        return self._format_messages(self._buffer(user).get())

    def get_global_context(self) -> str:
        return self._format_messages(self._buffer(_GLOBAL_KEY).get())


memory = JsonChatMemory()
