import logging
import math
import time
import tkinter as tk
from collections import deque
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from .gui_components import DicionarioComandos, EditorComLinhas, ToolTip
from .help_content import HELP_TOPICS
from .method_library import MethodLibrary
from .motor_controller import MOTOR_COUNT, MotorController
from .robix_language import (
    MovePoseCommand,
    MoveToCommand,
    WaitCommand,
    extract_method_sources,
    generate_routine,
    parse_command,
    parse_program,
)
from .routine_examples import (
    ROUTINE_EXAMPLES,
    RoutineExample,
    get_routine_example,
)
from .serial_manager import MAX_STOP_ID, GerenciadorSerial, format_stop_ack

MIN_ANGLE = 0
MAX_ANGLE = 180
MILLISECONDS_PER_DEGREE = 15
MAX_SPEED_DEGREES_PER_MS = 1 / MILLISECONDS_PER_DEGREE
ACCELERATION_DEGREES_PER_MS2 = 0.00025
MOVE_TO_SETTLING_MS = 100
MOVE_POSE_SETTLING_MS = 200
REAL_TIME_THROTTLE_SECONDS = 0.05
STOP_ACK_TIMEOUT_SECONDS = 1.0
STOP_ACK_POLL_MS = 50
STOP_BINDTAG = "RobixImmediateStop"

logger = logging.getLogger(__name__)


class RobixSupervisorio(ctk.CTk):
    def __init__(
        self,
        serial_manager: GerenciadorSerial | None = None,
        method_library: MethodLibrary | None = None,
    ) -> None:
        super().__init__()

        self.title("SuRI-EDU - Supervisório Educacional")
        self.geometry("1100x850")
        self.configure(fg_color="#1E1E1E")

        self.parar_execucao = False
        self.rotina_em_execucao = False
        self.rotina_gravada: list[str] = []
        self._execucao_geracao = 0
        self._callback_execucao: str | None = None
        self._fila_execucao: deque[str] = deque()
        self._comandos_loop: tuple[str, ...] = ()
        self._parada_solicitada = False
        self._parada_geracao = 0
        self._callback_ack: str | None = None
        self._limite_ack = 0.0

        self.var_tempo_real = tk.BooleanVar(value=False)
        self.var_debug_serial = tk.BooleanVar(value=True)

        self.tempos_motores = [0.0] * MOTOR_COUNT
        self.motor_selecionado_idx = 0
        self.frames_motores = []
        self.metodos_salvos = {}
        self.biblioteca_metodos = method_library if method_library is not None else MethodLibrary()
        self.metodos_usuario = self.biblioteca_metodos.load()

        self.porta_serial = serial_manager if serial_manager is not None else GerenciadorSerial()
        self.controle_motores = MotorController(
            self._transmitir_movimento,
            initial_desired=[90] * MOTOR_COUNT,
        )
        self.porta_selecionada = tk.StringVar(value="Conectar USB")
        self.lista_combos_portas = []

        self.frame_log = ctk.CTkFrame(self, fg_color="gray10", height=100, corner_radius=0)
        self.frame_log.pack(side="bottom", fill="x")
        self.frame_log.pack_propagate(False)

        self.console_log = ctk.CTkTextbox(
            self.frame_log, fg_color="#080808", font=("Consolas", 12), text_color="#00FF00"
        )
        self.console_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.frame_telas = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_telas.pack(fill="both", expand=True)

        self.tela_menu_inicial = ctk.CTkFrame(self.frame_telas, fg_color="transparent")
        self.tela_slider = ctk.CTkFrame(self.frame_telas, fg_color="transparent")
        self.tela_texto = ctk.CTkFrame(self.frame_telas, fg_color="transparent")
        self.tela_executar = ctk.CTkFrame(self.frame_telas, fg_color="transparent")
        self.tela_exemplos = ctk.CTkFrame(self.frame_telas, fg_color="transparent")

        self.construir_menu_inicial()
        self.construir_tela_slider()
        self.construir_tela_texto()
        self.construir_tela_executar()
        self.construir_tela_exemplos()

        self.configurar_atalhos_teclado()
        self.protocol("WM_DELETE_WINDOW", self.fechar_aplicacao)
        self.mostrar_tela(self.tela_menu_inicial)
        self.escrever_log("⚙️ Sistema SuRI-EDU atualizado. Pressione F1 para o Manual do Operador.")

    def abrir_ajuda(self, event=None):
        if hasattr(self, "janela_ajuda") and self.janela_ajuda.winfo_exists():
            self.janela_ajuda.focus()
            return

        self.janela_ajuda = ctk.CTkToplevel(self)
        self.janela_ajuda.title("Manual do Operador - SuRI-EDU")
        self.janela_ajuda.geometry("980x660")
        self.janela_ajuda.configure(fg_color="#1E1E1E")
        self.janela_ajuda.transient(self)

        frame_esq = ctk.CTkFrame(self.janela_ajuda, width=250, corner_radius=0, fg_color="gray15")
        frame_esq.pack(side="left", fill="y")
        frame_esq.pack_propagate(False)

        frame_dir = ctk.CTkFrame(self.janela_ajuda, fg_color="transparent")
        frame_dir.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame_esq,
            text="ÍNDICE DO MANUAL (F1)",
            font=("Arial", 16, "bold"),
            text_color="#569CD6",
        ).pack(pady=20)

        self.caixa_texto_ajuda = ctk.CTkTextbox(
            frame_dir, font=("Arial", 14), wrap="word", fg_color="gray10", text_color="#E0E0E0"
        )
        self.caixa_texto_ajuda.pack(fill="both", expand=True)

        def mudar_topico(titulo):
            self.caixa_texto_ajuda.configure(state="normal")
            self.caixa_texto_ajuda.delete("1.0", "end")
            self.caixa_texto_ajuda.insert("1.0", f"--- {titulo.upper()} ---\n\n")
            self.caixa_texto_ajuda.insert("end", HELP_TOPICS[titulo])
            self.caixa_texto_ajuda.configure(state="disabled")

        for titulo in HELP_TOPICS:
            btn = ctk.CTkButton(
                frame_esq,
                text=titulo,
                anchor="w",
                fg_color="transparent",
                text_color="white",
                hover_color="gray25",
                command=lambda t=titulo: mudar_topico(t),
            )
            btn.pack(fill="x", padx=10, pady=2)

        mudar_topico("1. Visão Geral")
        self._aplicar_bindtag_parada(self.janela_ajuda)

    def configurar_atalhos_teclado(self):
        self.bind_class(STOP_BINDTAG, "<space>", self.acao_espaco_emergencia)
        self._aplicar_bindtag_parada(self)
        self.bind("<F1>", self.abrir_ajuda)
        self.bind("<F2>", lambda e: self.mostrar_tela(self.tela_menu_inicial))
        self.bind("<F3>", lambda e: self.mostrar_tela(self.tela_slider))
        self.bind("<F4>", lambda e: self.mostrar_tela(self.tela_texto))
        self.bind("<F5>", lambda e: self.mostrar_tela(self.tela_executar))
        self.bind("<F6>", lambda e: self.mostrar_tela(self.tela_exemplos))
        self.bind("<F9>", self.rodar_rotina_f9)

        self.bind("<Tab>", lambda e: self.navegar_motores(e, 1))
        self.bind("<Shift-Tab>", lambda e: self.navegar_motores(e, -1))
        self.bind("<Left>", lambda e: self.ajustar_motor_teclado(e, -1))
        self.bind("<Right>", lambda e: self.ajustar_motor_teclado(e, 1))
        self.bind("<Down>", lambda e: self.ajustar_motor_teclado(e, -10))
        self.bind("<Up>", lambda e: self.ajustar_motor_teclado(e, 10))

    def _aplicar_bindtag_parada(self, widget: tk.Misc) -> None:
        tags = widget.bindtags()
        if STOP_BINDTAG not in tags:
            widget.bindtags((STOP_BINDTAG, *tags))
        for child in widget.winfo_children():
            self._aplicar_bindtag_parada(child)

    def rodar_rotina_f9(self, event=None):
        if self.tela_texto.winfo_ismapped():
            self.rodar_f()
        elif self.tela_executar.winfo_ismapped():
            self.rodar_execucao()
        elif self.__dict__.get("tela_exemplos") is not None and self.tela_exemplos.winfo_ismapped():
            self.executar_exemplo()
        else:
            self.escrever_log(
                "⚠️ Pressione F4 (Editor), F5 (Painel) ou F6 (Exemplos) antes de usar F9.",
                True,
            )

    def acao_espaco_emergencia(self, event: tk.Event | None) -> str | None:
        if not self.rotina_em_execucao:
            return None
        self.solicitar_parada_imediata()
        return "break"

    def navegar_motores(self, event: tk.Event | None, direcao: int) -> str | None:
        if not self.tela_slider.winfo_ismapped():
            return
        widget = getattr(event, "widget", None)
        if widget in self.sliders:
            self.motor_selecionado_idx = self.sliders.index(widget)
        self.motor_selecionado_idx = (self.motor_selecionado_idx + direcao) % MOTOR_COUNT
        self.sliders[self.motor_selecionado_idx].focus_set()
        self.destacar_motor(self.motor_selecionado_idx)
        return "break"

    def selecionar_motor(self, indice: int) -> None:
        self.motor_selecionado_idx = indice
        self.sliders[indice].focus_set()
        self.destacar_motor(indice)

    def destacar_motor(self, idx_selecionado):
        for i, frame in enumerate(self.frames_motores):
            if i == idx_selecionado:
                frame.configure(border_width=2, border_color="#3a7ebf")
            else:
                frame.configure(border_width=0)

    def ajustar_motor_teclado(self, event, delta):
        if not self.tela_slider.winfo_ismapped():
            return
        widget = getattr(event, "widget", None)
        if widget in self.sliders:
            self.motor_selecionado_idx = self.sliders.index(widget)
        self.inc_s(self.motor_selecionado_idx, delta)
        return "break"

    def escrever_log(self, msg, erro=False):
        ts = time.strftime("%H:%M:%S")
        self.console_log.configure(state="normal")
        self.console_log.insert("end", f"[{ts}] {'❌ ' if erro else ''}{msg}\n")
        self.console_log.see("end")
        self.console_log.configure(state="disabled")

    def mostrar_tela(self, tela_destino):
        if self.rotina_em_execucao:
            self.solicitar_parada_imediata()
        else:
            self.parar_execucao = True
        telas = [self.tela_menu_inicial, self.tela_slider, self.tela_texto, self.tela_executar]
        tela_exemplos = self.__dict__.get("tela_exemplos")
        if tela_exemplos is not None:
            telas.append(tela_exemplos)
        for t in telas:
            t.place_forget()
        tela_destino.place(relx=0, rely=0, relwidth=1, relheight=1)
        if tela_destino is self.tela_slider:
            self.after_idle(lambda: self.selecionar_motor(self.motor_selecionado_idx))

    def criar_toolbar_global(self, parent, titulo, botoes=None):
        toolbar = ctk.CTkFrame(parent, height=50, fg_color="gray15", corner_radius=0)
        toolbar.pack(side="top", fill="x")
        toolbar.pack_propagate(False)

        f_esq = ctk.CTkFrame(toolbar, fg_color="transparent")
        f_esq.pack(side="left", fill="y", padx=5)

        nav_botoes = [
            ("🏠", self.tela_menu_inicial, "Menu Inicial (F2)"),
            ("🎮", self.tela_slider, "Teach Pendant (F3)"),
            ("📝", self.tela_texto, "Editor (F4)"),
            ("🚀", self.tela_executar, "Painel de Execução (F5)"),
            ("🧪", self.tela_exemplos, "Exemplos (F6)"),
        ]

        for icon, target, hint in nav_botoes:
            btn = ctk.CTkButton(
                f_esq, text=icon, width=40, height=35, command=lambda t=target: self.mostrar_tela(t)
            )
            btn.pack(side="left", padx=2)
            ToolTip(btn, hint)

        btn_ajuda = ctk.CTkButton(
            f_esq, text="❓", width=40, height=35, fg_color="#1f538d", command=self.abrir_ajuda
        )
        btn_ajuda.pack(side="left", padx=10)
        ToolTip(btn_ajuda, "Manual do Operador (F1)")

        f_dir = ctk.CTkFrame(toolbar, fg_color="transparent")
        f_dir.pack(side="right", fill="y", padx=10)

        cb = ctk.CTkOptionMenu(
            f_dir, variable=self.porta_selecionada, command=self.conectar_arduino, width=140
        )
        cb.pack(side="right", padx=5)
        self.lista_combos_portas.append(cb)
        self.atualizar_lista_portas()

        chk_debug = ctk.CTkCheckBox(
            f_dir, text="Monitor", variable=self.var_debug_serial, font=("Arial", 12, "bold")
        )
        chk_debug.pack(side="right", padx=15)
        ToolTip(chk_debug, "Mostrar pacotes no log")

        if botoes:
            for item in botoes:
                b = ctk.CTkButton(f_dir, text=item[0], width=40, height=35, command=item[2])
                b.pack(side="right", padx=2)
                ToolTip(b, item[1])

        ctk.CTkLabel(toolbar, text=titulo, font=("Arial", 16, "bold"), text_color="white").pack(
            side="left", expand=True, fill="x"
        )

    def conectar_arduino(self, porta):
        if porta == "🔄 Atualizar...":
            self.atualizar_lista_portas()
            return
        ok, msg = self.porta_serial.conectar(porta)
        self.controle_motores.set_connection(ok, invalidate=True)
        if ok:
            self._parada_solicitada = False
        self.escrever_log(msg, not ok)

    def atualizar_lista_portas(self):
        portas = self.porta_serial.listar_portas() + ["🔄 Atualizar..."]
        for combo in self.lista_combos_portas:
            combo.configure(values=portas)

    def _transmitir_movimento(self, motor: int, angulo: int) -> bool:
        pacote = f"<{motor},{angulo}>"
        if self.porta_serial.enviar(pacote):
            self._parada_solicitada = False
            if self.var_debug_serial.get():
                self.escrever_log(f"📡 [TX] {pacote}")
            return True
        self.escrever_log("Erro de comunicação Serial!", True)
        return False

    def enviar_serial(self, m: int, a: int, *, origem: str = "manual") -> bool:
        if not (1 <= m <= MOTOR_COUNT and MIN_ANGLE <= a <= MAX_ANGLE):
            self.escrever_log(f"Limites excedidos: Motor {m}, Ângulo {a}°!", True)
            return False
        result = self.controle_motores.command_motor(m, a, source=origem)
        return bool(result.sent)

    def solicitar_parada_imediata(self) -> None:
        if (
            self._parada_solicitada
            and not self.rotina_em_execucao
            and self.controle_motores.snapshot.stop_state in {"requested", "command_sent"}
        ):
            return

        self._parada_solicitada = True
        parada_geracao = self._avancar_parada_geracao()
        self.parar_execucao = True
        self.rotina_em_execucao = False
        self._execucao_geracao += 1
        self._fila_execucao.clear()
        self._comandos_loop = ()
        self._cancelar_callback_execucao()
        self.controle_motores.set_routine_state("cancelled")
        self.controle_motores.invalidate_commanded_state()
        self.controle_motores.set_stop_state("requested")
        self.porta_serial.receber_respostas()

        if not self.porta_serial.enviar_parada(parada_geracao):
            self.controle_motores.set_stop_state("send_failed", "Falha ao enviar STOP")
            self.escrever_log(
                "🛑 Rotina cancelada; falha ao enviar a parada ao controlador.",
                True,
            )
            return

        self.controle_motores.set_stop_state("command_sent")
        self.escrever_log("🛑 Parada solicitada — aguardando confirmação do controlador.", True)
        self._limite_ack = time.monotonic() + STOP_ACK_TIMEOUT_SECONDS
        self._agendar_verificacao_ack(parada_geracao)

    def _avancar_parada_geracao(self) -> int:
        self._parada_geracao = (self._parada_geracao % MAX_STOP_ID) + 1
        return self._parada_geracao

    def parar_execucao_agora(self) -> None:
        self.solicitar_parada_imediata()

    def _cancelar_callback_execucao(self) -> None:
        if self._callback_execucao is None:
            return
        try:
            self.after_cancel(self._callback_execucao)
        except tk.TclError:
            logger.debug("Callback da rotina ja havia sido removido")
        self._callback_execucao = None

    def _cancelar_callback_ack(self) -> None:
        if self._callback_ack is not None:
            try:
                self.after_cancel(self._callback_ack)
            except tk.TclError:
                logger.debug("Callback de ACK ja havia sido removido")
        self._callback_ack = None

    def _agendar_verificacao_ack(self, parada_geracao: int) -> None:
        self._cancelar_callback_ack()
        self._callback_ack = self.after(
            STOP_ACK_POLL_MS,
            lambda: self._verificar_ack_parada(parada_geracao),
        )

    def _verificar_ack_parada(self, parada_geracao: int | None = None) -> None:
        parada_geracao = self._parada_geracao if parada_geracao is None else parada_geracao
        if parada_geracao != self._parada_geracao or not self._parada_solicitada:
            return
        self._callback_ack = None
        if format_stop_ack(parada_geracao) in self.porta_serial.receber_respostas():
            self.controle_motores.set_stop_state("controller_interrupted")
            self.escrever_log("✅ Controlador confirmou o processamento do STOP.")
            return
        if time.monotonic() >= self._limite_ack:
            self.controle_motores.set_stop_state("no_confirmation")
            self.escrever_log("⚠️ Parada enviada, mas sem confirmação do controlador.", True)
            return
        self._agendar_verificacao_ack(parada_geracao)

    def processar_codigo(self, texto_codigo: str) -> None:
        if self.rotina_em_execucao:
            self.solicitar_parada_imediata()

        self._execucao_geracao += 1
        geracao = self._execucao_geracao
        self._avancar_parada_geracao()
        self._cancelar_callback_ack()
        self.parar_execucao = False
        self.rotina_em_execucao = True
        self._parada_solicitada = False
        self.controle_motores.set_routine_state("running")
        self.controle_motores.set_stop_state("idle")
        self.escrever_log("🚀 Compilando código (análise de identação)...")

        programa = parse_program(
            texto_codigo,
            on_method=lambda nome: self.escrever_log(f"📦 Método '{nome}' registrado."),
        )
        self.metodos_salvos = programa.methods

        setup = self._expandir_comandos(programa.setup)
        loop = self._expandir_comandos(programa.loop)
        if setup is None or loop is None:
            self._finalizar_execucao(cancelada=True)
            return

        self._fila_execucao = deque(setup)
        self._comandos_loop = tuple(loop)
        if setup:
            self.escrever_log("▶ Executando SETUP...")
        elif loop:
            self.escrever_log("🔄 Executando LOOP (ESPAÇO para parar)...")
        self._agendar_proxima_etapa(0, geracao)

    def _expandir_comandos(
        self,
        comandos: list[str],
        pilha_chamadas: tuple[str, ...] = (),
    ) -> list[str] | None:
        expandidos: list[str] = []
        for comando in comandos:
            if comando not in self.metodos_salvos:
                expandidos.append(comando)
                continue
            if comando in pilha_chamadas:
                self.escrever_log(
                    f"Recursão detectada no método '{comando}'. Execução abortada.",
                    True,
                )
                return None
            subcomandos = self._expandir_comandos(
                self.metodos_salvos[comando],
                (*pilha_chamadas, comando),
            )
            if subcomandos is None:
                return None
            expandidos.extend(subcomandos)
        return expandidos

    def _agendar_proxima_etapa(self, atraso_ms: int, geracao: int) -> None:
        self._agendar_callback_execucao(
            atraso_ms,
            lambda: self._executar_proxima_etapa(geracao),
        )

    def _agendar_callback_execucao(self, atraso_ms: int, callback: Callable[[], None]) -> None:
        def executar() -> None:
            self._callback_execucao = None
            callback()

        self._callback_execucao = self.after(max(0, atraso_ms), executar)

    def _execucao_valida(self, geracao: int) -> bool:
        return (
            self.rotina_em_execucao
            and not self.parar_execucao
            and geracao == self._execucao_geracao
        )

    def _executar_proxima_etapa(self, geracao: int) -> None:
        if not self._execucao_valida(geracao):
            return
        if not self._fila_execucao:
            if self._comandos_loop:
                self.escrever_log("🔄 Executando LOOP (ESPAÇO para parar)...")
                self._fila_execucao.extend(self._comandos_loop)
            else:
                self._finalizar_execucao()
                return

        comando = self._fila_execucao.popleft()
        comando_parseado = parse_command(comando)
        if isinstance(comando_parseado, MovePoseCommand):
            self._executar_pose_em_etapas(comando_parseado, geracao)
            return
        atraso = self.executar_comando(comando, geracao=geracao)
        if self._execucao_valida(geracao):
            self._agendar_proxima_etapa(atraso, geracao)

    @staticmethod
    def _diferenca_movimento(angulo_anterior: int | None, angulo_alvo: int) -> int:
        return MAX_ANGLE if angulo_anterior is None else abs(angulo_alvo - angulo_anterior)

    @staticmethod
    def _estimar_tempo_movimento(diferenca: int) -> int:
        if diferenca <= 0:
            return 0
        limite_triangular = MAX_SPEED_DEGREES_PER_MS**2 / ACCELERATION_DEGREES_PER_MS2
        if diferenca <= limite_triangular:
            duracao = 2 * math.sqrt(diferenca / ACCELERATION_DEGREES_PER_MS2)
        else:
            duracao = (
                diferenca / MAX_SPEED_DEGREES_PER_MS
                + MAX_SPEED_DEGREES_PER_MS / ACCELERATION_DEGREES_PER_MS2
            )
        return math.ceil(duracao)

    def _executar_pose_em_etapas(self, comando: MovePoseCommand, geracao: int) -> None:
        if any(not MIN_ANGLE <= angulo <= MAX_ANGLE for angulo in comando.angles):
            self.escrever_log("MovePose contém ângulo fora do intervalo de 0 a 180.", True)
            self._agendar_proxima_etapa(0, geracao)
            return
        estado_anterior = self.controle_motores.snapshot.commanded
        angulos, motores = self.controle_motores.prepare_pose(
            comando.angles,
            source="MovePose",
        )
        for indice, angulo in enumerate(angulos):
            self.sliders[indice].set(angulo)
            self.labels[indice].configure(text=f"{angulo}°")

        diferencas_enviadas: list[int] = []

        def enviar_motor(indice: int) -> None:
            if not self._execucao_valida(geracao):
                return
            if indice >= len(motores):
                atraso = (
                    self._estimar_tempo_movimento(max(diferencas_enviadas)) + MOVE_POSE_SETTLING_MS
                    if diferencas_enviadas
                    else 0
                )
                self._agendar_proxima_etapa(atraso, geracao)
                return

            motor = motores[indice]
            resultado = self.controle_motores.command_motor(
                motor,
                angulos[motor - 1],
                source="MovePose",
                should_continue=lambda: self._execucao_valida(geracao),
            )
            if resultado.sent:
                diferencas_enviadas.append(
                    self._diferenca_movimento(estado_anterior[motor - 1], angulos[motor - 1])
                )
            if self._execucao_valida(geracao):
                self._agendar_callback_execucao(0, lambda: enviar_motor(indice + 1))

        self._agendar_callback_execucao(0, lambda: enviar_motor(0))

    def _finalizar_execucao(self, *, cancelada: bool = False) -> None:
        self.rotina_em_execucao = False
        self.parar_execucao = cancelada
        self._fila_execucao.clear()
        self._comandos_loop = ()
        self._callback_execucao = None
        self.controle_motores.set_routine_state("cancelled" if cancelada else "finished")
        if not cancelada:
            self.escrever_log("🏁 Fim da execução.")

    def executar_comando(self, cmd: str, *, geracao: int | None = None) -> int:
        if self.parar_execucao:
            return 0

        deve_continuar = (
            (lambda: self._execucao_valida(geracao))
            if geracao is not None
            else (lambda: not self.parar_execucao)
        )

        comando = parse_command(cmd)
        if isinstance(comando, MoveToCommand):
            if not 1 <= comando.motor <= MOTOR_COUNT:
                self.escrever_log(f"Motor inválido: {comando.motor}.", True)
                return 0
            if not MIN_ANGLE <= comando.angle <= MAX_ANGLE:
                self.escrever_log(
                    f"Ângulo inválido para o motor {comando.motor}: {comando.angle}.", True
                )
                return 0
            angulo = comando.angle
            angulo_anterior = self.controle_motores.snapshot.commanded[comando.motor - 1]

            resultado = self.controle_motores.command_motor(
                comando.motor,
                angulo,
                source="MoveTo",
                should_continue=deve_continuar,
            )
            self.sliders[comando.motor - 1].set(angulo)
            self.labels[comando.motor - 1].configure(text=f"{angulo}°")

            if not resultado.sent:
                return 0
            diferenca = self._diferenca_movimento(angulo_anterior, angulo)
            return self._estimar_tempo_movimento(diferenca) + MOVE_TO_SETTLING_MS

        if isinstance(comando, MovePoseCommand):
            if any(not MIN_ANGLE <= angulo <= MAX_ANGLE for angulo in comando.angles):
                self.escrever_log("MovePose contém ângulo fora do intervalo de 0 a 180.", True)
                return 0
            estado_anterior = self.controle_motores.snapshot.commanded
            for i in range(MOTOR_COUNT):
                angulo = MotorController.normalize_angle(comando.angles[i])
                self.sliders[i].set(angulo)
                self.labels[i].configure(text=f"{angulo}°")

            resultado = self.controle_motores.command_pose(
                comando.angles,
                source="MovePose",
                should_continue=deve_continuar,
            )

            if not resultado.sent:
                return 0
            max_diferenca = max(
                self._diferenca_movimento(
                    estado_anterior[motor - 1],
                    MotorController.normalize_angle(comando.angles[motor - 1]),
                )
                for motor in resultado.sent
            )
            return self._estimar_tempo_movimento(max_diferenca) + MOVE_POSE_SETTLING_MS

        if isinstance(comando, WaitCommand):
            return comando.milliseconds

        self.escrever_log(f"Sintaxe não reconhecida: '{cmd}'", True)
        return 0

    def construir_menu_inicial(self):
        self.criar_toolbar_global(self.tela_menu_inicial, "MENU PRINCIPAL")
        centro = ctk.CTkFrame(self.tela_menu_inicial, fg_color="transparent")
        centro.pack(expand=True)
        ctk.CTkLabel(centro, text="SuRI-EDU", font=("Arial", 40, "bold")).pack(pady=10)
        ctk.CTkLabel(
            centro,
            text="Supervisório Educacional para o braço Robix",
            font=("Arial", 16),
            text_color="gray70",
        ).pack(pady=(0, 25))
        ctk.CTkButton(
            centro,
            text="🧪  EXPLORAR EXEMPLOS",
            height=45,
            font=("Arial", 14, "bold"),
            command=lambda: self.mostrar_tela(self.tela_exemplos),
        ).pack()

    def construir_tela_slider(self):
        self.criar_toolbar_global(
            self.tela_slider,
            "TEACH PENDANT",
            [("⏹", "PARAR ROBÔ", self.solicitar_parada_imediata)],
        )

        rol = ctk.CTkScrollableFrame(self.tela_slider, fg_color="transparent")
        rol.pack(fill="both", expand=True)

        ctrl = ctk.CTkFrame(rol, fg_color="gray20", corner_radius=10)
        ctrl.pack(fill="x", padx=20, pady=10)

        ctk.CTkSwitch(ctrl, text="Modo Tempo Real", variable=self.var_tempo_real).pack(
            side="left", padx=20, pady=15
        )
        ctk.CTkButton(
            ctrl, text="▶ Enviar Pose", fg_color="#1f538d", command=self.enviar_pose_offline
        ).pack(side="left", padx=10)

        self.btn_salvar = ctk.CTkButton(
            ctrl, text="📌 Salvar Ponto", fg_color="#28a745", command=self.salvar_pose
        )
        self.btn_salvar.pack(side="left", padx=10)

        self.entry_nome_rotina = ctk.CTkEntry(ctrl, placeholder_text="Nome da Rotina", width=140)
        self.entry_nome_rotina.pack(side="right", padx=(10, 20))

        ctk.CTkButton(ctrl, text="📝 Exportar", command=self.exportar).pack(side="right", padx=10)

        grid = ctk.CTkFrame(rol, fg_color="transparent")
        grid.pack(expand=True, pady=10)

        nomes = ["Base", "Ombro", "Cotovelo", "Pitch", "Roll", "Garra"]
        self.sliders = []
        self.labels = []

        for i in range(MOTOR_COUNT):
            f = ctk.CTkFrame(grid, width=320, height=140, corner_radius=10)
            f.grid(row=i // 2, column=i % 2, padx=10, pady=10)
            f.grid_propagate(False)
            self.frames_motores.append(f)

            ctk.CTkLabel(f, text=f"{i + 1}. {nomes[i]}", font=("Arial", 12, "bold")).place(
                x=15, y=10
            )
            lbl_valor = ctk.CTkLabel(
                f, text="90°", text_color="#1f538d", font=("Arial", 14, "bold")
            )
            lbl_valor.place(x=260, y=10)
            self.labels.append(lbl_valor)

            slider = ctk.CTkSlider(
                f,
                from_=MIN_ANGLE,
                to=MAX_ANGLE,
                command=lambda v, idx=i: self.mover_s(idx, v),
            )
            slider.set(90)
            slider.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8)
            slider.bind("<Button-1>", lambda e, idx=i: self.selecionar_motor(idx))
            slider.bind("<FocusIn>", lambda e, idx=i: self.selecionar_motor(idx))
            slider.bind("<ButtonRelease-1>", lambda e, idx=i: self.final_s(idx))
            self.sliders.append(slider)

            fb = ctk.CTkFrame(f, fg_color="transparent")
            fb.place(relx=0.5, rely=0.85, anchor="center")
            for d in [-10, -1, 1, 10]:
                ctk.CTkButton(
                    fb,
                    text=f"{'+' if d > 0 else ''}{d}",
                    width=45,
                    height=25,
                    command=lambda idx=i, delta=d: self.inc_s(idx, delta),
                ).pack(side="left", padx=2)

        self.destacar_motor(0)

    def enviar_pose_offline(self) -> None:
        self.escrever_log("▶ Sincronizando robô com a pose atual...")
        self.controle_motores.command_pose(
            [int(slider.get()) for slider in self.sliders],
            source="Teach Pendant",
        )

    def mover_s(self, i: int, v: float) -> None:
        self.labels[i].configure(text=f"{int(v)}°")
        if (
            self.var_tempo_real.get()
            and time.time() - self.tempos_motores[i] > REAL_TIME_THROTTLE_SECONDS
        ):
            self.controle_motores.command_motor(
                i + 1,
                v,
                source="Teach Pendant em tempo real",
            )
            self.tempos_motores[i] = time.time()
        else:
            self.controle_motores.set_desired_motor(i + 1, v, source="Teach Pendant")

    def final_s(self, i: int) -> None:
        if self.var_tempo_real.get():
            self.controle_motores.command_motor(
                i + 1,
                self.sliders[i].get(),
                source="Teach Pendant em tempo real",
            )

    def inc_s(self, i: int, d: int) -> None:
        nv = max(MIN_ANGLE, min(MAX_ANGLE, int(self.sliders[i].get()) + d))
        self.sliders[i].set(nv)
        self.mover_s(i, nv)
        self.final_s(i)

    def salvar_pose(self):
        p = f"MovePose({', '.join([str(int(s.get())) for s in self.sliders])})\n"
        self.rotina_gravada.append(p)

        self.escrever_log(f"📍 Ponto {len(self.rotina_gravada)} salvo.")
        self.btn_salvar.configure(text="✅ Salvo!", fg_color="#155724")
        self.after(
            1000, lambda: self.btn_salvar.configure(text="📌 Salvar Ponto", fg_color="#28a745")
        )

    def exportar(self):
        if not self.rotina_gravada:
            return

        nome = self.entry_nome_rotina.get().strip()
        nome_metodo = nome if nome else "RotinaGravada"
        try:
            codigo = generate_routine(nome_metodo, self.rotina_gravada)
        except ValueError as error:
            self.escrever_log(str(error), True)
            return

        self.mostrar_tela(self.tela_texto)
        self.caixa_texto_programacao.delete("1.0", "end")
        self.caixa_texto_programacao.insert("1.0", codigo)

        self.rotina_gravada = []
        self.entry_nome_rotina.delete(0, "end")
        self.escrever_log(f"📝 Template '{nome_metodo}' gerado com sucesso!")

    def construir_tela_texto(self):
        acoes = [
            ("📂", "Abrir Arquivo", self.abrir_f),
            ("💾", "Salvar Arquivo", self.salvar_f),
            ("▶", "Rodar Rotina (F9)", self.rodar_f),
            ("⏹", "STOP", self.solicitar_parada_imediata),
        ]
        self.criar_toolbar_global(self.tela_texto, "EDITOR DE CÓDIGO", acoes)

        f_ed = ctk.CTkFrame(self.tela_texto, fg_color="transparent")
        f_ed.pack(fill="both", expand=True, padx=20, pady=10)

        self.caixa_texto_programacao = EditorComLinhas(f_ed)
        self.caixa_texto_programacao.pack(side="left", fill="both", expand=True)

        painel_lateral = ctk.CTkTabview(f_ed, width=300)
        painel_lateral.pack(side="right", fill="y", padx=(10, 0))
        aba_sintaxe = painel_lateral.add("Sintaxe")
        aba_metodos = painel_lateral.add("Métodos")
        DicionarioComandos(aba_sintaxe).pack(fill="both", expand=True)

        ctk.CTkLabel(
            aba_metodos,
            text="BIBLIOTECA DE MÉTODOS",
            font=("Arial", 11, "bold"),
            text_color="#569CD6",
        ).pack(fill="x", pady=(5, 3))
        ctk.CTkLabel(
            aba_metodos,
            text="Clique em um método para adicioná-lo ao código.",
            font=("Arial", 10),
            text_color="gray70",
            wraplength=250,
        ).pack(fill="x", padx=5, pady=(0, 5))

        self.lista_metodos_editor = ctk.CTkScrollableFrame(
            aba_metodos,
            fg_color="transparent",
        )
        self.lista_metodos_editor.pack(fill="both", expand=True)
        ctk.CTkButton(
            aba_metodos,
            text="💾 Salvar métodos do código",
            command=self.salvar_metodos_do_editor,
        ).pack(fill="x", padx=5, pady=(8, 5))
        self.atualizar_lista_metodos_editor()

    def atualizar_lista_metodos_editor(self) -> None:
        for child in self.lista_metodos_editor.winfo_children():
            child.destroy()

        self._adicionar_titulo_biblioteca("EXEMPLOS")
        for exemplo in ROUTINE_EXAMPLES:
            self._adicionar_item_biblioteca(
                exemplo.method_name,
                exemplo.method_code,
            )

        self._adicionar_titulo_biblioteca("MEUS MÉTODOS")
        if not self.metodos_usuario:
            ctk.CTkLabel(
                self.lista_metodos_editor,
                text="Nenhum método salvo.",
                font=("Arial", 10),
                text_color="gray60",
            ).pack(fill="x", padx=5, pady=5)
            return

        for nome, codigo in sorted(self.metodos_usuario.items()):
            self._adicionar_item_biblioteca(nome, codigo, removivel=True)

    def _adicionar_titulo_biblioteca(self, titulo: str) -> None:
        ctk.CTkLabel(
            self.lista_metodos_editor,
            text=titulo,
            font=("Arial", 10, "bold"),
            text_color="gray65",
            anchor="w",
        ).pack(fill="x", padx=5, pady=(8, 2))

    def _adicionar_item_biblioteca(
        self,
        nome: str,
        codigo: str,
        *,
        removivel: bool = False,
    ) -> None:
        linha = ctk.CTkFrame(self.lista_metodos_editor, fg_color="transparent")
        linha.pack(fill="x", pady=2)
        ctk.CTkButton(
            linha,
            text=f"＋ {nome}",
            anchor="w",
            height=32,
            command=lambda: self.inserir_metodo_no_editor(nome, codigo),
        ).pack(side="left", fill="x", expand=True)
        if removivel:
            botao_remover = ctk.CTkButton(
                linha,
                text="×",
                width=30,
                height=32,
                fg_color="#8B2E2E",
                hover_color="#6E2424",
                command=lambda: self.remover_metodo_salvo(nome),
            )
            botao_remover.pack(side="right", padx=(4, 0))
            ToolTip(botao_remover, f"Remover {nome}")

    def inserir_metodo_no_editor(self, nome: str, codigo: str) -> None:
        conteudo_atual = self.caixa_texto_programacao.get("1.0", "end-1c")
        if nome in parse_program(conteudo_atual).methods:
            self.escrever_log(f"O método '{nome}' já está presente no Editor.", True)
            return

        separador = "\n\n" if conteudo_atual.strip() else ""
        self.caixa_texto_programacao.insert(
            "end-1c",
            f"{separador}{codigo.rstrip()}\n",
        )
        self.escrever_log(
            f"➕ Método '{nome}' adicionado ao Editor. Chame-o pelo nome no setup ou loop."
        )

    def salvar_metodos_do_editor(self) -> None:
        conteudo = self.caixa_texto_programacao.get("1.0", "end-1c")
        encontrados = extract_method_sources(conteudo)
        if not encontrados:
            self.escrever_log("Nenhuma declaração 'metodo Nome:' encontrada no Editor.", True)
            return

        atualizados = {**self.metodos_usuario, **encontrados}
        try:
            self.biblioteca_metodos.save(atualizados)
        except OSError as error:
            logger.exception("Falha ao salvar biblioteca de metodos")
            self.escrever_log(f"Não foi possível salvar os métodos: {error}", True)
            return

        self.metodos_usuario = atualizados
        self.atualizar_lista_metodos_editor()
        self.escrever_log(f"💾 {len(encontrados)} método(s) salvo(s) na biblioteca do usuário.")

    def remover_metodo_salvo(self, nome: str) -> None:
        if nome not in self.metodos_usuario:
            return
        if not messagebox.askyesno(
            "Remover método",
            f"Remover '{nome}' da biblioteca?",
            parent=self,
        ):
            return

        restantes = {key: value for key, value in self.metodos_usuario.items() if key != nome}
        try:
            self.biblioteca_metodos.save(restantes)
        except OSError as error:
            logger.exception("Falha ao remover metodo da biblioteca")
            self.escrever_log(f"Não foi possível remover o método: {error}", True)
            return

        self.metodos_usuario = restantes
        self.atualizar_lista_metodos_editor()
        self.escrever_log(f"Método '{nome}' removido da biblioteca.")

    def rodar_f(self):
        codigo = self.caixa_texto_programacao.get("1.0", "end-1c")
        self.processar_codigo(codigo)

    def abrir_f(self):
        p = filedialog.askopenfilename(filetypes=[("TXT", "*.txt")])
        if p:
            caminho = Path(p)
            self.caixa_texto_programacao.delete("1.0", "end")
            self.caixa_texto_programacao.insert(
                "1.0",
                caminho.read_text(encoding="utf-8"),
            )
            self.escrever_log(f"📂 Aberto: {caminho.name}")

    def salvar_f(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")])
        if p:
            Path(p).write_text(
                self.caixa_texto_programacao.get("1.0", "end-1c"),
                encoding="utf-8",
            )
            self.escrever_log("💾 Rotina salva com sucesso.")

    def construir_tela_executar(self):
        acoes = [
            ("📂", "Carregar Arquivo", self.abrir_execucao),
            ("▶", "Iniciar (F9)", self.rodar_execucao),
            ("⏹", "STOP", self.solicitar_parada_imediata),
        ]
        self.criar_toolbar_global(self.tela_executar, "PAINEL DE EXECUÇÃO", acoes)

        self.caixa_visualizacao = EditorComLinhas(self.tela_executar)
        self.caixa_visualizacao.configure(state="disabled")
        self.caixa_visualizacao.pack(fill="both", expand=True, padx=20, pady=20)

    def abrir_execucao(self):
        p = filedialog.askopenfilename(filetypes=[("TXT", "*.txt")])
        if p:
            caminho = Path(p)
            self.caixa_visualizacao.configure(state="normal")
            self.caixa_visualizacao.delete("1.0", "end")
            self.caixa_visualizacao.insert("1.0", caminho.read_text(encoding="utf-8"))
            self.caixa_visualizacao.configure(state="disabled")
            self.escrever_log(f"📂 Arquivo carregado: {caminho.name}")

    def rodar_execucao(self):
        codigo = self.caixa_visualizacao.get("1.0", "end-1c")
        self.processar_codigo(codigo)

    def construir_tela_exemplos(self) -> None:
        acoes = [
            ("▶", "Executar Exemplo (F9)", self.executar_exemplo),
            ("⏹", "PARAR EXEMPLO", self.solicitar_parada_imediata),
        ]
        self.criar_toolbar_global(self.tela_exemplos, "EXEMPLOS", acoes)

        conteudo = ctk.CTkFrame(self.tela_exemplos, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=20, pady=15)

        lista = ctk.CTkScrollableFrame(conteudo, width=270, fg_color="gray15")
        lista.pack(side="left", fill="y", padx=(0, 15))
        ctk.CTkLabel(
            lista,
            text="ROTINAS DISPONÍVEIS",
            font=("Arial", 13, "bold"),
            text_color="#569CD6",
        ).pack(fill="x", padx=10, pady=(10, 8))

        self.botoes_exemplos = {}
        for exemplo in ROUTINE_EXAMPLES:
            botao = ctk.CTkButton(
                lista,
                text=exemplo.title,
                anchor="w",
                height=40,
                fg_color="transparent",
                hover_color="gray25",
                command=lambda chave=exemplo.key: self.selecionar_exemplo(chave),
            )
            botao.pack(fill="x", padx=8, pady=3)
            self.botoes_exemplos[exemplo.key] = botao

        painel = ctk.CTkFrame(conteudo, fg_color="gray15")
        painel.pack(side="right", fill="both", expand=True)

        self.titulo_exemplo = ctk.CTkLabel(
            painel,
            text="",
            font=("Arial", 22, "bold"),
            anchor="w",
        )
        self.titulo_exemplo.pack(fill="x", padx=18, pady=(15, 2))
        self.descricao_exemplo = ctk.CTkLabel(
            painel,
            text="",
            font=("Arial", 13),
            text_color="gray75",
            anchor="w",
            justify="left",
            wraplength=650,
        )
        self.descricao_exemplo.pack(fill="x", padx=18, pady=(0, 8))
        ctk.CTkLabel(
            painel,
            text=(
                "⚠ Revise os ângulos no Editor antes do primeiro teste. A faixa 0-180 "
                "não representa os limites mecânicos da sua montagem."
            ),
            font=("Arial", 12, "bold"),
            text_color="#F0AD4E",
            anchor="w",
            justify="left",
            wraplength=650,
        ).pack(fill="x", padx=18, pady=(0, 10))

        self.codigo_exemplo = ctk.CTkTextbox(
            painel,
            font=("Consolas", 13),
            wrap="none",
            fg_color="#101010",
        )
        self.codigo_exemplo.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        acoes_exemplo = ctk.CTkFrame(painel, fg_color="transparent")
        acoes_exemplo.pack(fill="x", padx=18, pady=(0, 15))
        ctk.CTkButton(
            acoes_exemplo,
            text="➕ Adicionar método ao Editor",
            command=self.abrir_exemplo_no_editor,
        ).pack(side="left")
        ctk.CTkButton(
            acoes_exemplo,
            text="▶ Executar uma vez",
            fg_color="#28A745",
            hover_color="#218838",
            command=self.executar_exemplo,
        ).pack(side="right")

        self.exemplo_atual = ROUTINE_EXAMPLES[0]
        self.selecionar_exemplo(self.exemplo_atual.key)

    def selecionar_exemplo(self, chave: str) -> None:
        exemplo = get_routine_example(chave)
        if exemplo is None:
            self.escrever_log(f"Exemplo desconhecido: {chave}.", True)
            return

        self.exemplo_atual = exemplo
        self.titulo_exemplo.configure(text=exemplo.title)
        self.descricao_exemplo.configure(text=exemplo.description)
        self.codigo_exemplo.configure(state="normal")
        self.codigo_exemplo.delete("1.0", "end")
        self.codigo_exemplo.insert("1.0", exemplo.code)
        self.codigo_exemplo.configure(state="disabled")
        for key, botao in self.botoes_exemplos.items():
            botao.configure(fg_color="#1F538D" if key == chave else "transparent")

    def abrir_exemplo_no_editor(self) -> None:
        exemplo: RoutineExample = self.exemplo_atual
        self.mostrar_tela(self.tela_texto)
        self.inserir_metodo_no_editor(exemplo.method_name, exemplo.method_code)

    def executar_exemplo(self) -> None:
        exemplo: RoutineExample = self.exemplo_atual
        self.escrever_log(f"🧪 Executando exemplo: {exemplo.title}.")
        self.processar_codigo(exemplo.code)

    def fechar_aplicacao(self) -> None:
        if self.rotina_em_execucao:
            self.solicitar_parada_imediata()
        self.porta_serial.desconectar()
        self.destroy()
