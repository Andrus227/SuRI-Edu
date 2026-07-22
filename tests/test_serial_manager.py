from types import SimpleNamespace
from unittest.mock import Mock

import pytest
import serial

from suri_edu import serial_manager
from suri_edu.serial_manager import (
    MAX_STOP_ID,
    STOP_COMMAND,
    GerenciadorSerial,
    format_stop_ack,
    format_stop_command,
)


def test_listar_portas_retorna_dispositivos(monkeypatch):
    monkeypatch.setattr(
        serial_manager.serial.tools.list_ports,
        "comports",
        lambda: [SimpleNamespace(device="COM3"), SimpleNamespace(device="COM8")],
    )

    assert GerenciadorSerial().listar_portas() == ["COM3", "COM8"]


def test_listar_portas_retorna_sentindela_quando_vazia(monkeypatch):
    monkeypatch.setattr(serial_manager.serial.tools.list_ports, "comports", lambda: [])

    assert GerenciadorSerial().listar_portas() == ["Nenhuma porta"]


@pytest.mark.parametrize(
    ("connection", "expected"),
    [(None, False), (SimpleNamespace(is_open=False), False), (SimpleNamespace(is_open=True), True)],
)
def test_esta_conectado(connection, expected):
    manager = GerenciadorSerial()
    manager.conexao = connection

    assert manager.esta_conectado() is expected


def test_conectar_fecha_anterior_abre_serial_e_aguarda(monkeypatch):
    manager = GerenciadorSerial(baudrate=9600, timeout=2)
    manager.desconectar = Mock()
    connection = object()
    serial_factory = Mock(return_value=connection)
    sleep = Mock()
    monkeypatch.setattr(serial_manager.serial, "Serial", serial_factory)
    monkeypatch.setattr(serial_manager.time, "sleep", sleep)

    result = manager.conectar("COM4")

    assert result == (True, "Conectado em COM4")
    assert manager.conexao is connection
    manager.desconectar.assert_called_once_with()
    serial_factory.assert_called_once_with("COM4", 9600, timeout=2, write_timeout=0.1)
    sleep.assert_called_once_with(1.5)


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (serial.SerialException("ocupada"), "Erro serial ao conectar: ocupada"),
        (RuntimeError("falha"), "Erro inesperado ao conectar: falha"),
    ],
)
def test_conectar_converte_excecoes_em_resultado(monkeypatch, error, message):
    manager = GerenciadorSerial()
    monkeypatch.setattr(serial_manager.serial, "Serial", Mock(side_effect=error))

    assert manager.conectar("COM1") == (False, message)


def test_desconectar_fecha_apenas_conexao_aberta():
    manager = GerenciadorSerial()
    manager.conexao = SimpleNamespace(is_open=True, close=Mock())

    manager.desconectar()

    manager.conexao.close.assert_called_once_with()


def test_enviar_retorna_falso_quando_desconectado():
    assert GerenciadorSerial().enviar("<1,90>") is False


def test_enviar_codifica_pacote_em_utf8():
    manager = GerenciadorSerial()
    manager.conexao = SimpleNamespace(is_open=True, write=Mock(return_value=6))

    assert manager.enviar("<1,90>") is True
    manager.conexao.write.assert_called_once_with(b"<1,90>")


def test_enviar_parada_usa_comando_explicito_sem_fila():
    manager = GerenciadorSerial()
    manager.conexao = SimpleNamespace(is_open=True, write=Mock(return_value=6))

    assert manager.enviar_parada() is True
    manager.conexao.write.assert_called_once_with(STOP_COMMAND.encode("utf-8"))


def test_parada_identificada_permite_correlacionar_confirmacao():
    manager = GerenciadorSerial()
    manager.conexao = SimpleNamespace(is_open=True, write=Mock(return_value=9))

    assert manager.enviar_parada(42) is True
    manager.conexao.write.assert_called_once_with(format_stop_command(42).encode("utf-8"))
    assert format_stop_ack(42) == "<ACK,STOP,42>"


@pytest.mark.parametrize("stop_id", [True, 0, -1, MAX_STOP_ID + 1])
def test_parada_identificada_rejeita_id_fora_do_contrato(stop_id):
    with pytest.raises(ValueError):
        format_stop_command(stop_id)


def test_receber_respostas_monta_pacotes_fragmentados():
    chunks = [b"ruido<ACK,", b"STOP><POS,1,90>"]
    connection = SimpleNamespace(is_open=True, read=Mock(side_effect=chunks))
    manager = GerenciadorSerial()
    manager.conexao = connection

    connection.in_waiting = len(chunks[0])
    assert manager.receber_respostas() == []
    connection.in_waiting = len(chunks[1])
    assert manager.receber_respostas() == ["<ACK,STOP>", "<POS,1,90>"]


def test_receber_respostas_ressincroniza_em_novo_inicio():
    payload = b"<fragmento<ACK,STOP,7>\r\n"
    manager = GerenciadorSerial()
    manager.conexao = SimpleNamespace(
        is_open=True,
        in_waiting=len(payload),
        read=Mock(return_value=payload),
    )

    assert manager.receber_respostas() == ["<ACK,STOP,7>"]


def test_enviar_rejeita_escrita_parcial():
    manager = GerenciadorSerial()
    manager.conexao = SimpleNamespace(is_open=True, write=Mock(return_value=3))

    assert manager.enviar("<1,90>") is False


@pytest.mark.parametrize(
    "error",
    [serial.SerialTimeoutException(), serial.SerialException(), RuntimeError("falha")],
)
def test_enviar_converte_erros_de_escrita_em_falso(error):
    manager = GerenciadorSerial()
    manager.conexao = SimpleNamespace(is_open=True, write=Mock(side_effect=error))

    assert manager.enviar("<1,90>") is False
