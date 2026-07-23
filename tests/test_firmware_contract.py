from pathlib import Path

FIRMWARE = Path(__file__).parents[1] / "Servo" / "Servo.ino"


def test_firmware_preserva_protocolo_e_limites():
    source = FIRMWARE.read_text(encoding="utf-8")

    assert "Serial.begin(115200)" in source
    assert "const int pinosMotores[6] = {8,9,10,11,12,13};" in source
    assert "motorRecebido >= 1 && motorRecebido <= 6" in source
    assert "anguloRecebido >= 0 && anguloRecebido <= 180" in source
    assert "const float VELOCIDADE_MAX_GRAUS_MS = 1.0 / 15.0" in source
    assert "const float ACELERACAO_GRAUS_MS2 = 0.00025" in source


def test_firmware_inicializa_todos_os_servos_em_90_graus():
    source = FIRMWARE.read_text(encoding="utf-8")

    assert "for (int i = 0; i < 6; i++)" in source
    assert "motores[i].attach(pinosMotores[i]);" in source
    assert "motores[i].write(90);" in source


def test_firmware_processa_stop_durante_interpolacao_e_confirma():
    source = FIRMWARE.read_text(encoding="utf-8")

    assert 'strcmp(receivedChars, "STOP") == 0' in source
    assert 'strncmp(receivedChars, "STOP,", 5) == 0' in source
    assert "posicaoAlvo[i] = posicaoAtual[i];" in source
    assert "velocidadeAtual[i] = 0.0;" in source
    assert 'Serial.print("<ACK,STOP,");' in source
    assert "receberComandoSerial();" in source
    assert "delay(" not in source


def test_firmware_aplica_suavizacao_global_sem_passos_no_codigo_robix():
    source = FIRMWARE.read_text(encoding="utf-8")

    assert "velocidadeDeFrenagem = sqrt" in source
    assert "variacaoMaxima = ACELERACAO_GRAUS_MS2 * deltaTempo" in source
    assert "INTERVALO_ATUALIZACAO_MS" in source


def test_firmware_descarta_campos_vazios_e_ressincroniza_quadros():
    source = FIRMWARE.read_text(encoding="utf-8")

    assert "bool contemSomenteDigitos" in source
    assert "!contemSomenteDigitos(separador + 1)" in source
    assert "if (rc == startMarker)" in source
    assert "frameOverflow = true;" in source
    assert "texto[0] == '0'" in source


def test_stop_mantem_servos_anexados_e_congela_alvos():
    source = FIRMWARE.read_text(encoding="utf-8")
    stop_block = source.split("// Congela os alvos", maxsplit=1)[1].split(
        "char *separador", maxsplit=1
    )[0]

    assert ".detach(" not in stop_block
    assert "posicaoAlvo[i] = posicaoAtual[i];" in stop_block
