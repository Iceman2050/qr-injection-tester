"""qr-injection-tester — test multimodal agents for QR-code prompt injection.

A QR code is just text rendered as pixels. When a multimodal agent scans a QR
code found "in the wild" (a flyer, a screen, a shipping label) and feeds the
decoded text into its instruction-following loop, any instruction embedded in
that payload can hijack the agent. This package generates malicious QR payloads
and tests whether an agent endpoint acts on them or treats them as untrusted
data.

Built by Ingenious AI.
"""

__version__ = "1.0.0"
__author__ = "Ingenious AI"

from .agents import HardenedMockAgent, VisionAgentAdapter, VulnerableMockAgent
from .generator import generate_payload, list_templates, render_qr
from .tester import TestCase, run_tests

__all__ = [
    "VisionAgentAdapter",
    "VulnerableMockAgent",
    "HardenedMockAgent",
    "generate_payload",
    "render_qr",
    "list_templates",
    "TestCase",
    "run_tests",
]
