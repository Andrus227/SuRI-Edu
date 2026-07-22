from unittest.mock import Mock, call

import pytest

from suri_edu.robix_language import (
    MovePoseCommand,
    MoveToCommand,
    WaitCommand,
    generate_routine,
    parse_command,
    parse_program,
)


def test_parse_program_preserva_gramatica_permissiva():
    on_method = Mock()
    source = """
metodo Acao:
    MoveTo(1, 20);
setup:
    Acao // comentário
loop:
    Wait(10)
MoveTo(2, 30)
"""

    program = parse_program(source, on_method=on_method)

    assert program.methods == {"Acao": ["MoveTo(1, 20)"]}
    assert program.setup == ["Acao", "MoveTo(2, 30)"]
    assert program.loop == ["Wait(10)"]
    assert on_method.call_args_list == [call("Acao")]


def test_parse_program_metodo_duplicado_substitui_corpo_anterior():
    program = parse_program("metodo A:\n    Wait(1)\nmetodo A:\n    Wait(2)")

    assert program.methods == {"A": ["Wait(2)"]}


def test_generate_routine_usa_nome_padrao_e_formato_legado():
    code = generate_routine("  ", ["MovePose(1, 2, 3, 4, 5, 6)\n"])

    assert code == (
        "metodo RotinaGravada:\n"
        "    // Ponto 1\n"
        "    MovePose(1, 2, 3, 4, 5, 6)\n"
        "    Wait(1000)\n"
        "\nsetup:\n"
        "    // Posição inicial\n"
        "    MovePose(1, 2, 3, 4, 5, 6)\n"
        "\nloop:\n"
        "    // Execução contínua\n"
        "    RotinaGravada\n"
    )


def test_generate_routine_rejeita_nome_que_o_parser_nao_reconhece():
    with pytest.raises(ValueError, match="apenas letras"):
        generate_routine("Minha Rotina", ["MovePose(1, 2, 3, 4, 5, 6)\n"])


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("prefixo moveto(1, 180) sufixo", MoveToCommand(1, 180)),
        (
            "MovePose(0, 1, 2, 3, 4, 5)",
            MovePoseCommand((0, 1, 2, 3, 4, 5)),
        ),
        ("WAIT ( 25 )", WaitCommand(25)),
        ("desconhecido", None),
    ],
)
def test_parse_command_preserva_reconhecimento_legado(source, expected):
    assert parse_command(source) == expected
