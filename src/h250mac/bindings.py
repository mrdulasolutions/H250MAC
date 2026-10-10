"""Thread-safe key bindings for the HID listener and menu bar."""

from __future__ import annotations

import threading
from dataclasses import dataclass

from h250mac.keys import KeyChord, canonical_key_name, resolve_chord


@dataclass(frozen=True)
class BindingSnapshot:
    names: dict[int, str]
    chords: dict[int, KeyChord | None]


class BindingStore:
    def __init__(self, primary: str, secondary: str = "") -> None:
        self._lock = threading.Lock()
        self._primary = canonical_key_name(primary)
        self._secondary = canonical_key_name(secondary)

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
            self._primary = canonical_key_name(name)

    def set_secondary(self, name: str) -> None:
        with self._lock:
            self._secondary = canonical_key_name(name)

    def snapshot(self) -> BindingSnapshot:
        with self._lock:
            primary = self._primary
            secondary = self._secondary
        chord1 = resolve_chord(primary)
        chord2 = resolve_chord(secondary) if secondary else None
        return BindingSnapshot(
            names={1: primary, 2: secondary},
            chords={1: chord1, 2: chord2},
        )
