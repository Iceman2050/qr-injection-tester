"""Tests for payload generation and QR rendering."""

import json
import os

import pytest

from qr_injection_tester import generate_payload, list_templates, render_qr


def test_list_templates_non_empty():
    templates = list_templates()
    assert "ignore-previous" in templates
    assert "benign-control" in templates


def test_generate_payload_contains_canary():
    item = generate_payload("ignore-previous", canary="ABC123")
    assert "ABC123" in item["payload"]
    assert item["canary"] == "ABC123"
    assert item["template_id"] == "ignore-previous"
    assert item["expected_instruction"] is not None


def test_generate_payload_unknown_template_raises():
    with pytest.raises(ValueError):
        generate_payload("no-such-template")


def test_render_qr_writes_png_and_sidecar(tmp_path):
    item = generate_payload("fake-support-url", canary="XYZ999")
    out = str(tmp_path / "test.png")
    path = render_qr(item["payload"], out)
    assert os.path.isfile(path)
    assert os.path.getsize(path) > 0
    sidecar = path + ".qrmeta.json"
    assert os.path.isfile(sidecar)
    with open(sidecar, encoding="utf-8") as fh:
        meta = json.load(fh)
    assert meta["payload"] == item["payload"]


def test_qr_file_is_valid_png(tmp_path):
    from PIL import Image

    item = generate_payload("benign-control", canary="CTRL1")
    path = render_qr(item["payload"], str(tmp_path / "ctrl.png"))
    with Image.open(path) as img:
        img.verify()  # raises if not a valid image
