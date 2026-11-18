# Vendored (copied, not imported) from lupin-desk (github.com/NathanLCR/lupin-desk) app/llm.py: constants and TagStreamParser.
import re
from dataclasses import dataclass, field

# Official list of the 12 emotions supported by the EMO-style face.
SUPPORTED_EMOTIONS: tuple[str, ...] = (
    "neutral",
    "happy",
    "excited",
    "curious",
    "skeptical",
    "surprised",
    "sad",
    "wink",
    "love",
    "sleepy",
    "angry",
    "dizzy",
)
VALID_EMOTIONS: frozenset[str] = frozenset(SUPPORTED_EMOTIONS)

_EMOTION_TAG_RE = re.compile(r"^\[emotion\s*:\s*([a-zA-Z0-9_-]+)\s*\]$", re.IGNORECASE)
_SHORT_EMOTION_TAG_RE = re.compile(r"^\[\s*([a-zA-Z0-9_-]+)\s*\]$")
_FACT_TAG_RE = re.compile(r"^\[fact\s*:\s*(.*?)\s*\]$", re.IGNORECASE | re.DOTALL)
_ACTION_TAG_RE = re.compile(
    r"^\[action\s*:\s*(shortcut|app|pomodoro|today)\s*:\s*(.*?)\s*\]$",
    re.IGNORECASE | re.DOTALL,
)
_KNOWN_TAG_PREFIXES: tuple[str, ...] = (
    "[emotion",
    "[fact",
    "[action",
    *(f"[{emotion}" for emotion in SUPPORTED_EMOTIONS),
)

# Safety limit to avoid unbounded buffering when a '[' is never closed.
_MAX_TAG_BUFFER_CHARS = 256


@dataclass
class TagStreamParser:
    """Incremental parser that strips `[emotion:...]`, `[fact:...]` and `[action:...]` tags from the stream.

    Guarantees that no internal tag leaks into the `delta`/`sentence` events sent to the frontend/TTS,
    even when the brackets or the tag content arrive split across several chunks.
    """

    emotion_emitted: bool = False
    detected_emotion: str = "neutral"
    _buffer: str = ""
    _sentence_buf: str = ""
    _raw_parts: list[str] = field(default_factory=list)
    _clean_parts: list[str] = field(default_factory=list)
    _has_emitted_text: bool = False

    def feed(self, chunk: str) -> list[dict[str, str]]:
        """Process a `delta.content` chunk and return ready-to-send structured events."""
        if not chunk:
            return []

        self._raw_parts.append(chunk)
        self._buffer += chunk
        events: list[dict[str, str]] = []

        while self._buffer:
            if not self._has_emitted_text and not self._buffer.startswith("["):
                # Drop leading whitespace before the first tag or the first useful text.
                stripped = self._buffer.lstrip()
                if not stripped:
                    self._buffer = ""
                    break
                self._buffer = stripped

            if self._buffer.startswith("["):
                close_idx = self._buffer.find("]")
                if close_idx != -1:
                    tag = self._buffer[: close_idx + 1]
                    self._buffer = self._buffer[close_idx + 1 :]
                    events.extend(self._handle_closed_tag(tag))
                    continue

                # Still waiting for the closing ']' of the tag.
                if len(self._buffer) > _MAX_TAG_BUFFER_CHARS and not self._looks_like_known_tag_prefix(
                    self._buffer
                ):
                    # Does not look like one of our tags; release it as plain text so the stream does not stall.
                    text = self._buffer
                    self._buffer = ""
                    events.extend(self._emit_text(text))
                break

            next_bracket = self._buffer.find("[")
            if next_bracket == -1:
                text = self._buffer
                self._buffer = ""
                events.extend(self._emit_text(text))
            else:
                text = self._buffer[:next_bracket]
                self._buffer = self._buffer[next_bracket:]
                events.extend(self._emit_text(text))

        return events

    def finish(self) -> tuple[list[dict[str, str]], str, str, str]:
        """Finish the stream, drain the safe remainder of the buffer and return the full result.

        Returns `(final_events, clean_text, raw_text, emotion)`.
        """
        events: list[dict[str, str]] = []

        if self._buffer:
            # If an incomplete `[emotion...`, `[fact...`, `[action...` or `[happy...` tag is left over,
            # discard it so markup never leaks to the user/TTS.
            if not self._looks_like_known_tag_prefix(self._buffer):
                events.extend(self._emit_text(self._buffer))
            self._buffer = ""

        if not self.emotion_emitted:
            self.emotion_emitted = True
            self.detected_emotion = "neutral"
            events.append({"type": "emotion", "emotion": "neutral"})

        remainder = self._sentence_buf.strip()
        self._sentence_buf = ""
        if remainder and any(ch.isalnum() for ch in remainder):
            events.append({"type": "sentence", "text": remainder})

        clean_text = "".join(self._clean_parts).strip()
        raw_text = "".join(self._raw_parts)
        return events, clean_text, raw_text, self.detected_emotion

    @staticmethod
    def _looks_like_known_tag_prefix(text: str) -> bool:
        """Check whether the start of the buffer may match a known protocol tag."""
        lower = text.lstrip().lower()
        for prefix in _KNOWN_TAG_PREFIXES:
            if lower.startswith(prefix) or prefix.startswith(lower):
                return True
        return False

    def _handle_closed_tag(self, tag: str) -> list[dict[str, str]]:
        """Interpret a complete `[...]` tag and return the matching events."""
        emotion_match = _EMOTION_TAG_RE.match(tag)
        if emotion_match:
            candidate = emotion_match.group(1).strip().lower()
            valid_emotion = candidate if candidate in VALID_EMOTIONS else "neutral"
            if not self.emotion_emitted:
                self.emotion_emitted = True
                self.detected_emotion = valid_emotion
                return [{"type": "emotion", "emotion": valid_emotion}]
            return []

        short_match = _SHORT_EMOTION_TAG_RE.match(tag)
        if short_match:
            candidate = short_match.group(1).strip().lower()
            if candidate in VALID_EMOTIONS:
                if not self.emotion_emitted:
                    self.emotion_emitted = True
                    self.detected_emotion = candidate
                    return [{"type": "emotion", "emotion": candidate}]
                return []

        if _FACT_TAG_RE.match(tag):
            # Fact tags stay only in raw_text, for extraction by the memory layer.
            return []

        action_match = _ACTION_TAG_RE.match(tag)
        if action_match:
            kind = action_match.group(1).strip().lower()
            target = " ".join(action_match.group(2).strip().split())
            if target:
                return [{"type": "action", "kind": kind, "target": target}]
            return []

        # Ordinary brackets that are not control tags become spoken text.
        return self._emit_text(tag)

    def _emit_text(self, text: str) -> list[dict[str, str]]:
        """Emit clean text, guaranteeing an emotion before the first delta, plus any completed sentences."""
        events: list[dict[str, str]] = []
        if not self._has_emitted_text:
            text = text.lstrip()
            if not text:
                return events

        if not self.emotion_emitted:
            self.emotion_emitted = True
            self.detected_emotion = "neutral"
            events.append({"type": "emotion", "emotion": "neutral"})

        self._has_emitted_text = True
        self._clean_parts.append(text)
        events.append({"type": "delta", "text": text})

        self._sentence_buf += text
        events.extend(self._pop_complete_sentences())
        return events

    def _pop_complete_sentences(self) -> list[dict[str, str]]:
        """Extract complete sentences ending in `.`, `!` or `?` from the sentence buffer."""
        emitted: list[dict[str, str]] = []
        buf = self._sentence_buf
        start = 0
        i = 0
        length = len(buf)

        while i < length:
            ch = buf[i]
            if ch in ".!?":
                # Keep grouped punctuation (`...`, `!?`, `!!`) together in the same sentence.
                if i + 1 < length and buf[i + 1] in ".!?":
                    i += 1
                    continue
                # Do not split decimals such as `3.14` when the next digit is already in the buffer.
                if (
                    ch == "."
                    and i > 0
                    and buf[i - 1].isdigit()
                    and i + 1 < length
                    and buf[i + 1].isdigit()
                ):
                    i += 1
                    continue

                end = i + 1
                # Include closing quotes/brackets right after the punctuation, if any.
                while end < length and buf[end] in "\"')]}":
                    end += 1

                candidate = buf[start:end].strip()
                if candidate and any(c.isalnum() for c in candidate):
                    emitted.append({"type": "sentence", "text": candidate})
                    start = end
                    i = end
                    continue
            i += 1

        if start > 0:
            self._sentence_buf = buf[start:]
        return emitted


