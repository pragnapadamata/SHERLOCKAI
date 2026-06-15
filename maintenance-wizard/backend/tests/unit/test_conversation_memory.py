"""In-process conversation memory: append, retrieve, window, isolation."""

from __future__ import annotations

from backend.app.conversation.memory import ConversationMemory


def test_append_and_get():
    mem = ConversationMemory(clock=lambda: "t0")
    mem.append("s1", "user", "hi")
    mem.append("s1", "assistant", "hello", provenance=[{"kind": "record", "table": "x", "id": "1"}])
    session = mem.get("s1")
    assert [t.role for t in session.turns] == ["user", "assistant"]
    assert session.turns[1].provenance[0]["table"] == "x"
    assert session.turns[0].timestamp == "t0"


def test_history_window_returns_recent_messages():
    mem = ConversationMemory(clock=lambda: "t")
    for i in range(10):
        mem.append("s", "user", f"q{i}")
    msgs = mem.history_messages("s", 4)
    assert len(msgs) == 4
    assert msgs[-1].content == "q9"
    assert all(m.role == "user" for m in msgs)


def test_sessions_are_isolated():
    mem = ConversationMemory()
    mem.append("a", "user", "x")
    assert mem.get("b").turns == []
