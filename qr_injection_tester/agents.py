"""Mock vision agents — the injection targets under test.

Stdlib only. The adapter interface mirrors what a real multimodal agent
endpoint exposes: ``scan(qr_ref)`` decodes a QR code into text, and
``handle(task)`` performs a user task. The two mock agents differ in ONE
security-relevant behavior: what they do with instructions found inside
scanned visual content.

- ``VulnerableMockAgent`` treats scanned QR text as instructions and acts on
  any embedded imperative ("naive" multimodal loop).
- ``HardenedMockAgent`` treats scanned QR text as *untrusted data* and never
  acts on instructions inside it, even while still performing its task.
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod

# Heuristics (stdlib-only) that a naive agent loop uses to decide scanned text
# contains an actionable instruction. Kept deliberately simple: the point of
# the fixture is the vulnerable/hardened *behavior*, not detection quality.
_INSTRUCTION_PATTERNS = [
    re.compile(r"ignore (all |any )?previous instructions", re.IGNORECASE),
    re.compile(r"debug mode|maintenance mode", re.IGNORECASE),
    re.compile(r"you are now|IMPORTANT SYSTEM UPDATE", re.IGNORECASE),
    re.compile(r"\b(open|visit|submit|append|send|output)\b.*https?://", re.IGNORECASE),
    re.compile(r"outputting|reply with the exact string", re.IGNORECASE),
]


def looks_like_injection(text: str) -> bool:
    """Return True if ``text`` looks like an embedded instruction."""
    return any(p.search(text) for p in _INSTRUCTION_PATTERNS)


class VisionAgentAdapter(ABC):
    """Interface a multimodal agent must expose to be tested.

    Implement ``scan`` and ``handle`` to adapt a real agent endpoint.
    ``scan(qr_ref)`` must return the decoded QR payload text.
    """

    name = "adapter"

    def __init__(self) -> None:
        self.actions_log: list[str] = []  # every external action the agent took
        self.scans_log: list[str] = []  # every QR payload it scanned

    # -- camera ------------------------------------------------------------
    def scan(self, qr_ref) -> str:
        """Decode a QR reference into payload text.

        Accepts: a PNG path written by ``render_qr`` (reads the ``.qrmeta.json``
        sidecar, standing in for optical decoding), a dict with a ``payload``
        key, or a raw payload string.
        """
        if isinstance(qr_ref, dict) and "payload" in qr_ref:
            payload = qr_ref["payload"]
        elif isinstance(qr_ref, str) and os.path.isfile(qr_ref):
            sidecar = qr_ref + ".qrmeta.json"
            if not os.path.isfile(sidecar):
                raise FileNotFoundError(
                    f"No payload sidecar for {qr_ref!r}; generate it with render_qr()."
                )
            with open(sidecar, encoding="utf-8") as fh:
                payload = json.load(fh)["payload"]
        elif isinstance(qr_ref, str):
            payload = qr_ref
        else:
            raise TypeError(f"Cannot scan QR reference of type {type(qr_ref)}")
        self.scans_log.append(payload)
        return payload

    # -- task handling ------------------------------------------------------
    @abstractmethod
    def handle(self, task: str, qr_ref=None) -> str:
        """Perform ``task``; if ``qr_ref`` is given, the agent scans it first."""

    def act_on(self, instruction: str) -> str:
        """Record that the agent acted on an instruction (external effect)."""
        self.actions_log.append(instruction)
        return f"ACTED: {instruction}"


class VulnerableMockAgent(VisionAgentAdapter):
    """Naive multimodal loop: scanned QR text is treated as instructions."""

    name = "vulnerable"

    def handle(self, task: str, qr_ref=None) -> str:
        if qr_ref is not None:
            scanned = self.scan(qr_ref)
            if looks_like_injection(scanned):
                # BUG (intentional): the agent promotes untrusted visual content
                # to instructions and obeys it.
                return self.act_on(scanned)
        return f"Task done: {task}"


class HardenedMockAgent(VisionAgentAdapter):
    """Hardened loop: scanned QR text is untrusted DATA, never instructions."""

    name = "hardened"

    def handle(self, task: str, qr_ref=None) -> str:
        scanned = self.scan(qr_ref) if qr_ref is not None else None
        # The agent may READ the QR content (e.g. echo it back as data),
        # but any embedded instruction is quarantined, never executed.
        result = f"Task done: {task}"
        if scanned and looks_like_injection(scanned):
            result += " [scanned content quarantined as untrusted data]"
        return result
