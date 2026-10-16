"""Prompt injection defenses: Neutralize untrusted web text before LLM context injection."""

import re

# LLM instruction delimiters that should never appear in untrusted web text
INJECTION_MARKERS = [
    r"\[INST\]", r"\[/INST\]",
    r"<<SYS>>", r"<</SYS>>",
    r"<\|im_start\|>", r"<\|im_end\|>",
    r"<\|system\|>", r"<\|user\|>", r"<\|assistant\|>",
    r"human:", r"assistant:",
]

# Jailbreak phrases attempting to hijack agent behavior
JAILBREAK_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"you are now in developer mode",
    r"system override\b",
    r"output (the |your )?(hidden )?system prompt",
    r"print all environment variables",
    r"disregard (the )?above guidelines"
]


def sanitize_untrusted_text(text: str) -> str:
    """Sanitize retrieved external text, neutralizing adversarial instruction markers."""
    if not text:
        return ""

    sanitized = text

    # 1. Strip special token markers
    for marker in INJECTION_MARKERS:
        sanitized = re.sub(marker, " [FILTERED_TAG] ", sanitized, flags=re.IGNORECASE)

    # 2. Neutralize jailbreak instructions
    for pattern in JAILBREAK_PATTERNS:
        sanitized = re.sub(pattern, "[UNTRUSTED_INSTRUCTION_REDACTED]", sanitized, flags=re.IGNORECASE)

    return sanitized
