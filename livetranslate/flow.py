import signal
from dataclasses import dataclass
from types import FrameType
from typing import Any, Callable

_handler = Callable[[int, FrameType | None], Any]


@dataclass(kw_only=True)
class ProgramState:
    keyboard_interrupt: bool = False

    def make_handler(self, handler: _handler) -> _handler:
        def handle_keyboard_interrupt(signal: int, frame: FrameType | None) -> None:
            self.keyboard_interrupt = True
            handler(signal, frame)

        return handle_keyboard_interrupt


keyboard_interrupt = False


def register() -> ProgramState:
    state: ProgramState = ProgramState()
    original_sigint_handler: Any = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, state.make_handler(original_sigint_handler))

    return state
