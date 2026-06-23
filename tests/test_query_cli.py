import pytest
from query import build_parser


def test_dominio_defaults_to_none():
    args = build_parser().parse_args(["minha pergunta"])
    assert args.dominio is None


def test_dominio_accepts_tecnico():
    args = build_parser().parse_args(["minha pergunta", "--dominio", "tecnico"])
    assert args.dominio == "tecnico"


def test_dominio_accepts_operacional():
    args = build_parser().parse_args(["q", "--dominio", "operacional"])
    assert args.dominio == "operacional"


def test_dominio_rejects_invalid_choice():
    with pytest.raises(SystemExit):
        build_parser().parse_args(["q", "--dominio", "misto"])
