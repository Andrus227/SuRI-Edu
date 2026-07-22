from collections import deque
from unittest.mock import Mock

import pytest

from suri_edu.app import RobixSupervisorio
from suri_edu.motor_controller import MotorController


class Value:
    def __init__(self, value=None):
        self.value = value
        self.configurations = []

    def get(self, *args, **kwargs):
        return self.value

    def set(self, value):
        self.value = value

    def configure(self, **kwargs):
        self.configurations.append(kwargs)

    def focus_set(self):
        self.focused = True


@pytest.fixture
def supervisor():
    app = RobixSupervisorio.__new__(RobixSupervisorio)
    app.parar_execucao = False
    app.rotina_em_execucao = False
    app.metodos_salvos = {}
    app.sliders = [Value(90) for _ in range(6)]
    app.labels = [Value("90°") for _ in range(6)]
    app.tempos_motores = [0.0] * 6
    app.rotina_gravada = []
    app.motor_selecionado_idx = 0
    app.frames_motores = [Value() for _ in range(6)]
    app.var_tempo_real = Value(False)
    app.var_debug_serial = Value(True)
    app.porta_serial = Mock()
    app.porta_serial.enviar.return_value = True
    app.porta_serial.enviar_parada.return_value = True
    app.porta_serial.receber_respostas.return_value = []
    app.escrever_log = Mock()
    app.update = Mock()
    app.after = Mock(return_value="after-id")
    app.after_idle = Mock()
    app.after_cancel = Mock()
    app._execucao_geracao = 0
    app._callback_execucao = None
    app._fila_execucao = deque()
    app._comandos_loop = ()
    app._parada_solicitada = False
    app._parada_geracao = 0
    app._callback_ack = None
    app._limite_ack = 0.0
    app.controle_motores = MotorController(
        app._transmitir_movimento,
        initial_desired=[90] * 6,
    )
    return app
