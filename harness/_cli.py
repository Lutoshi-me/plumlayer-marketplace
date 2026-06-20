"""
_cli.py — shared helper: invoke the `claude` CLI and parse stream-json events.

Grounding role: thin wrapper around subprocess + JSONL parsing. No inference.
"""

import json
import subprocess
from pathlib import Path
from typing import Iterator


def invoke_headless(
    plugin_dir: Path,
    prompt: str,
    output_path: Path,
    timeout_sec: int = 120,
) -> list[dict]:
    """
    Run claude --bare --plugin-dir <plugin_dir> -p <prompt> --output-format stream-json --verbose.

    Captures stdout to output_path (JSONL) and returns the parsed event list.
    Raises subprocess.TimeoutExpired if the process exceeds timeout_sec.
    Raises RuntimeError if `claude` is not found on PATH.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "claude",
        "--bare",
        "--plugin-dir", str(plugin_dir),
        "-p", prompt,
        "--output-format", "stream-json",
        "--verbose",
    ]

    with open(output_path, "w", encoding="utf-8") as fh:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # merge stderr into stdout for capture
            timeout=timeout_sec,
            encoding="utf-8",
        )
        fh.write(result.stdout)

    return _parse_jsonl(output_path)


def _parse_jsonl(path: Path) -> list[dict]:
    """Parse a JSONL file; skip blank lines and non-JSON lines gracefully."""
    events = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass  # non-JSON line (rare; captured stderr text)
    return events


def find_init_event(events: list[dict]) -> dict | None:
    """Return the first system/init event from the event stream, or None."""
    for ev in events:
        if ev.get("type") == "system" and ev.get("subtype") == "init":
            return ev
    return None
