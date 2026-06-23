from compile import COMPILE_INSTRUCTIONS


def test_instructions_are_portuguese():
    assert "conceito" in COMPILE_INSTRUCTIONS.lower()
    assert "artigo" in COMPILE_INSTRUCTIONS.lower()


def test_instructs_to_fill_dominio_field():
    assert "dominio" in COMPILE_INSTRUCTIONS.lower()


def test_instructs_misto_to_connections():
    assert "misto" in COMPILE_INSTRUCTIONS.lower()
    assert "connections" in COMPILE_INSTRUCTIONS.lower()


def test_index_row_includes_dominio_column():
    assert "dominio" in COMPILE_INSTRUCTIONS.lower()
