"""Thread-safe key bindings for the HID listener and menu bar."""

from __future__ import annotations

import threading
from dataclasses import dataclass

from h250mac.keys import resolve_key


@dataclass(frozen=True)
class BindingSnapshot:
    names: dict[int, str]
    keycodes: dict[int, int | None]


class BindingStore:
    def __init__(self, primary: str, secondary: str = "") -> None:
        self._lock = threading.Lock()
        self._primary = primary.strip().lower()
        self._secondary = secondary.strip().lower()

    @property
    def primary(self) -> str:
        with self._lock:
            return self._primary

    @property
    def secondary(self) -> str:
        with self._lock:
            return self._secondary

    def set_primary(self, name: str) -> None:
        with self._lock:
            self._primary = name.strip().lower()

    def set_secondary(self, name: str) -> None:
        with self._lock:
            self._secondary = name.strip().lower()

    def snapshot(self) -> BindingSnapshot:
        with self._lock:
            primary = self._primary
            secondary = self._secondary
        key1 = resolve_key(primary)
        key2 = resolve_key(secondary) if secondary else None
        return BindingSnapshot(
            names={1: primary, 2: secondary},
            keycodes={1: key1, 2: key2},
        )
