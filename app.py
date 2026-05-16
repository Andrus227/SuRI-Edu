import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
import re
import time

from gui_components import ToolTip, EditorComLinhas, DicionarioComandos
from serial_manager import GerenciadorSerial


class RobixSupervisorio(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SuRI-EDU - Supervisório Educacional")
        self.geometry("1100x850")
        self.configure(fg_color="#1E1E1E")

        self.botoes_dinamicos = {}
        self.parar_execucao = False
        self.rotina_gravada = []

        self.var_tempo_real = tk.BooleanVar(value=False)
        self.var_debug_serial = tk.BooleanVar(value=True)

        self.tempos_motores = [0.0] * 6
        self.motor_selecionado_idx = 0
        self.frames_motores = []
        self.metodos_salvos = {}

        self.porta_serial = GerenciadorSerial()
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

        self.construir_menu_inicial()
        self.construir_tela_slider()
        self.construir_tela_texto()
        self.construir_tela_executar()

        self.configurar_atalhos_teclado()
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

        ctk.CTkLabel(frame_esq, text="ÍNDICE DO MANUAL (F1)", font=("Arial", 16, "bold"), text_color="#569CD6").pack(pady=20)

        self.caixa_texto_ajuda = ctk.CTkTextbox(
            frame_dir, font=("Arial", 14), wrap="word", fg_color="gray10", text_color="#E0E0E0"
        )
        self.caixa_texto_ajuda.pack(fill="both", expand=True)

        textos_manual = {
            "1. Visão Geral": (
                "O SuRI-EDU é um supervisório educacional para controle do braço Robix com Arduino Mega.\n"
                "Ele integra interface desktop, comunicação serial e firmware no Arduino para executar movimentos.\n"
                "Documentação completa em HELP.md na pasta do projeto.\n"
                "Use o sistema com o robô fixado, área livre e atenção ao STOP de emergência.\n"
                "Consulte também: 2. Primeiros Passos e 7. Atalhos."
            ),
            "2. Primeiros Passos": (
                "1) Instale Python 3.x e crie o ambiente virtual.\n"
                "2) Instale dependências: pip install -r requirements.txt\n"
                "3) Grave o firmware Servo/Servo.ino no Arduino Mega.\n"
                "4) Conecte o USB e execute: python main.py\n"
                "5) Selecione a porta serial e teste um MoveTo(1, 90).\n"
                "Dica: no Windows, ative o ambiente com .venv\\Scripts\\activate."
            ),
            "3. Conexão Serial": (
                "Abra o menu de portas no topo direito e selecione a porta do Arduino.\n"
                "Use \"Atualizar...\" caso a porta não apareça.\n"
                "O modo Monitor exibe pacotes no log para depuração.\n"
                "Se aparecer \"Nenhuma porta\", verifique cabo USB, driver e Arduino ligado."
            ),
            "4. Teach Pendant (Sliders)": (
                "Controle manual das juntas por sliders.\n"
                "Modo Tempo Real envia o comando durante o arraste; desligado envia ao soltar.\n"
                "Use \"Enviar Pose\" para sincronizar com a pose atual.\n"
                "Use \"Salvar Ponto\" para gravar sequência e \"Exportar\" para gerar um método."
            ),
            "5. Editor de Código": (
                "O editor interpreta a Linguagem Robix com blocos setup, loop e metodo.\n"
                "Comandos suportados: MoveTo(M, A), MovePose(B, O, C, P, R, G) e Wait(MS).\n"
                "Exemplo:\n"
                "setup:\n"
                "    MoveTo(1, 90)\n"
                "loop:\n"
                "    MovePose(90, 90, 90, 90, 90, 90)\n"
                "    Wait(1000)\n"
                "Use o dicionário à direita como referência."
            ),
            "6. Painel de Execução": (
                "Carregue um arquivo .txt e execute sem editar.\n"
                "Use F5 para abrir o painel e F9 para iniciar a rotina.\n"
                "O painel é indicado para aulas e demonstrações rápidas.\n"
                "Para editar o código, use o Editor (F4)."
            ),
            "7. Atalhos e Operação": (
                "F1: Manual | F2: Menu | F3: Teach Pendant | F4: Editor | F5: Painel.\n"
                "F9: Executar rotina (Editor/Painel).\n"
                "Espaço: parada de emergência (não funciona dentro de campos de texto).\n"
                "Setas e Tab: navegação e ajuste fino dos motores no Teach Pendant."
            ),
            "8. FAQ": (
                "Q: Posso usar sem Arduino? A: É possível testar a interface, mas não haverá movimento.\n"
                "Q: Por que os motores não se mexem? A: Verifique conexão serial e se o firmware foi gravado.\n"
                "Q: Onde ficam as rotinas? A: Salve como .txt e abra no Editor/Painel."
            ),
            "9. Troubleshooting": (
                "- Erro de comunicação Serial: confirme porta correta e velocidade 115200.\n"
                "- Nenhuma porta: verifique cabo, driver e reinicie o Arduino.\n"
                "- Sintaxe não reconhecida: confirme MoveTo/MovePose/Wait e identação.\n"
                "- Recursão detectada: evite chamar método dentro dele mesmo.\n"
                "- Parada inesperada: pressione Espaço apenas em situações de risco."
            ),
            "10. Suporte e Bugs": (
                "Antes de solicitar suporte, anote: versão do Python, sistema, passos e arquivo .txt.\n"
                "Inclua trechos do log exibido na parte inferior do aplicativo.\n"
                "Contato: equipe do projeto/disciplinas listada no README.md.\n"
                "Sugestões de melhoria são bem-vindas para evolução do SuRI-EDU."
            ),
        }

        def mudar_topico(titulo):
            self.caixa_texto_ajuda.configure(state="normal")
            self.caixa_texto_ajuda.delete("1.0", "end")
            self.caixa_texto_ajuda.insert("1.0", f"--- {titulo.upper()} ---\n\n")
            self.caixa_texto_ajuda.insert("end", textos_manual[titulo])
            self.caixa_texto_ajuda.configure(state="disabled")

        for titulo in textos_manual.keys():
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

    def configurar_atalhos_teclado(self):
        self.bind("<space>", self.acao_espaco_emergencia)
        self.bind("<F1>", self.abrir_ajuda)
        self.bind("<F2>", lambda e: self.mostrar_tela(self.tela_menu_inicial))
        self.bind("<F3>", lambda e: self.mostrar_tela(self.tela_slider))
        self.bind("<F4>", lambda e: self.mostrar_tela(self.tela_texto))
        self.bind("<F5>", lambda e: self.mostrar_tela(self.tela_executar))
        self.bind("<F9>", self.rodar_rotina_f9)

        self.bind("<Tab>", lambda e: self.navegar_motores(e, 1))
        self.bind("<Shift-Tab>", lambda e: self.navegar_motores(e, -1))
        self.bind("<Left>", lambda e: self.ajustar_motor_teclado(e, -1))
        self.bind("<Right>", lambda e: self.ajustar_motor_teclado(e, 1))
        self.bind("<Down>", lambda e: self.ajustar_motor_teclado(e, -10))
        self.bind("<Up>", lambda e: self.ajustar_motor_teclado(e, 10))

    def rodar_rotina_f9(self, event=None):
        if self.tela_texto.winfo_ismapped():
            self.rodar_f()
        elif self.tela_executar.winfo_ismapped():
            self.rodar_execucao()
        else:
            self.escrever_log("⚠️ Pressione F4 (Editor) ou F5 (Painel) antes de usar F9.", True)

    def acao_espaco_emergencia(self, event):
        widget_em_foco = self.focus_get()
        if isinstance(widget_em_foco, (tk.Entry, tk.Text, ctk.CTkTextbox, ctk.CTkEntry)):
            return
        self.parar_execucao_agora()

    def navegar_motores(self, event, direcao):
        if not self.tela_slider.winfo_ismapped():
            return
        self.motor_selecionado_idx = (self.motor_selecionado_idx + direcao) % 6
        self.destacar_motor(self.motor_selecionado_idx)
        return "break"

    def destacar_motor(self, idx_selecionado):
        for i, frame in enumerate(self.frames_motores):
            if i == idx_selecionado:
                frame.configure(border_width=2, border_color="#3a7ebf")
            else:
                frame.configure(border_width=0)

    def ajustar_motor_teclado(self, event, delta):
        if not self.tela_slider.winfo_ismapped():
            return
        self.inc_s(self.motor_selecionado_idx, delta)
        return "break"

    def escrever_log(self, msg, erro=False):
        ts = time.strftime("%H:%M:%S")
        self.console_log.configure(state="normal")
        self.console_log.insert("end", f"[{ts}] {'❌ ' if erro else ''}{msg}\n")
        self.console_log.see("end")
        self.console_log.configure(state="disabled")

    def mostrar_tela(self, tela_destino):
        self.parar_execucao = True
        for t in [self.tela_menu_inicial, self.tela_slider, self.tela_texto, self.tela_executar]:
            t.place_forget()
        tela_destino.place(relx=0, rely=0, relwidth=1, relheight=1)

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
        ]

        for icon, target, hint in nav_botoes:
            btn = ctk.CTkButton(f_esq, text=icon, width=40, height=35, command=lambda t=target: self.mostrar_tela(t))
            btn.pack(side="left", padx=2)
            ToolTip(btn, hint)

        btn_ajuda = ctk.CTkButton(f_esq, text="❓", width=40, height=35, fg_color="#1f538d", command=self.abrir_ajuda)
        btn_ajuda.pack(side="left", padx=10)
        ToolTip(btn_ajuda, "Manual do Operador (F1)")

        f_dir = ctk.CTkFrame(toolbar, fg_color="transparent")
        f_dir.pack(side="right", fill="y", padx=10)

        cb = ctk.CTkOptionMenu(f_dir, variable=self.porta_selecionada, command=self.conectar_arduino, width=140)
        cb.pack(side="right", padx=5)
        self.lista_combos_portas.append(cb)
        self.atualizar_lista_portas()

        chk_debug = ctk.CTkCheckBox(f_dir, text="Monitor", variable=self.var_debug_serial, font=("Arial", 12, "bold"))
        chk_debug.pack(side="right", padx=15)
        ToolTip(chk_debug, "Mostrar pacotes no log")

        if botoes:
            for item in botoes:
                b = ctk.CTkButton(f_dir, text=item[0], width=40, height=35, command=item[2])
                b.pack(side="right", padx=2)
                ToolTip(b, item[1])

        ctk.CTkLabel(toolbar, text=titulo, font=("Arial", 16, "bold"), text_color="white").pack(side="left", expand=True, fill="x")

    def conectar_arduino(self, porta):
        if porta == "🔄 Atualizar...":
            self.atualizar_lista_portas()
            return
        ok, msg = self.porta_serial.conectar(porta)
        self.escrever_log(msg, not ok)

    def atualizar_lista_portas(self):
        portas = self.porta_serial.listar_portas() + ["🔄 Atualizar..."]
        for combo in self.lista_combos_portas:
            combo.configure(values=portas)

    def enviar_serial(self, m, a):
        if not (1 <= m <= 6 and 0 <= a <= 180):
            self.escrever_log(f"Limites excedidos: Motor {m}, Ângulo {a}°!", True)
            return

        if self.porta_serial.enviar(f"<{m},{a}>"):
            if self.var_debug_serial.get():
                self.escrever_log(f"📡 [TX] <{m},{a}>")
        else:
            self.escrever_log("Erro de comunicação Serial!", True)

    def aguardar_com_parada(self, ms):
        fim = time.time() + ms / 1000.0
        while time.time() < fim and not self.parar_execucao:
            self.update()
            time.sleep(0.02)

    def parar_execucao_agora(self):
        self.parar_execucao = True
        self.escrever_log("🛑 Parada de emergência ativada.", True)

    def processar_codigo(self, texto_codigo):
        self.parar_execucao = False
        self.escrever_log("🚀 Compilando código (análise de identação)...")

        linhas = texto_codigo.split("\n")
        self.metodos_salvos = {}
        bloco_setup = []
        bloco_loop = []

        estado_alvo = "root"
        nivel_base = -1

        for linha_bruta in linhas:
            linha_sem_comentario = linha_bruta.split("//")[0].rstrip().rstrip(";")
            if not linha_sem_comentario.strip():
                continue

            identacao = len(linha_sem_comentario) - len(linha_sem_comentario.lstrip())
            cmd = linha_sem_comentario.strip()

            match_metodo = re.search(r"^metodo\s+([a-zA-Z0-9_]+)\s*:", cmd, re.IGNORECASE)
            if match_metodo:
                nome = match_metodo.group(1)
                self.metodos_salvos[nome] = []
                estado_alvo = f"metodo_{nome}"
                nivel_base = identacao
                self.escrever_log(f"📦 Método '{nome}' registrado.")
                continue

            if cmd.lower() == "setup:":
                estado_alvo = "setup_block"
                nivel_base = identacao
                continue

            if cmd.lower() == "loop:":
                estado_alvo = "loop_block"
                nivel_base = identacao
                continue

            if nivel_base != -1 and identacao > nivel_base:
                if estado_alvo.startswith("metodo_"):
                    nome = estado_alvo.replace("metodo_", "")
                    self.metodos_salvos[nome].append(cmd)
                elif estado_alvo == "setup_block":
                    bloco_setup.append(cmd)
                elif estado_alvo == "loop_block":
                    bloco_loop.append(cmd)
            else:
                estado_alvo = "root"
                nivel_base = -1
                bloco_setup.append(cmd)

        if bloco_setup:
            self.escrever_log("▶ Executando SETUP...")
            for cmd in bloco_setup:
                if self.parar_execucao:
                    break
                self.executar_comando(cmd)

        if bloco_loop and not self.parar_execucao:
            self.escrever_log("🔄 Executando LOOP (ESPAÇO para parar)...")
            while not self.parar_execucao:
                for cmd in bloco_loop:
                    if self.parar_execucao:
                        break
                    self.executar_comando(cmd)

        if not self.parar_execucao:
            self.escrever_log("🏁 Fim da execução.")

    def executar_comando(self, cmd, pilha_chamadas=None):
        if self.parar_execucao:
            return

        if pilha_chamadas is None:
            pilha_chamadas = []

        self.update()

        if cmd in self.metodos_salvos:
            if cmd in pilha_chamadas:
                self.escrever_log(f"Recursão detectada no método '{cmd}'. Execução abortada.", True)
                self.parar_execucao = True
                return

            pilha_chamadas.append(cmd)
            for sub_cmd in self.metodos_salvos[cmd]:
                if self.parar_execucao:
                    break
                self.executar_comando(sub_cmd, pilha_chamadas)
            pilha_chamadas.pop()
            return

        m_mov = re.search(r"MoveTo\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", cmd, re.IGNORECASE)
        if m_mov:
            motor = int(m_mov.group(1))
            angulo = int(m_mov.group(2))
            angulo_atual = int(self.sliders[motor - 1].get())
            diferenca = abs(angulo - angulo_atual)

            self.enviar_serial(motor, angulo)
            self.sliders[motor - 1].set(angulo)

            tempo_espera = (diferenca * 15) + 100
            if diferenca > 0:
                self.aguardar_com_parada(tempo_espera)
            return

        m_pose = re.search(
            r"MovePose\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)",
            cmd,
            re.IGNORECASE,
        )
        if m_pose:
            angulos_alvo = [int(m_pose.group(i)) for i in range(1, 7)]
            max_diferenca = 0

            for i in range(6):
                angulo_atual = int(self.sliders[i].get())
                diferenca = abs(angulos_alvo[i] - angulo_atual)
                if diferenca > max_diferenca:
                    max_diferenca = diferenca

                self.enviar_serial(i + 1, angulos_alvo[i])
                self.sliders[i].set(angulos_alvo[i])

            tempo_espera = (max_diferenca * 15) + 200
            if max_diferenca > 0:
                self.aguardar_com_parada(tempo_espera)
            return

        m_wait = re.search(r"Wait\s*\(\s*(\d+)\s*\)", cmd, re.IGNORECASE)
        if m_wait:
            self.aguardar_com_parada(int(m_wait.group(1)))
            return

        self.escrever_log(f"Sintaxe não reconhecida: '{cmd}'", True)

    def construir_menu_inicial(self):
        self.criar_toolbar_global(self.tela_menu_inicial, "MENU PRINCIPAL")
        ctk.CTkLabel(self.tela_menu_inicial, text="SuRI-EDU", font=("Arial", 40, "bold")).pack(expand=True)

    def construir_tela_slider(self):
        self.criar_toolbar_global(self.tela_slider, "TEACH PENDANT", [("⏹", "PARAR ROBÔ (ESPAÇO)", self.parar_execucao_agora)])

        rol = ctk.CTkScrollableFrame(self.tela_slider, fg_color="transparent")
        rol.pack(fill="both", expand=True)

        ctrl = ctk.CTkFrame(rol, fg_color="gray20", corner_radius=10)
        ctrl.pack(fill="x", padx=20, pady=10)

        ctk.CTkSwitch(ctrl, text="Modo Tempo Real", variable=self.var_tempo_real).pack(side="left", padx=20, pady=15)
        ctk.CTkButton(ctrl, text="▶ Enviar Pose", fg_color="#1f538d", command=self.enviar_pose_offline).pack(side="left", padx=10)

        self.btn_salvar = ctk.CTkButton(ctrl, text="📌 Salvar Ponto", fg_color="#28a745", command=self.salvar_pose)
        self.btn_salvar.pack(side="left", padx=10)

        self.entry_nome_rotina = ctk.CTkEntry(ctrl, placeholder_text="Nome da Rotina", width=140)
        self.entry_nome_rotina.pack(side="right", padx=(10, 20))

        ctk.CTkButton(ctrl, text="📝 Exportar", command=self.exportar).pack(side="right", padx=10)

        grid = ctk.CTkFrame(rol, fg_color="transparent")
        grid.pack(expand=True, pady=10)

        nomes = ["Base", "Ombro", "Cotovelo", "Pitch", "Roll", "Garra"]
        self.sliders = []
        self.labels = []

        for i in range(6):
            f = ctk.CTkFrame(grid, width=320, height=140, corner_radius=10)
            f.grid(row=i // 2, column=i % 2, padx=10, pady=10)
            f.grid_propagate(False)
            self.frames_motores.append(f)

            ctk.CTkLabel(f, text=f"{i+1}. {nomes[i]}", font=("Arial", 12, "bold")).place(x=15, y=10)
            lbl_valor = ctk.CTkLabel(f, text="90°", text_color="#1f538d", font=("Arial", 14, "bold"))
            lbl_valor.place(x=260, y=10)
            self.labels.append(lbl_valor)

            slider = ctk.CTkSlider(f, from_=0, to=180, command=lambda v, idx=i: self.mover_s(idx, v))
            slider.set(90)
            slider.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.8)
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

    def enviar_pose_offline(self):
        self.escrever_log("▶ Sincronizando robô com a pose atual...")
        for i, s in enumerate(self.sliders):
            self.enviar_serial(i + 1, int(s.get()))

    def mover_s(self, i, v):
        self.labels[i].configure(text=f"{int(v)}°")
        if self.var_tempo_real.get() and time.time() - self.tempos_motores[i] > 0.05:
            self.enviar_serial(i + 1, int(v))
            self.tempos_motores[i] = time.time()

    def final_s(self, i):
        if self.var_tempo_real.get():
            self.enviar_serial(i + 1, int(self.sliders[i].get()))

    def inc_s(self, i, d):
        nv = max(0, min(180, int(self.sliders[i].get()) + d))
        self.sliders[i].set(nv)
        self.mover_s(i, nv)
        self.final_s(i)

    def salvar_pose(self):
        p = f"MovePose({', '.join([str(int(s.get())) for s in self.sliders])})\n"
        self.rotina_gravada.append(p)

        self.escrever_log(f"📍 Ponto {len(self.rotina_gravada)} salvo.")
        self.btn_salvar.configure(text="✅ Salvo!", fg_color="#155724")
        self.after(1000, lambda: self.btn_salvar.configure(text="📌 Salvar Ponto", fg_color="#28a745"))

    def exportar(self):
        if not self.rotina_gravada:
            return

        nome = self.entry_nome_rotina.get().strip()
        nome_metodo = nome if nome else "RotinaGravada"

        codigo = f"metodo {nome_metodo}:\n"
        for i, pose in enumerate(self.rotina_gravada):
            codigo += f"    // Ponto {i+1}\n"
            codigo += f"    {pose}"
            codigo += "    Wait(1000)\n"

        codigo += "\nsetup:\n"
        codigo += "    // Posição inicial\n"
        codigo += f"    {self.rotina_gravada[0]}"

        codigo += "\nloop:\n"
        codigo += "    // Execução contínua\n"
        codigo += f"    {nome_metodo}\n"

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
            ("⏹", "STOP", self.parar_execucao_agora),
        ]
        self.criar_toolbar_global(self.tela_texto, "EDITOR DE CÓDIGO", acoes)

        f_ed = ctk.CTkFrame(self.tela_texto, fg_color="transparent")
        f_ed.pack(fill="both", expand=True, padx=20, pady=10)

        self.caixa_texto_programacao = EditorComLinhas(f_ed)
        self.caixa_texto_programacao.pack(side="left", fill="both", expand=True)
        DicionarioComandos(f_ed, width=300).pack(side="right", fill="y", padx=(10, 0))

    def rodar_f(self):
        codigo = self.caixa_texto_programacao.get("1.0", "end-1c")
        self.processar_codigo(codigo)

    def abrir_f(self):
        p = filedialog.askopenfilename(filetypes=[("TXT", "*.txt")])
        if p:
            with open(p, "r", encoding="utf-8") as f:
                self.caixa_texto_programacao.delete("1.0", "end")
                self.caixa_texto_programacao.insert("1.0", f.read())
            self.escrever_log(f"📂 Aberto: {os.path.basename(p)}")

    def salvar_f(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT", "*.txt")])
        if p:
            with open(p, "w", encoding="utf-8") as f:
                f.write(self.caixa_texto_programacao.get("1.0", "end-1c"))
            self.escrever_log("💾 Rotina salva com sucesso.")

    def construir_tela_executar(self):
        acoes = [
            ("📂", "Carregar Arquivo", self.abrir_execucao),
            ("▶", "Iniciar (F9)", self.rodar_execucao),
            ("⏹", "STOP", self.parar_execucao_agora),
        ]
        self.criar_toolbar_global(self.tela_executar, "PAINEL DE EXECUÇÃO", acoes)

        self.caixa_visualizacao = EditorComLinhas(self.tela_executar)
        self.caixa_visualizacao.configure(state="disabled")
        self.caixa_visualizacao.pack(fill="both", expand=True, padx=20, pady=20)

    def abrir_execucao(self):
        p = filedialog.askopenfilename(filetypes=[("TXT", "*.txt")])
        if p:
            with open(p, "r", encoding="utf-8") as f:
                self.caixa_visualizacao.configure(state="normal")
                self.caixa_visualizacao.delete("1.0", "end")
                self.caixa_visualizacao.insert("1.0", f.read())
                self.caixa_visualizacao.configure(state="disabled")
            self.escrever_log(f"📂 Arquivo carregado: {os.path.basename(p)}")

    def rodar_execucao(self):
        codigo = self.caixa_visualizacao.get("1.0", "end-1c")
        self.processar_codigo(codigo)
