"""The end-of-turn progress flush never re-sends a bubble's unchanged text as an edit.

The final flush raced the progress sender: when the sender had already delivered the bubble, the
flush edited it again with identical text (a wasted platform call; flaky in
tests/gateway/test_hold_stream_delivery.py). Adapters that seal a bubble by editing still get it.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from gateway.platforms.base import SendResult
from gateway.run_turn_progress import GatewayTurnProgressMixin


class _Chat:
    def __init__(self, finalize: bool = False):
        self.calls: list[tuple[str, str]] = []
        self.REQUIRES_EDIT_FINALIZE = finalize

    async def send(self, chat_id, content, reply_to=None, metadata=None):
        self.calls.append(("send", content))
        return SendResult(success=True, message_id="m1")

    async def edit_message(self, chat_id, message_id, content, finalize=False):
        self.calls.append(("edit", content))
        return SendResult(success=True, message_id=message_id)


def _runner_and_state(chat):
    runner = GatewayTurnProgressMixin.__new__(GatewayTurnProgressMixin)
    runner._ctx = SimpleNamespace(source=SimpleNamespace(chat_id="c1"), _progress_metadata=None,
                                  _progress_reply_to=None, _cleanup_progress=False, _cleanup_msg_ids=[])
    state = GatewayTurnProgressMixin._ProgressEditState(
        adapter=chat, progress_lines=["📋 todo_list..."], progress_msg_id=None, can_edit=True,
        _progress_len_fn=len, _PROGRESS_TEXT_LIMIT=4000, _edit_accepts_metadata=False)
    return runner, state


async def _send_then_flush(chat, lines_after_send):
    runner, state = _runner_and_state(chat)
    await runner._progress_send_or_edit(state, state.progress_lines[-1])
    state.progress_lines.extend(lines_after_send)
    await runner._flush_progress_edit(state)


@pytest.mark.parametrize("finalize, later, edited", [
    (False, [], False),                    # unchanged bubble: no edit
    (False, ["🔎 search_files..."], True),  # a new line still reaches the bubble
    (True, [], True),                      # adapters that seal by editing keep the final edit
])
def test_final_flush_edits_only_a_changed_or_sealable_bubble(finalize, later, edited):
    chat = _Chat(finalize=finalize)
    asyncio.run(_send_then_flush(chat, later))
    assert chat.calls[0] == ("send", "📋 todo_list...")
    assert any(kind == "edit" for kind, _ in chat.calls[1:]) is edited, chat.calls
