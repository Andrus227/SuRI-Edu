from __future__ import annotations

import logging
import time

import serial
import serial.tools.list_ports

DEFAULT_BAUDRATE = 115200
DEFAULT_TIMEOUT_SECONDS = 1
DEFAULT_WRITE_TIMEOUT_SECONDS = 0.1
ARDUINO_RESET_SECONDS = 1.5
STOP_COMMAND = "<STOP>"
STOP_ACK = "<ACK,STOP>"
MAX_STOP_ID = 2_147_483_647
MAX_FRAME_CONTENT_LENGTH = 31

logger = logging.getLogger(__name__)


def _validate_stop_id(stop_id: int) -> None:
    if isinstance(stop_id, bool) or not isinstance(stop_id, int) or not 1 <= stop_id <= MAX_STOP_ID:
        raise ValueError(f"stop_id deve estar entre 1 e {MAX_STOP_ID}")


def format_stop_command(stop_id: int) -> str:
    _validate_stop_id(stop_id)
    return f"<STOP,{stop_id}>"


def format_stop_ack(stop_id: int) -> str:
    _validate_stop_id(stop_id)
    return f"<ACK,STOP,{stop_id}>"


class GerenciadorSerial:
    def __init__(
        self,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        write_timeout: float = DEFAULT_WRITE_TIMEOUT_SECONDS,
    ) -> None:
        self.conexao: serial.Serial | None = None
        self.baudrate = baudrate
        self.timeout = timeout
        self.write_timeout = write_timeout
        self._receive_buffer = ""

    def listar_portas(self) -> list[str]:
        portas = [porta.device for porta in serial.tools.list_ports.comports()]
        return portas if portas else ["Nenhuma porta"]

    def esta_conectado(self) -> bool:
        return self.conexao is not None and self.conexao.is_open

    def conectar(self, porta: str) -> tuple[bool, str]:
        try:
            self.desconectar()
            self.conexao = serial.Serial(
                porta,
                self.baudrate,
                timeout=self.timeout,
                write_timeout=self.write_timeout,
            )
            self._receive_buffer = ""
            time.sleep(ARDUINO_RESET_SECONDS)
            return True, f"Conectado em {porta}"
        except serial.SerialException as e:
            logger.warning("Erro serial ao conectar em %s: %s", porta, e)
            return False, f"Erro serial ao conectar: {e}"
        except Exception as e:
            logger.exception("Erro inesperado ao conectar em %s", porta)
            return False, f"Erro inesperado ao conectar: {e}"

    def desconectar(self) -> None:
        if self.esta_conectado():
            self.conexao.close()

    def enviar(self, pacote_string: str) -> bool:
        return self._escrever(pacote_string)

    def enviar_parada(self, stop_id: int | None = None) -> bool:
        """Write STOP directly; regular movement commands are not queued."""
        command = STOP_COMMAND if stop_id is None else format_stop_command(stop_id)
        return self._escrever(command)

    def receber_respostas(self) -> list[str]:
        """Read complete framed responses without blocking the GUI thread."""
        if not self.esta_conectado():
            return []

        try:
            available = self.conexao.in_waiting
            if available <= 0:
                return []
            self._receive_buffer += self.conexao.read(available).decode("ascii", errors="replace")
        except (serial.SerialException, OSError) as error:
            logger.warning("Erro ao receber resposta serial: %s", error)
            return []
        except Exception:
            logger.exception("Erro inesperado ao receber resposta serial")
            return []

        responses: list[str] = []
        while "<" in self._receive_buffer:
            start = self._receive_buffer.find("<")
            self._receive_buffer = self._receive_buffer[start:]
            next_start = self._receive_buffer.find("<", 1)
            end = self._receive_buffer.find(">", 1)
            if next_start >= 0 and (end < 0 or next_start < end):
                self._receive_buffer = self._receive_buffer[next_start:]
                continue
            if end < 0:
                if len(self._receive_buffer) > MAX_FRAME_CONTENT_LENGTH + 2:
                    self._receive_buffer = ""
                break
            if end - 1 <= MAX_FRAME_CONTENT_LENGTH:
                responses.append(self._receive_buffer[: end + 1])
            self._receive_buffer = self._receive_buffer[end + 1 :]
        if "<" not in self._receive_buffer:
            self._receive_buffer = ""
        return responses

    def _escrever(self, pacote_string: str) -> bool:
        if not self.esta_conectado():
            return False

        try:
            payload = pacote_string.encode("ascii")
            return self.conexao.write(payload) == len(payload)
        except serial.SerialTimeoutException as error:
            logger.warning("Timeout ao enviar pacote serial: %s", error)
            return False
        except serial.SerialException as error:
            logger.warning("Erro ao enviar pacote serial: %s", error)
            return False
        except Exception:
            logger.exception("Erro inesperado ao enviar pacote serial")
            return False
