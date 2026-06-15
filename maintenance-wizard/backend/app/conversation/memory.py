"""In-process conversational memory keyed by session_id.

Holds the user queries and assistant final answers (with each answer's
provenance, for follow-ups), not the full tool transcripts. Behind a small
interface so the API phase can swap in a persistent store. Only recent turns flow
back to the orchestrator (token control).
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from backend.app.llm.messages import Message


@dataclass
class Turn:
    role: str  # "user" | "assistant"
    content: str
    timestamp: str
    provenance: list[dict] = field(default_factory=list)


@dataclass
class Session:
    session_id: str
    turns: list[Turn] = field(default_factory=list)


class ConversationMemory:
    """A simple in-process session store."""

    def __init__(self, clock: Callable[[], str] | None = None) -> None:
        self._sessions: dict[str, Session] = {}
        self._clock = clock or (lambda: datetime.now().isoformat(timespec="seconds"))
        # Guards the sessions dict and each session's turn list against concurrent
        # appends/reads (the API runs sync handlers across a threadpool).
        self._lock = threading.Lock()

    def _session(self, session_id: str) -> Session:
        """Get-or-create the session. Caller MUST hold ``self._lock``."""

        return self._sessions.setdefault(session_id, Session(session_id=session_id))

    def get(self, session_id: str) -> Session:
        with self._lock:
            return self._session(session_id)

    def append(self, session_id: str, role: str, content: str,
               provenance: list[dict] | None = None) -> Turn:
        turn = Turn(role=role, content=content, timestamp=self._clock(),
                    provenance=provenance or [])
        with self._lock:
            self._session(session_id).turns.append(turn)
        return turn

    def history_messages(self, session_id: str, max_turns: int) -> list[Message]:
        """Return the last ``max_turns`` turns as chat messages for the orchestrator."""

        with self._lock:
            turns = list(self._session(session_id).turns)
        recent = turns[-max_turns:] if max_turns > 0 else []
        return [Message(role=t.role, content=t.content) for t in recent]
