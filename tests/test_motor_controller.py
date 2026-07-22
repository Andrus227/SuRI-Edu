from unittest.mock import Mock, call

import pytest

from suri_edu.motor_controller import MotorController


def controller_with(sender=None):
    sender = sender or Mock(return_value=True)
    return MotorController(sender, initial_desired=[90] * 6, clock=lambda: 10.0), sender


def test_primeira_pose_envia_todos_quando_estado_comandado_e_desconhecido():
    controller, sender = controller_with()

    result = controller.command_pose([90] * 6, source="test")

    assert result.sent == (1, 2, 3, 4, 5, 6)
    assert sender.call_args_list == [call(motor, 90) for motor in range(1, 7)]


def test_pose_seguinte_envia_somente_motor_alterado():
    controller, sender = controller_with()
    controller.command_pose([10, 20, 30, 40, 50, 60], source="primeira")
    sender.reset_mock()

    result = controller.command_pose([10, 20, 35, 40, 50, 60], source="segunda")

    assert result.attempted == (3,)
    sender.assert_called_once_with(3, 35)


def test_pose_inalterada_nao_envia_pacotes():
    controller, sender = controller_with()
    controller.command_pose([10, 20, 30, 40, 50, 60], source="primeira")
    sender.reset_mock()

    result = controller.command_pose([10, 20, 30, 40, 50, 60], source="segunda")

    assert result.attempted == ()
    sender.assert_not_called()


def test_moveto_e_alteracao_manual_atualizam_comparacao_da_pose():
    controller, sender = controller_with()
    controller.command_pose([90] * 6, source="inicial")
    controller.command_motor(1, 30, source="MoveTo")
    controller.command_motor(2, 40, source="Teach Pendant")
    sender.reset_mock()

    controller.command_pose([30, 40, 90, 90, 90, 90], source="MovePose")

    sender.assert_not_called()


def test_reconexao_invalida_estado_e_forca_pose_completa():
    controller, sender = controller_with()
    controller.command_pose([90] * 6, source="inicial")
    controller.set_connection(True, invalidate=True)
    sender.reset_mock()

    controller.command_pose([90] * 6, source="apos reconexao")

    assert sender.call_count == 6


def test_falha_total_nao_atualiza_estado_comandado():
    controller, sender = controller_with(Mock(return_value=False))

    result = controller.command_pose([1, 2, 3, 4, 5, 6], source="test")

    assert result.failed == (1, 2, 3, 4, 5, 6)
    assert controller.snapshot.commanded == (None,) * 6
    assert sender.call_count == 6


def test_falha_parcial_preserva_estado_individual_dos_sucessos():
    sender = Mock(side_effect=[True, False, True, False, True, False])
    controller, _ = controller_with(sender)

    result = controller.command_pose([10, 20, 30, 40, 50, 60], source="test")

    assert result.sent == (1, 3, 5)
    assert result.failed == (2, 4, 6)
    assert controller.snapshot.commanded == (10, None, 30, None, 50, None)


def test_angulos_sao_normalizados_antes_da_comparacao():
    controller, sender = controller_with()
    controller.command_pose([-10, 20, 30, 40, 50, 200], source="primeira")
    sender.reset_mock()

    controller.command_pose([0, 20, 30, 40, 50, 180], source="segunda")

    sender.assert_not_called()
    assert controller.snapshot.commanded == (0, 20, 30, 40, 50, 180)


@pytest.mark.parametrize("motor", [0, 7, True])
def test_motor_invalido_e_rejeitado_sem_transmissao(motor):
    controller, sender = controller_with()

    with pytest.raises(ValueError):
        controller.command_motor(motor, 90, source="test")

    sender.assert_not_called()


def test_execucao_offline_mantem_desejado_sem_fingir_estado_comandado():
    controller, _ = controller_with(Mock(return_value=False))

    controller.command_motor(1, 45, source="offline")

    assert controller.snapshot.desired[0] == 45
    assert controller.snapshot.commanded[0] is None
    assert controller.snapshot.confirmed[0] is None


def test_cancelamento_durante_pose_impede_transmissoes_restantes():
    active = True

    def send(motor, angle):
        nonlocal active
        active = False
        return True

    controller = MotorController(send, initial_desired=[90] * 6)

    result = controller.command_pose(
        [1, 2, 3, 4, 5, 6],
        source="routine",
        should_continue=lambda: active,
    )

    assert result.sent == (1,)
    assert result.cancelled is True
    assert controller.snapshot.commanded == (1, None, None, None, None, None)


def test_observadores_recebem_snapshots_com_estados_distintos():
    controller, _ = controller_with()
    snapshots = []
    unsubscribe = controller.subscribe(snapshots.append)

    controller.set_desired_motor(1, 20, source="slider")
    controller.command_motor(1, 30, source="MoveTo")
    controller.confirm_motor(1, 25)
    unsubscribe()

    assert snapshots[-1].desired[0] == 30
    assert snapshots[-1].commanded[0] == 30
    assert snapshots[-1].confirmed[0] == 25
    assert snapshots[-1].source == "controller"
