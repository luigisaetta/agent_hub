from __future__ import annotations

from types import SimpleNamespace


class _Event:
    def __init__(self, event_type: str, delta: str = ""):
        self.type = event_type
        self.delta = delta


def test_print_streamed_output_collects_only_text_deltas(reload_module, capsys):
    utils = reload_module("examples.utils")

    stream = [
        _Event("response.output_text.delta", "Hel"),
        _Event("response.reasoning.delta", "ignored"),
        _Event("response.output_text.delta", "lo"),
    ]

    result = utils.print_streamed_output(stream)
    captured = capsys.readouterr()

    assert result == "Hello"
    assert captured.out == "Hello"


def test_get_client_production_uses_openai_with_expected_kwargs(reload_module):
    utils = reload_module("examples.utils")

    client = utils.get_client(region="eu-frankfurt-1", is_preproduction=False)

    assert client.kwargs["base_url"] == utils.BASE_URL
    assert client.kwargs["api_key"] == utils.KEY1
    assert client.kwargs["project"] == utils.PROJECT_ID


def test_get_client_preproduction_uses_oci_client_with_ppe_url(reload_module):
    utils = reload_module("examples.utils")

    client = utils.get_client(region="eu-frankfurt-1", is_preproduction=True)

    assert "ppe.generativeai.eu-frankfurt-1.oci.oraclecloud.com" in client.kwargs["base_url"]
    assert client.kwargs["compartment_id"] == utils.COMPARTMENT_ID
    assert client.kwargs["auth"].__class__.__name__ == "FakeOciUserPrincipalAuth"


def test_print_header_outputs_consistent_banner(reload_module, capsys):
    utils = reload_module("examples.utils")

    utils.print_header("files", "project")
    captured = capsys.readouterr()

    assert "List of the files in the project" in captured.out
    assert captured.out.count("=") >= 40
