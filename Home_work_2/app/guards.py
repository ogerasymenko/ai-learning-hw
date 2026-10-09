"""Safety/cost guards, modeled after the lesson demo's guards.mjs."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

SECRETS = [
    (re.compile(r"sk-ant-[A-Za-z0-9_-]{8,}"), "[REDACTED:anthropic-key]"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "[REDACTED:github-token]"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "[REDACTED:aws-key]"),
    (re.compile(r"xox[abprs]-[A-Za-z0-9-]{10,}"), "[REDACTED:slack-token]"),
    (re.compile(r"eyJ[\w-]{10,}\.[\w-]{10,}\.[\w-]{10,}"), "[REDACTED:jwt]"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"), "[REDACTED:private-key]"),
    (re.compile(r"\b([A-Z0-9_]*(?:password|passwd|secret|token|api[_-]?key)[A-Z0-9_]*)(\s*[=:]\s*)[\"']?(?!\[REDACTED)[^\s\"']{4,}", re.I), r"\1\2[REDACTED]"),
]


def redact(text: str) -> tuple[str, int]:
    hits = 0
    for rx, replacement in SECRETS:
        text, n = rx.subn(replacement, text)
        hits += n
    return text, hits


def cap(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return f"{text[:max_chars]}\n[truncated: showed {max_chars} of {len(text)} chars — ask a narrower question]", True


def firewall(text: str, max_chars: int) -> tuple[str, int, bool]:
    clean, redactions = redact(text)
    clean, truncated = cap(clean, max_chars)
    return clean, redactions, truncated


class Guard:
    def __init__(self, *, allowed_tools: set[str], max_tool_calls: int, max_repeats: int,
                 max_tool_chars: int, context_budget_chars: int, log_dir: Path):
        self.allowed_tools = allowed_tools
        self.max_tool_calls = max_tool_calls
        self.max_repeats = max_repeats
        self.max_tool_chars = max_tool_chars
        self.context_budget_chars = context_budget_chars
        self.calls = 0
        self.context_chars = 0
        self.redactions = 0
        self.truncated = 0
        self.denied: list[str] = []
        self.seen: dict[str, int] = {}
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).isoformat().replace(":", "-").replace("+00:00", "Z")
        self.log_file = log_dir / f"run-{stamp}.jsonl"

    def _audit(self, entry: dict) -> None:
        record = {"t": datetime.now(timezone.utc).isoformat(), **entry}
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def before_tool(self, name: str, args: dict) -> tuple[bool, str]:
        if name not in self.allowed_tools:
            reason = "This agent may only use its own Terraform read-only tools."
            self.denied.append(f"{name}: {reason}")
            self._audit({"event": "denied", "tool": name, "reason": reason})
            return False, reason
        if self.calls >= self.max_tool_calls:
            reason = f"Tool-call budget of {self.max_tool_calls} is spent."
            self.denied.append(f"{name}: {reason}")
            self._audit({"event": "denied", "tool": name, "reason": reason})
            return False, reason

        key = f"{name} {json.dumps(args, sort_keys=True)}"
        count = self.seen.get(key, 0) + 1
        self.seen[key] = count
        if count > self.max_repeats:
            reason = f"You already made this exact call {self.max_repeats} times."
            self.denied.append(f"{name}: {reason}")
            self._audit({"event": "denied", "tool": name, "reason": reason})
            return False, reason
        if self.context_chars >= self.context_budget_chars:
            reason = f"Context budget of {self.context_budget_chars} chars is spent."
            self.denied.append(f"{name}: {reason}")
            self._audit({"event": "denied", "tool": name, "reason": reason})
            return False, reason

        self.calls += 1
        return True, ""

    def after_tool(self, name: str, args: dict, raw: str) -> str:
        clean, redactions, truncated = firewall(raw, self.max_tool_chars)
        self.context_chars += len(clean)
        self.redactions += redactions
        self.truncated += int(truncated)
        self._audit({
            "event": "tool", "tool": name, "args": args,
            "charsIn": len(raw), "charsOut": len(clean),
            "redactions": redactions, "truncated": truncated,
        })
        return clean
