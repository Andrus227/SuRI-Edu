import re
import tkinter as tk

import customtkinter as ctk


class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None

        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return

        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5

        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{x}+{y}")

        tk.Label(
            self.tip_window,
            text=self.text,
            background="#333333",
            fg="white",
            relief="solid",
            borderwidth=1,
            font=("Arial", 11),
        ).pack(ipadx=5, ipady=2)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


class EditorComLinhas(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.caixa_linhas = tk.Text(
            self,
            width=4,
            bg="#1a1a1a",
            fg="#666666",
            font=("Consolas", 14),
            state="disabled",
            borderwidth=0,
            highlightthickness=0,
            pady=7,
        )
        self.caixa_linhas.grid(row=0, column=0, sticky="ns", padx=(5, 0))

        self.caixa_texto = ctk.CTkTextbox(self, font=("Consolas", 14), wrap="none")
        self.caixa_texto.grid(row=0, column=1, sticky="nsew")
        self.caixa_texto._textbox.configure(undo=True, autoseparators=True, maxundo=-1)

        self.palavras_chave = ["MoveTo()", "MovePose()", "Wait()", "metodo ", "setup:", "loop:"]

        self.caixa_texto.bind("<Tab>", self.autocompletar_ou_identar)
        self.caixa_texto.bind("<Return>", self.auto_identar_enter)
        self.caixa_texto.bind("<BackSpace>", self.smart_backspace)

        eventos = ["<KeyRelease>", "<MouseWheel>", "<Control-v>", "<Control-z>"]
        for ev in eventos:
            self.caixa_texto.bind(ev, self.processar_eventos)

        self._orig_yscroll = self.caixa_texto._textbox.cget("yscrollcommand")
        self.caixa_texto._textbox.configure(yscrollcommand=self._sync_scroll)

        self._atualizar_numeros()
        self.configurar_cores()

    def smart_backspace(self, event):
        txt = self.caixa_texto._textbox
        pos_atual = txt.index("insert")
        linha, col = pos_atual.split(".")
        col = int(col)

        if col > 0:
            texto_antes = txt.get(f"{linha}.0", pos_atual)
            if texto_antes.isspace() and len(texto_antes) == col:
                txt.delete(f"{linha}.0", pos_atual)
                self.processar_eventos()
                return "break"

        self.processar_eventos()

    def auto_identar_enter(self, event):
        txt = self.caixa_texto._textbox
        pos_atual = txt.index("insert")
        linha = pos_atual.split(".")[0]
        texto_linha = txt.get(f"{linha}.0", f"{linha}.end")

        match_espacos = re.match(r"^(\s*)", texto_linha)
        espacos = match_espacos.group(1) if match_espacos else ""

        txt.insert("insert", "\n" + espacos)
        self.processar_eventos()
        return "break"

    def autocompletar_ou_identar(self, event):
        txt = self.caixa_texto._textbox
        pos_atual = txt.index("insert")
        linha = pos_atual.split(".")[0]
        texto_linha = txt.get(f"{linha}.0", pos_atual)

        match = re.search(r"([a-zA-Z_0-9]+[\(]*)$", texto_linha)
        if match:
            palavra_atual_raw = match.group(1)
            palavra_limpa = palavra_atual_raw.replace("(", "")

            texto_completo = txt.get("1.0", "end")
            nomes_metodos = []
            for m in re.finditer(r"metodo\s+([a-zA-Z0-9_]+)\s*:", texto_completo, re.IGNORECASE):
                nomes_metodos.append(m.group(1))

            todas_palavras = self.palavras_chave + nomes_metodos

            sugestoes_limpas = [s.replace("()", "") for s in getattr(self, "_sugestoes_atuais", [])]
            if hasattr(self, "_sugestoes_atuais") and palavra_limpa in sugestoes_limpas:
                self._indice_sugestao = (self._indice_sugestao + 1) % len(self._sugestoes_atuais)
                sugestao = self._sugestoes_atuais[self._indice_sugestao]

                inicio_palavra = f"{pos_atual} - {len(palavra_atual_raw)} chars"
                txt.delete(inicio_palavra, pos_atual)
                if txt.get("insert", "insert+1c") == ")":
                    txt.delete("insert", "insert+1c")
                txt.insert("insert", sugestao)
                if sugestao.endswith("()"):
                    txt.mark_set("insert", "insert-1c")
                self.processar_eventos()
                return "break"

            sugestoes = [p for p in todas_palavras if p.lower().startswith(palavra_limpa.lower())]
            if sugestoes:
                self._sugestoes_atuais = sugestoes
                self._indice_sugestao = 0
                sugestao = sugestoes[0]

                inicio_palavra = f"{pos_atual} - {len(palavra_atual_raw)} chars"
                txt.delete(inicio_palavra, pos_atual)
                if txt.get("insert", "insert+1c") == ")":
                    txt.delete("insert", "insert+1c")

                txt.insert("insert", sugestao)
                if sugestao.endswith("()"):
                    txt.mark_set("insert", "insert-1c")

                self.processar_eventos()
                return "break"

        if hasattr(self, "_sugestoes_atuais"):
            self._sugestoes_atuais = []

        txt.insert("insert", "    ")
        self.processar_eventos()
        return "break"

    def configurar_cores(self):
        txt = self.caixa_texto._textbox
        txt.tag_config("comando", foreground="#569CD6", font=("Consolas", 14, "bold"))
        txt.tag_config("numero", foreground="#B5CEA8")
        txt.tag_config("comentario", foreground="#6A9955", font=("Consolas", 14, "italic"))
        txt.tag_config("estrutura", foreground="#C586C0", font=("Consolas", 14, "bold"))
        txt.tag_config("funcao", foreground="#DCDCAA", font=("Consolas", 14))

    def processar_eventos(self, event=None):
        self.after(1, self._atualizar_numeros)
        self.after(2, self.colorir_sintaxe)

    def colorir_sintaxe(self):
        txt = self.caixa_texto._textbox
        texto_completo = txt.get("1.0", "end")

        for tag in ["comando", "numero", "comentario", "estrutura", "funcao"]:
            txt.tag_remove(tag, "1.0", "end")

        for match in re.finditer(r"\b(MoveTo|Wait|MovePose)\b", texto_completo):
            txt.tag_add("comando", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

        for match in re.finditer(r"\b(metodo|setup:|loop:)\b", texto_completo):
            txt.tag_add("estrutura", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

        for match in re.finditer(r"\b\d+\b", texto_completo):
            txt.tag_add("numero", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

        for match in re.finditer(r"//.*", texto_completo):
            txt.tag_add("comentario", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

        nomes_metodos = []
        for match in re.finditer(r"metodo\s+([a-zA-Z0-9_]+)\s*:", texto_completo, re.IGNORECASE):
            txt.tag_add("funcao", f"1.0 + {match.start(1)} chars", f"1.0 + {match.end(1)} chars")
            nomes_metodos.append(match.group(1))

        if nomes_metodos:
            nomes_metodos.sort(key=len, reverse=True)
            padrao = r"\b(" + "|".join(re.escape(n) for n in nomes_metodos) + r")\b"
            for match in re.finditer(padrao, texto_completo):
                txt.tag_add("funcao", f"1.0 + {match.start()} chars", f"1.0 + {match.end()} chars")

    def _sync_scroll(self, *args):
        if self._orig_yscroll:
            self.tk.call(self._orig_yscroll, *args)
        self.caixa_linhas.yview_moveto(args[0])

    def _atualizar_numeros(self):
        qtd = int(self.caixa_texto.index("end-1c").split(".")[0])
        self.caixa_linhas.configure(state="normal")
        self.caixa_linhas.delete("1.0", "end")
        self.caixa_linhas.insert("1.0", "\n".join(str(i) for i in range(1, qtd + 1)))
        self.caixa_linhas.configure(state="disabled")
        self.caixa_linhas.yview_moveto(self.caixa_texto._textbox.yview()[0])

    def get(self, *args, **kwargs):
        return self.caixa_texto.get(*args, **kwargs)

    def insert(self, *args, **kwargs):
        self.caixa_texto.insert(*args, **kwargs)
        self.processar_eventos()

    def delete(self, *args, **kwargs):
        self.caixa_texto.delete(*args, **kwargs)
        self.processar_eventos()

    def index(self, *args, **kwargs):
        return self.caixa_texto.index(*args, **kwargs)

    def configure(self, **kwargs):
        if "state" in kwargs:
            self.caixa_texto.configure(state=kwargs["state"])
        else:
            super().configure(**kwargs)


class DicionarioComandos(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color="gray15", corner_radius=10)

        ctk.CTkLabel(
            self,
            text="📖 SINTAXE ROBIX",
            font=("Arial", 11, "bold"),
            text_color="#1f538d",
        ).pack(pady=10)

        cmds = [
            ("MoveTo(M, A)", "M:1-6 | A:0-180"),
            ("MovePose(...)", "B, O, C, P, R, G"),
            ("Wait(MS)", "Pausa em ms"),
            ("setup:\n    // Roda uma vez", "Configuração Inicial"),
            ("loop:\n    // Roda infinito", "Laço Principal"),
            ("metodo NOME:\n    // Comandos", "Função Customizada"),
            ("// Comentário", "Ignorado pelo robô"),
        ]

        for c, d in cmds:
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.pack(fill="x", padx=10, pady=3)

            ctk.CTkLabel(
                f,
                text=c,
                font=("Consolas", 10, "bold"),
                text_color="yellow",
                justify="left",
            ).pack(anchor="w")

            ctk.CTkLabel(
                f,
                text=d,
                font=("Arial", 9),
                text_color="gray70",
                justify="left",
            ).pack(anchor="w")
