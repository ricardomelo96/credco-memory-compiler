from flush import FLUSH_INSTRUCTIONS


def test_instructions_are_portuguese():
    assert "Contexto" in FLUSH_INSTRUCTIONS
    assert "Decisões" in FLUSH_INSTRUCTIONS
    assert "Lições" in FLUSH_INSTRUCTIONS


def test_instructions_ask_for_domain_tag():
    assert "tecnico" in FLUSH_INSTRUCTIONS
    assert "operacional" in FLUSH_INSTRUCTIONS


def test_preserves_flush_ok_sentinel():
    assert "FLUSH_OK" in FLUSH_INSTRUCTIONS
