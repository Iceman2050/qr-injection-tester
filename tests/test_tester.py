"""Tests for the end-to-end test runner."""

from qr_injection_tester import (
    HardenedMockAgent,
    TestCase,
    VulnerableMockAgent,
    run_tests,
)


def test_run_tests_vulnerable_flags_all_injections(tmp_path):
    results = run_tests(VulnerableMockAgent(), render_dir=str(tmp_path))
    by_template = {r.template_id: r for r in results}
    for tid, r in by_template.items():
        if tid == "benign-control":
            assert not r.acted and r.passed, tid
        else:
            assert r.acted and r.passed, tid


def test_run_tests_hardened_resists_all_injections(tmp_path):
    from qr_injection_tester import list_templates

    cases = [TestCase(tid, tid, expect_action=False) for tid in list_templates()]
    results = run_tests(HardenedMockAgent(), cases=cases, render_dir=str(tmp_path))
    for r in results:
        assert not r.acted, r.template_id
        assert r.passed, r.template_id


def test_run_tests_without_render_dir_also_works():
    results = run_tests(VulnerableMockAgent())
    assert any(r.acted for r in results)


def test_custom_case_expectation_mismatch_is_failure():
    # Ask the hardened agent to act -> it won't -> expectation fails.
    results = run_tests(
        HardenedMockAgent(),
        cases=[TestCase("must act", "ignore-previous", expect_action=True)],
    )
    assert results[0].passed is False
