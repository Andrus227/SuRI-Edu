from suri_edu.robix_language import MovePoseCommand, MoveToCommand, parse_command, parse_program
from suri_edu.routine_examples import ROUTINE_EXAMPLES, get_routine_example


def test_exemplos_possuem_chaves_unicas_e_cobrem_rotinas_basicas():
    keys = [example.key for example in ROUTINE_EXAMPLES]

    assert len(keys) == len(set(keys))
    assert set(keys) == {
        "posicao_neutra",
        "abrir_garra",
        "fechar_garra",
        "ciclo_garra",
        "teste_juntas",
        "varredura_base",
        "espaco_trabalho",
        "percurso_tres_pontos",
        "aceno_robix",
        "inspecionar_objeto",
        "coreografia",
        "pick_and_place",
    }


def test_exemplos_sao_programas_finitos_com_comandos_validos():
    for example in ROUTINE_EXAMPLES:
        program = parse_program(example.code)
        commands = [*program.setup]
        for method_commands in program.methods.values():
            commands.extend(method_commands)

        assert program.loop == []
        assert commands
        for command in commands:
            assert command in program.methods or parse_command(command) is not None

        assert example.method_name in program.methods
        assert example.method_code.startswith(f"metodo {example.method_name}:\n")


def test_busca_de_exemplo_por_chave():
    assert get_routine_example("abrir_garra").title == "Abrir garra"
    assert get_routine_example("inexistente") is None


def test_aceno_delega_suavizacao_ao_firmware_sem_passos_intermediarios():
    example = get_routine_example("aceno_robix")
    program = parse_program(example.code)
    commands = [parse_command(source) for source in program.methods[example.method_name]]

    assert MovePoseCommand((90, 80, 50, 70, 60, 90)) in commands
    assert MoveToCommand(5, 120) in commands
    assert MoveToCommand(3, 60) not in commands
