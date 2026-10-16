"""Tests for the mock vision agents (vulnerable vs hardened behavior)."""

from qr_injection_tester import HardenedMockAgent, VulnerableMockAgent, generate_payload


def test_vulnerable_agent_acts_on_injection():
    agent = VulnerableMockAgent()
    item = generate_payload("ignore-previous")
    out = agent.handle("translate this document", qr_ref=item)
    assert agent.actions_log, "vulnerable agent should record an action"
    assert item["canary"] in agent.actions_log[0]
    assert "ACTED" in out


def test_hardened_agent_ignores_injection():
    agent = HardenedMockAgent()
    item = generate_payload("ignore-previous")
    out = agent.handle("translate this document", qr_ref=item)
    assert agent.actions_log == [], "hardened agent must not act on scanned instructions"
    assert "quarantined" in out


def test_hardened_agent_ignores_all_injection_templates():
    from qr_injection_tester import list_templates

    for tid in list_templates():
        agent = HardenedMockAgent()
        item = generate_payload(tid)
        agent.handle("summarize", qr_ref=item)
        assert agent.actions_log == [], f"hardened agent acted on template {tid}"


def test_vulnerable_agent_acts_on_all_malicious_templates():
    from qr_injection_tester import list_templates

    for tid in list_templates():
        agent = VulnerableMockAgent()
        item = generate_payload(tid)
        agent.handle("summarize", qr_ref=item)
        if tid == "benign-control":
            assert agent.actions_log == []
        else:
            assert agent.actions_log, f"vulnerable agent ignored template {tid}"


def test_hardened_agent_still_completes_benign_task():
    agent = HardenedMockAgent()
    out = agent.handle("summarize this document")
    assert out == "Task done: summarize this document"
    assert agent.actions_log == []


def test_scan_accepts_payload_string(tmp_path):
    agent = HardenedMockAgent()
    assert agent.scan("just some qr text") == "just some qr text"
