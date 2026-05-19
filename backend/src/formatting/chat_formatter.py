#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Visual Markdown post-processing for final C.O.R.A. answers.

The formatter is intentionally conservative: it only changes spacing and
light Markdown structure, while preserving content, citations, numbers and
literal blocks.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Callable, Dict, List, Optional, Tuple


CODE_BLOCK_RE = re.compile(r"(```.*?```)", re.DOTALL)
ORDER_MARKER_RE = re.compile(
    r"\b(primeiro|primeira|segundo|segunda|terceiro|terceira|depois|em seguida|por fim|por ultimo|por último)\b",
    re.IGNORECASE,
)
LEGAL_LITERAL_RE = re.compile(
    r"(\b(art\.|artigo|inciso|al[ií]nea|lei\s+n[ºo°.]?|in verbis)\b|§)",
    re.IGNORECASE,
)
DIRECT_QUOTE_RE = re.compile(r'["“”]')
MARKDOWN_BLOCK_RE = re.compile(
    r"^\s*(#{1,6}\s+|[-*+]\s+|\d+\.\s+|[a-z]\)\s+|>\s+|\|.*\|)",
    re.IGNORECASE | re.MULTILINE,
)
VISUAL_MARKER_RE = re.compile(
    r"(?m)^\s*(?:[-*+]\s+|>\s+|\d+\.\s+|[a-z]\)\s+)"
)


def is_chat_formatting_enabled(value: Optional[str] = None) -> bool:
    """Return True only when the feature flag is explicitly set to true."""
    raw_value = os.getenv("ENABLE_CHAT_FORMATTING", "false") if value is None else value
    return str(raw_value).strip().lower() == "true"


def _split_code_blocks(answer: str) -> List[Tuple[str, bool]]:
    parts = CODE_BLOCK_RE.split(answer)
    return [(part, bool(CODE_BLOCK_RE.fullmatch(part))) for part in parts if part]


def _split_sentences(text: str) -> List[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])", text.strip())
        if sentence.strip()
    ]


def _is_probably_literal_or_legal(text: str) -> bool:
    if DIRECT_QUOTE_RE.search(text):
        return True
    if LEGAL_LITERAL_RE.search(text):
        return True
    if re.search(r"\b[IVXLCDM]+\s+-", text):
        return True
    return False


def _canonical_verbatim_text(text: str) -> str:
    """Normalize only visual Markdown/spacing added by this formatter."""
    chunks: List[str] = []
    for segment, is_code in _split_code_blocks(str(text)):
        if is_code:
            chunks.append(segment)
            continue

        cleaned = VISUAL_MARKER_RE.sub("", segment)
        chunks.append(cleaned)

    return re.sub(r"\s+", " ", "".join(chunks)).strip()


def _preserves_verbatim_text(original: str, formatted: str) -> bool:
    """Ensure the LLM wording survives exactly, aside from visual markers."""
    return _canonical_verbatim_text(original) == _canonical_verbatim_text(formatted)


def _split_trailing_observation(text: str) -> Tuple[str, str]:
    match = re.match(
        r"(.+?[.!?])\s+((?:caso|quando|se\s+o\s+contexto|a\s+aus[eê]ncia|observa[cç][aã]o|ressalta-se|importante|no entanto|contudo)\b.+)$",
        text,
        flags=re.IGNORECASE,
    )
    if not match:
        return text, ""
    return match.group(1).strip(), match.group(2).strip()


def _format_semicolon_list(paragraph: str) -> Optional[str]:
    if ":" not in paragraph or ";" not in paragraph:
        return None
    if _is_probably_literal_or_legal(paragraph):
        return None

    intro, tail = paragraph.split(":", 1)
    intro = intro.strip()
    tail = tail.strip()
    if not intro or not tail or len(intro) > 220:
        return None

    raw_parts = tail.split(";")
    final_items: List[str] = []
    for index, part in enumerate(raw_parts):
        item = part.strip()
        if not item:
            continue
        suffix = ";" if index < len(raw_parts) - 1 else ""
        final_items.append(f"{item}{suffix}")

    if len(final_items) < 2:
        return None

    trailing_text = ""
    final_items[-1], trailing_text = _split_trailing_observation(final_items[-1])

    bullet_lines = "\n".join(f"- {item}" for item in final_items)
    formatted = f"{intro}:\n\n{bullet_lines}"
    if trailing_text:
        formatted += f"\n\n{_format_observation(trailing_text)}"
    return formatted


def _format_ordered_sequence(paragraph: str) -> Optional[str]:
    if _is_probably_literal_or_legal(paragraph):
        return None
    if not ORDER_MARKER_RE.search(paragraph):
        return None

    sentences = _split_sentences(paragraph)
    marker_count = sum(1 for sentence in sentences if ORDER_MARKER_RE.search(sentence))
    if len(sentences) < 3 or marker_count < 2:
        return None

    lines = []
    for index, sentence in enumerate(sentences, start=1):
        lines.append(f"{index}. {sentence}")
    return "\n".join(lines)


def _format_long_paragraph(paragraph: str) -> str:
    if len(paragraph) < 360 or _is_probably_literal_or_legal(paragraph):
        return paragraph

    sentences = _split_sentences(paragraph)
    if len(sentences) < 3:
        return paragraph

    return "\n\n".join(sentences)


def _format_observation(paragraph: str) -> str:
    if paragraph.startswith(">") or MARKDOWN_BLOCK_RE.search(paragraph):
        return paragraph

    if re.match(
        r"^(caso|quando|se\s+o\s+contexto|a\s+aus[eê]ncia|observa[cç][aã]o|ressalta-se|importante|no entanto|contudo)\b",
        paragraph,
        flags=re.IGNORECASE,
    ):
        return "> " + paragraph

    return paragraph


def _format_paragraph(paragraph: str) -> str:
    stripped = paragraph.strip()
    if not stripped:
        return ""
    if MARKDOWN_BLOCK_RE.search(stripped):
        return stripped

    for formatter in (_format_semicolon_list, _format_ordered_sequence):
        formatted = formatter(stripped)
        if formatted and _preserves_verbatim_text(stripped, formatted):
            return formatted

    stripped = _format_long_paragraph(stripped)
    stripped = _format_observation(stripped)
    return stripped


def _format_text_segment(text: str) -> str:
    if not text.strip():
        return text

    leading = re.match(r"^\s*", text).group(0)
    trailing = re.search(r"\s*$", text).group(0)
    core_end = len(text) - len(trailing) if trailing else len(text)
    core = text[len(leading):core_end].replace("\r\n", "\n").replace("\r", "\n")
    if not core:
        return text

    paragraphs = re.split(r"\n\s*\n", core)
    formatted_paragraphs = [_format_paragraph(paragraph) for paragraph in paragraphs]
    formatted_core = "\n\n".join(paragraph for paragraph in formatted_paragraphs if paragraph)
    return f"{leading}{formatted_core}{trailing}"


def format_for_chat(answer: str, options: Optional[Dict] = None) -> str:
    """Apply visual Markdown formatting while preserving answer content."""
    del options

    if not answer:
        return answer

    try:
        segments = _split_code_blocks(str(answer))
        formatted = "".join(
            segment if is_code else _format_text_segment(segment)
            for segment, is_code in segments
        )

        original = str(answer)
        if len(formatted) < len(original):
            return answer
        if not _preserves_verbatim_text(original, formatted):
            return answer

        return formatted
    except Exception:
        return answer


def apply_chat_formatting(
    answer: str,
    *,
    enabled: Optional[bool] = None,
    logger: Optional[logging.Logger] = None,
    formatter: Callable[[str], str] = format_for_chat,
) -> str:
    """Feature-flagged wrapper with safe fallback and audit logs."""
    active = is_chat_formatting_enabled() if enabled is None else bool(enabled)
    log = logger or logging.getLogger(__name__)

    if not active:
        log.info(
            "chat_formatting_skipped",
            extra={"enabled": False, "original_length": len(answer or "")},
        )
        return answer

    try:
        formatted = formatter(answer)
        log.info(
            "chat_formatting_applied",
            extra={
                "enabled": True,
                "original_length": len(answer or ""),
                "formatted_length": len(formatted or ""),
            },
        )
        return formatted
    except Exception:
        log.exception(
            "chat_formatting_failed",
            extra={"enabled": True, "original_length": len(answer or "")},
        )
        return answer
