from types import SimpleNamespace
from unittest.mock import Mock, call

import pytest

from suri_edu import app as app_module
from suri_edu.routine_examples import ROUTINE_EXAMPLES


def test_conectar_arduino_atualiza_lista_sem_conectar(supervisor):
    supervisor.atualizar_lista_portas = Mock()

    supervisor.conectar_arduino("🔄 Atualizar...")

    supervisor.atualizar_lista_portas.assert_called_once_with()
    supervisor.porta_serial.conectar.assert_not_called()


@pytest.mark.parametrize("success", [True, False])
def test_conectar_arduino_registra_resultado(supervisor, success):
    supervisor.porta_serial.conectar.return_value = success, "resultado"

    supervisor.conectar_arduino("COM5")

    supervisor.escrever_log.assert_called_once_with("resultado", not success)


def test_atualizar_lista_portas_configura_todos_os_combos(supervisor):
    supervisor.porta_serial.listar_portas.return_value = ["COM1"]
    supervisor.lista_combos_portas = [Mock(), Mock()]

    supervisor.atualizar_lista_portas()

    for combo in supervisor.lista_combos_portas:
        combo.configure.assert_called_once_with(values=["COM1", "🔄 Atualizar..."])


@pytest.mark.parametrize("motor,angle", [(0, 90), (7, 90), (1, -1), (6, 181)])
def test_enviar_serial_rejeita_limites_invalidos(supervisor, motor, angle):
    supervisor.enviar_serial(motor, angle)

    supervisor.porta_serial.enviar.assert_not_called()
    supervisor.escrever_log.assert_called_once_with(
        f"Limites excedidos: Motor {motor}, Ângulo {angle}°!", True
    )


def test_enviar_serial_registra_pacote_quando_monitor_ativo(supervisor):
    supervisor.porta_serial.enviar.return_value = True

    supervisor.enviar_serial(6, 180)

    supervisor.porta_serial.enviar.assert_called_once_with("<6,180>")
    supervisor.escrever_log.assert_called_once_with("📡 [TX] <6,180>")


def test_enviar_serial_nao_registra_pacote_quando_monitor_inativo(supervisor):
    supervisor.porta_serial.enviar.return_value = True
    supervisor.var_debug_serial.value = False

    supervisor.enviar_serial(1, 0)

    supervisor.escrever_log.assert_not_called()


def test_enviar_serial_registra_falha(supervisor):
    supervisor.porta_serial.enviar.return_value = False

    supervisor.enviar_serial(1, 90)

    supervisor.escrever_log.assert_called_once_with("Erro de comunicação Serial!", True)


def test_processamento_agenda_etapas_sem_update_reentrante(supervisor):
    supervisor.processar_codigo("setup:\n    Wait(50)")

    supervisor.after.assert_called_once()
    assert supervisor.after.call_args.args[0] == 0
    supervisor.update.assert_not_called()


def test_parar_execucao_agora_altera_estado_e_registra(supervisor):
    supervisor.parar_execucao_agora()

    assert supervisor.parar_execucao is True
    supervisor.porta_serial.enviar_parada.assert_called_once_with(1)
    assert supervisor.controle_motores.snapshot.stop_state == "command_sent"
    supervisor.escrever_log.assert_called_once_with(
        "🛑 Parada solicitada — aguardando confirmação do controlador.", True
    )


def test_espaco_para_rotina_globalmente_e_consumido(supervisor):
    supervisor.rotina_em_execucao = True
    supervisor.solicitar_parada_imediata = Mock()

    assert supervisor.acao_espaco_emergencia(SimpleNamespace(widget=object())) == "break"
    supervisor.solicitar_parada_imediata.assert_called_once_with()


def test_espaco_sem_rotina_preserva_comportamento_do_controle_em_foco(supervisor):
    supervisor.solicitar_parada_imediata = Mock()

    assert supervisor.acao_espaco_emergencia(SimpleNamespace(widget=object())) is None
    supervisor.solicitar_parada_imediata.assert_not_called()


def test_botao_e_atalho_delegam_a_mesma_operacao_central(supervisor):
    supervisor.rotina_em_execucao = True
    supervisor.solicitar_parada_imediata = Mock()

    supervisor.parar_execucao_agora()
    supervisor.acao_espaco_emergencia(None)

    assert supervisor.solicitar_parada_imediata.call_count == 2


def test_parada_e_idempotente_contra_repeticao_automatica(supervisor):
    supervisor.rotina_em_execucao = True

    supervisor.solicitar_parada_imediata()
    supervisor.solicitar_parada_imediata()

    supervisor.porta_serial.enviar_parada.assert_called_once_with(1)


def test_parada_cancela_callback_fila_e_invalida_execucao_antiga(supervisor):
    supervisor.processar_codigo("setup:\n    MoveTo(1, 20)\n    MoveTo(2, 30)")
    callback_antigo = supervisor.after.call_args.args[1]

    supervisor.solicitar_parada_imediata()
    callback_antigo()

    supervisor.after_cancel.assert_called_with("after-id")
    assert not supervisor._fila_execucao
    supervisor.porta_serial.enviar.assert_not_called()
    assert supervisor.controle_motores.snapshot.routine_state == "cancelled"


def test_movepose_de_rotina_envia_um_motor_por_callback_e_para_os_restantes(supervisor):
    supervisor.processar_codigo("setup:\n    MovePose(1, 2, 3, 4, 5, 6)")
    iniciar_comando = supervisor.after.call_args.args[1]
    iniciar_comando()
    enviar_primeiro_motor = supervisor.after.call_args.args[1]
    enviar_primeiro_motor()
    callback_antigo = supervisor.after.call_args.args[1]

    supervisor.solicitar_parada_imediata()
    callback_antigo()

    supervisor.porta_serial.enviar.assert_called_once_with("<1,1>")


def test_ack_antigo_nao_altera_estado_de_nova_execucao(supervisor):
    supervisor.rotina_em_execucao = True
    supervisor.solicitar_parada_imediata()
    callback_ack_antigo = supervisor.after.call_args.args[1]
    supervisor.processar_codigo("setup:\n    Wait(1)")
    supervisor.porta_serial.receber_respostas.return_value = ["<ACK,STOP,1>"]

    callback_ack_antigo()

    assert supervisor.controle_motores.snapshot.stop_state == "idle"
    assert not any(
        "confirmou o processamento" in chamada.args[0]
        for chamada in supervisor.escrever_log.call_args_list
    )


def test_parada_registra_falha_de_transmissao(supervisor):
    supervisor.porta_serial.enviar_parada.return_value = False

    supervisor.solicitar_parada_imediata()

    assert supervisor.controle_motores.snapshot.stop_state == "send_failed"
    supervisor.after.assert_not_called()
    supervisor.escrever_log.assert_called_once_with(
        "🛑 Rotina cancelada; falha ao enviar a parada ao controlador.", True
    )


def test_parada_permite_nova_tentativa_apos_falha(supervisor):
    supervisor.porta_serial.enviar_parada.side_effect = [False, True]

    supervisor.solicitar_parada_imediata()
    supervisor.solicitar_parada_imediata()

    assert supervisor.porta_serial.enviar_parada.call_args_list == [call(1), call(2)]
    assert supervisor.controle_motores.snapshot.stop_state == "command_sent"


def test_id_de_parada_reinicia_apos_limite(supervisor):
    supervisor._parada_geracao = app_module.MAX_STOP_ID

    supervisor.solicitar_parada_imediata()

    supervisor.porta_serial.enviar_parada.assert_called_once_with(1)


def test_ack_confirma_interrupcao_no_controlador(supervisor):
    supervisor.solicitar_parada_imediata()
    supervisor.porta_serial.receber_respostas.return_value = ["<ACK,STOP,1>"]

    supervisor._verificar_ack_parada()

    assert supervisor.controle_motores.snapshot.stop_state == "controller_interrupted"
    supervisor.escrever_log.assert_called_with("✅ Controlador confirmou o processamento do STOP.")


def test_ack_de_outra_parada_nao_confirma_stop_atual(supervisor):
    supervisor.solicitar_parada_imediata()
    supervisor.porta_serial.receber_respostas.return_value = ["<ACK,STOP,999>"]

    supervisor._verificar_ack_parada(1)

    assert supervisor.controle_motores.snapshot.stop_state == "command_sent"
    assert call("✅ Controlador confirmou o processamento do STOP.") not in (
        supervisor.escrever_log.call_args_list
    )


def test_timeout_de_ack_nao_e_apresentado_como_confirmacao(monkeypatch, supervisor):
    supervisor._limite_ack = 10.0
    supervisor._parada_solicitada = True
    supervisor._parada_geracao = 1
    monkeypatch.setattr(app_module.time, "monotonic", lambda: 10.0)

    supervisor._verificar_ack_parada()

    assert supervisor.controle_motores.snapshot.stop_state == "no_confirmation"
    supervisor.escrever_log.assert_called_once_with(
        "⚠️ Parada enviada, mas sem confirmação do controlador.", True
    )


def test_parada_permite_nova_tentativa_apos_timeout(monkeypatch, supervisor):
    supervisor.solicitar_parada_imediata()
    supervisor._limite_ack = 10.0
    monkeypatch.setattr(app_module.time, "monotonic", lambda: 10.0)
    supervisor._verificar_ack_parada(1)

    supervisor.solicitar_parada_imediata()

    assert supervisor.porta_serial.enviar_parada.call_args_list == [call(1), call(2)]


def test_processar_codigo_registra_metodos_e_executa_setup(supervisor):
    supervisor.executar_comando = Mock(return_value=0)
    code = """
metodo Pegar:
    MoveTo(1, 10);
    // ignorado
setup:
    Pegar
MoveTo(2, 20) // raiz
"""

    supervisor.processar_codigo(code)

    assert supervisor.metodos_salvos == {"Pegar": ["MoveTo(1, 10)"]}
    first_step = supervisor.after.call_args.args[1]
    first_step()
    second_step = supervisor.after.call_args.args[1]
    second_step()
    last_step = supervisor.after.call_args.args[1]
    last_step()
    assert supervisor.executar_comando.call_args_list == [
        call("MoveTo(1, 10)", geracao=1),
        call("MoveTo(2, 20)", geracao=1),
    ]
    supervisor.escrever_log.assert_any_call("📦 Método 'Pegar' registrado.")
    supervisor.escrever_log.assert_any_call("🏁 Fim da execução.")


def test_processar_codigo_repete_loop_ate_parada(supervisor):
    def stop_on_third(command, **kwargs):
        if supervisor.executar_comando.call_count == 3:
            supervisor.parar_execucao = True
        return 1

    supervisor.executar_comando = Mock(side_effect=stop_on_third)

    supervisor.processar_codigo("loop:\n    Wait(1)\n    MoveTo(1, 90)")

    for _ in range(3):
        supervisor.after.call_args.args[1]()

    assert supervisor.executar_comando.call_args_list == [
        call("Wait(1)", geracao=1),
        call("MoveTo(1, 90)", geracao=1),
        call("Wait(1)", geracao=1),
    ]


def test_executar_metodo_aninhado(supervisor):
    supervisor.metodos_salvos = {"A": ["B"], "B": ["Wait(5)"]}

    assert supervisor._expandir_comandos(["A"]) == ["Wait(5)"]


def test_executar_comando_detecta_recursao(supervisor):
    supervisor.processar_codigo("metodo Repetir:\n    Repetir\nsetup:\n    Repetir")

    assert supervisor.parar_execucao is True
    supervisor.escrever_log.assert_any_call(
        "Recursão detectada no método 'Repetir'. Execução abortada.", True
    )


def test_executar_moveto_envia_atualiza_e_aguarda(supervisor):
    supervisor.sliders[0].value = 80

    delay = supervisor.executar_comando("prefixo MoveTo(1, 100) sufixo")

    supervisor.porta_serial.enviar.assert_called_once_with("<1,100>")
    assert supervisor.sliders[0].value == 100
    assert delay == 3067


@pytest.mark.parametrize(
    ("difference", "expected"),
    [(0, 0), (10, 400), (180, 2967)],
)
def test_estimativa_de_movimento_considera_aceleracao_e_frenagem(difference, expected):
    assert app_module.RobixSupervisorio._estimar_tempo_movimento(difference) == expected


def test_executar_moveto_motor_acima_do_limite_e_rejeitado(supervisor):
    assert supervisor.executar_comando("MoveTo(7, 90)") == 0
    supervisor.porta_serial.enviar.assert_not_called()
    supervisor.escrever_log.assert_called_once_with("Motor inválido: 7.", True)


def test_executar_moveto_rejeita_angulo_fora_do_limite(supervisor):
    assert supervisor.executar_comando("MoveTo(1, 181)") == 0
    supervisor.porta_serial.enviar.assert_not_called()
    supervisor.escrever_log.assert_called_once_with("Ângulo inválido para o motor 1: 181.", True)


def test_executar_movepose_inicial_envia_todos_e_usa_maior_diferenca(supervisor):
    delay = supervisor.executar_comando("MovePose(0, 30, 60, 90, 120, 180)")

    assert supervisor.porta_serial.enviar.call_args_list == [
        call("<1,0>"),
        call("<2,30>"),
        call("<3,60>"),
        call("<4,90>"),
        call("<5,120>"),
        call("<6,180>"),
    ]
    assert [slider.value for slider in supervisor.sliders] == [0, 30, 60, 90, 120, 180]
    assert delay == 3167


def test_executar_wait_e_comando_desconhecido(supervisor):
    assert supervisor.executar_comando("Wait(25)") == 25
    supervisor.executar_comando("Invalido")

    supervisor.escrever_log.assert_called_once_with("Sintaxe não reconhecida: 'Invalido'", True)


def test_controles_de_slider_respeitam_tempo_real(monkeypatch, supervisor):
    supervisor.var_tempo_real.value = True
    times = iter([1.0, 1.0])
    monkeypatch.setattr(app_module.time, "time", lambda: next(times))

    supervisor.mover_s(0, 45.9)
    supervisor.final_s(0)

    assert supervisor.labels[0].configurations == [{"text": "45°"}]
    assert supervisor.porta_serial.enviar.call_args_list == [call("<1,45>"), call("<1,90>")]
    assert supervisor.tempos_motores[0] == 1.0


def test_final_slider_nao_envia_no_modo_offline(supervisor):
    supervisor.final_s(0)

    supervisor.porta_serial.enviar.assert_not_called()


def test_incrementar_slider_limita_angulo(supervisor):
    supervisor.sliders[0].value = 175
    supervisor.mover_s = Mock()
    supervisor.final_s = Mock()

    supervisor.inc_s(0, 10)

    assert supervisor.sliders[0].value == 180
    supervisor.mover_s.assert_called_once_with(0, 180)
    supervisor.final_s.assert_called_once_with(0)


def test_enviar_pose_offline_envia_seis_motores(supervisor):
    for index, slider in enumerate(supervisor.sliders):
        slider.value = index * 10

    supervisor.enviar_pose_offline()

    assert supervisor.porta_serial.enviar.call_args_list == [
        call(f"<{i + 1},{i * 10}>") for i in range(6)
    ]


def test_salvar_pose_armazena_texto_e_retorna_botao(supervisor):
    supervisor.btn_salvar = SimpleNamespace(configure=Mock())

    supervisor.salvar_pose()

    assert supervisor.rotina_gravada == ["MovePose(90, 90, 90, 90, 90, 90)\n"]
    supervisor.after.assert_called_once()
    callback = supervisor.after.call_args.args[1]
    callback()
    assert supervisor.btn_salvar.configure.call_args_list[-1] == call(
        text="📌 Salvar Ponto", fg_color="#28a745"
    )


def test_exportar_gera_codigo_exato_e_limpa_estado(supervisor):
    supervisor.rotina_gravada = [
        "MovePose(1, 2, 3, 4, 5, 6)\n",
        "MovePose(6, 5, 4, 3, 2, 1)\n",
    ]
    supervisor.entry_nome_rotina = Mock()
    supervisor.entry_nome_rotina.get.return_value = "Teste"
    supervisor.caixa_texto_programacao = Mock()
    supervisor.tela_texto = object()
    supervisor.mostrar_tela = Mock()

    supervisor.exportar()

    expected = (
        "metodo Teste:\n"
        "    // Ponto 1\n"
        "    MovePose(1, 2, 3, 4, 5, 6)\n"
        "    Wait(1000)\n"
        "    // Ponto 2\n"
        "    MovePose(6, 5, 4, 3, 2, 1)\n"
        "    Wait(1000)\n"
        "\nsetup:\n"
        "    // Posição inicial\n"
        "    MovePose(1, 2, 3, 4, 5, 6)\n"
        "\nloop:\n"
        "    // Execução contínua\n"
        "    Teste\n"
    )
    supervisor.caixa_texto_programacao.insert.assert_called_once_with("1.0", expected)
    assert supervisor.rotina_gravada == []
    supervisor.entry_nome_rotina.delete.assert_called_once_with(0, "end")


def test_exportar_sem_pose_nao_faz_nada(supervisor):
    supervisor.entry_nome_rotina = Mock()

    supervisor.exportar()

    supervisor.entry_nome_rotina.get.assert_not_called()


def test_exportar_preserva_pontos_quando_nome_e_invalido(supervisor):
    supervisor.rotina_gravada = ["MovePose(1, 2, 3, 4, 5, 6)\n"]
    supervisor.entry_nome_rotina = Mock()
    supervisor.entry_nome_rotina.get.return_value = "Minha Rotina"

    supervisor.exportar()

    assert supervisor.rotina_gravada == ["MovePose(1, 2, 3, 4, 5, 6)\n"]
    supervisor.escrever_log.assert_called_once_with(
        "Nome da rotina deve conter apenas letras, números e sublinhado (_).", True
    )


def test_abrir_e_salvar_arquivo(monkeypatch, tmp_path, supervisor):
    source = tmp_path / "entrada.txt"
    source.write_text("setup:\n", encoding="utf-8")
    target = tmp_path / "saida.txt"
    editor = Mock()
    editor.get.return_value = "loop:\n"
    supervisor.caixa_texto_programacao = editor
    paths = iter([str(source), str(target)])
    monkeypatch.setattr(app_module.filedialog, "askopenfilename", lambda **kwargs: next(paths))
    monkeypatch.setattr(app_module.filedialog, "asksaveasfilename", lambda **kwargs: next(paths))

    supervisor.abrir_f()
    supervisor.salvar_f()

    editor.insert.assert_called_once_with("1.0", "setup:\n")
    assert target.read_text(encoding="utf-8") == "loop:\n"


def test_rodar_editor_e_painel_delegam_ao_processador(supervisor):
    supervisor.processar_codigo = Mock()
    supervisor.caixa_texto_programacao = Mock(get=Mock(return_value="editor"))
    supervisor.caixa_visualizacao = Mock(get=Mock(return_value="painel"))

    supervisor.rodar_f()
    supervisor.rodar_execucao()

    assert supervisor.processar_codigo.call_args_list == [call("editor"), call("painel")]


def test_executar_exemplo_delega_codigo_ao_processador(supervisor):
    supervisor.exemplo_atual = ROUTINE_EXAMPLES[0]
    supervisor.processar_codigo = Mock()

    supervisor.executar_exemplo()

    supervisor.processar_codigo.assert_called_once_with(ROUTINE_EXAMPLES[0].code)
    supervisor.escrever_log.assert_called_once_with("🧪 Executando exemplo: Posição neutra.")


def test_abrir_exemplo_no_editor_adiciona_metodo_sem_substituir_codigo(supervisor):
    supervisor.exemplo_atual = ROUTINE_EXAMPLES[1]
    supervisor.tela_texto = object()
    supervisor.mostrar_tela = Mock()
    supervisor.inserir_metodo_no_editor = Mock()

    supervisor.abrir_exemplo_no_editor()

    supervisor.mostrar_tela.assert_called_once_with(supervisor.tela_texto)
    supervisor.inserir_metodo_no_editor.assert_called_once_with(
        ROUTINE_EXAMPLES[1].method_name,
        ROUTINE_EXAMPLES[1].method_code,
    )


def test_inserir_metodo_acrescenta_ao_editor_e_preserva_conteudo(supervisor):
    supervisor.caixa_texto_programacao = Mock()
    supervisor.caixa_texto_programacao.get.return_value = "setup:\n    Wait(1)"

    supervisor.inserir_metodo_no_editor("Abrir", "metodo Abrir:\n    MoveTo(6, 30)\n")

    supervisor.caixa_texto_programacao.insert.assert_called_once_with(
        "end-1c",
        "\n\nmetodo Abrir:\n    MoveTo(6, 30)\n",
    )


def test_inserir_metodo_nao_duplica_declaracao_existente(supervisor):
    supervisor.caixa_texto_programacao = Mock()
    supervisor.caixa_texto_programacao.get.return_value = "metodo Abrir:\n    MoveTo(6, 30)"

    supervisor.inserir_metodo_no_editor("Abrir", "metodo Abrir:\n    MoveTo(6, 30)\n")

    supervisor.caixa_texto_programacao.insert.assert_not_called()
    supervisor.escrever_log.assert_called_once_with(
        "O método 'Abrir' já está presente no Editor.", True
    )


def test_salvar_metodos_do_editor_atualiza_biblioteca(supervisor):
    supervisor.caixa_texto_programacao = Mock()
    supervisor.caixa_texto_programacao.get.return_value = "metodo Novo:\n    Wait(10)"
    supervisor.metodos_usuario = {"Antigo": "metodo Antigo:\n    Wait(1)\n"}
    supervisor.biblioteca_metodos = Mock()
    supervisor.atualizar_lista_metodos_editor = Mock()

    supervisor.salvar_metodos_do_editor()

    assert supervisor.metodos_usuario == {
        "Antigo": "metodo Antigo:\n    Wait(1)\n",
        "Novo": "metodo Novo:\n    Wait(10)\n",
    }
    supervisor.biblioteca_metodos.save.assert_called_once_with(supervisor.metodos_usuario)
    supervisor.atualizar_lista_metodos_editor.assert_called_once_with()


def test_mostrar_tela_interrompe_execucao_e_troca_frame(supervisor):
    telas = [Mock() for _ in range(4)]
    (
        supervisor.tela_menu_inicial,
        supervisor.tela_slider,
        supervisor.tela_texto,
        supervisor.tela_executar,
    ) = telas

    supervisor.mostrar_tela(telas[2])

    assert supervisor.parar_execucao is True
    for tela in telas:
        tela.place_forget.assert_called_once_with()
    telas[2].place.assert_called_once_with(relx=0, rely=0, relwidth=1, relheight=1)


def test_navegar_e_ajustar_motor_apenas_na_tela_de_sliders(supervisor):
    supervisor.tela_slider = Mock()
    supervisor.tela_slider.winfo_ismapped.return_value = True
    supervisor.destacar_motor = Mock()
    supervisor.inc_s = Mock()

    assert supervisor.navegar_motores(None, -1) == "break"
    assert supervisor.motor_selecionado_idx == 5
    supervisor.destacar_motor.assert_called_once_with(5)

    assert supervisor.ajustar_motor_teclado(None, 10) == "break"
    supervisor.inc_s.assert_called_once_with(5, 10)


def test_tab_e_shift_tab_seguem_ordem_e_preservam_valores(supervisor):
    supervisor.tela_slider = Mock()
    supervisor.tela_slider.winfo_ismapped.return_value = True
    valores = [slider.value for slider in supervisor.sliders]

    assert supervisor.navegar_motores(SimpleNamespace(widget=supervisor.sliders[0]), 1) == "break"
    assert supervisor.motor_selecionado_idx == 1
    assert supervisor.sliders[1].focused is True
    assert supervisor.navegar_motores(SimpleNamespace(widget=supervisor.sliders[1]), -1) == "break"
    assert supervisor.motor_selecionado_idx == 0
    assert [slider.value for slider in supervisor.sliders] == valores


def test_navegacao_circular_apos_ultimo_slider(supervisor):
    supervisor.tela_slider = Mock()
    supervisor.tela_slider.winfo_ismapped.return_value = True

    supervisor.navegar_motores(SimpleNamespace(widget=supervisor.sliders[5]), 1)

    assert supervisor.motor_selecionado_idx == 0


def test_clique_seleciona_slider_sem_alterar_valor(supervisor):
    valor = supervisor.sliders[3].value

    supervisor.selecionar_motor(3)

    assert supervisor.motor_selecionado_idx == 3
    assert supervisor.sliders[3].focused is True
    assert supervisor.sliders[3].value == valor


def test_botao_stop_preserva_icone_e_nao_exibe_atalho():
    source = app_module.Path(app_module.__file__).read_text(encoding="utf-8")

    assert '[("⏹", "PARAR ROBÔ", self.solicitar_parada_imediata)]' in source
    assert source.count('("⏹", "STOP", self.solicitar_parada_imediata)') == 2
    assert "[Espaço]" not in source
    assert '"SPACE"' not in source


def test_rodar_rotina_f9_escolhe_tela_visivel(supervisor):
    supervisor.tela_texto = Mock()
    supervisor.tela_executar = Mock()
    supervisor.rodar_f = Mock()
    supervisor.rodar_execucao = Mock()
    supervisor.tela_texto.winfo_ismapped.return_value = False
    supervisor.tela_executar.winfo_ismapped.return_value = True

    supervisor.rodar_rotina_f9()

    supervisor.rodar_execucao.assert_called_once_with()
    supervisor.rodar_f.assert_not_called()


def test_abrir_execucao_carrega_arquivo_e_retorna_estado_desabilitado(
    monkeypatch, tmp_path, supervisor
):
    source = tmp_path / "rotina.txt"
    source.write_text("setup:\n", encoding="utf-8")
    supervisor.caixa_visualizacao = Mock()
    monkeypatch.setattr(
        app_module.filedialog,
        "askopenfilename",
        lambda **kwargs: str(source),
    )

    supervisor.abrir_execucao()

    assert supervisor.caixa_visualizacao.configure.call_args_list == [
        call(state="normal"),
        call(state="disabled"),
    ]
    supervisor.caixa_visualizacao.insert.assert_called_once_with("1.0", "setup:\n")
    supervisor.escrever_log.assert_called_once_with("📂 Arquivo carregado: rotina.txt")
