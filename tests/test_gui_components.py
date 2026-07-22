from types import SimpleNamespace
from unittest.mock import Mock, call

from suri_edu import gui_components
from suri_edu.gui_components import EditorComLinhas, ToolTip


def test_tooltip_registra_bindings_e_evitar_duplicacao(monkeypatch):
    widget = SimpleNamespace(
        bind=Mock(),
        winfo_rootx=Mock(return_value=10),
        winfo_rooty=Mock(return_value=20),
        winfo_height=Mock(return_value=30),
    )
    window = SimpleNamespace(wm_overrideredirect=Mock(), wm_geometry=Mock(), destroy=Mock())
    label = SimpleNamespace(pack=Mock())
    monkeypatch.setattr(gui_components.tk, "Toplevel", Mock(return_value=window))
    monkeypatch.setattr(gui_components.tk, "Label", Mock(return_value=label))

    tooltip = ToolTip(widget, "Ajuda")
    tooltip.show_tip()
    tooltip.show_tip()
    tooltip.hide_tip()

    assert widget.bind.call_args_list == [
        call("<Enter>", tooltip.show_tip),
        call("<Leave>", tooltip.hide_tip),
    ]
    window.wm_geometry.assert_called_once_with("+30+55")
    window.destroy.assert_called_once_with()
    assert tooltip.tip_window is None


def test_tooltip_vazio_nao_cria_janela(monkeypatch):
    widget = SimpleNamespace(bind=Mock())
    toplevel = Mock()
    monkeypatch.setattr(gui_components.tk, "Toplevel", toplevel)

    ToolTip(widget, "").show_tip()

    toplevel.assert_not_called()


def test_editor_delega_operacoes_e_processa_mutacoes():
    editor = EditorComLinhas.__new__(EditorComLinhas)
    editor.caixa_texto = Mock()
    editor.processar_eventos = Mock()

    editor.caixa_texto.get.return_value = "texto"
    editor.caixa_texto.index.return_value = "1.0"

    assert editor.get("1.0", "end") == "texto"
    assert editor.index("insert") == "1.0"
    editor.insert("1.0", "abc")
    editor.delete("1.0", "end")

    editor.caixa_texto.insert.assert_called_once_with("1.0", "abc")
    editor.caixa_texto.delete.assert_called_once_with("1.0", "end")
    assert editor.processar_eventos.call_count == 2


def test_editor_configure_state_configura_apenas_textbox():
    editor = EditorComLinhas.__new__(EditorComLinhas)
    editor.caixa_texto = Mock()

    editor.configure(state="disabled", width=200)

    editor.caixa_texto.configure.assert_called_once_with(state="disabled")


def test_processar_eventos_agenda_numeracao_e_cores():
    editor = EditorComLinhas.__new__(EditorComLinhas)
    editor.after = Mock()
    editor._atualizar_numeros = Mock()
    editor.colorir_sintaxe = Mock()

    editor.processar_eventos()

    assert editor.after.call_args_list == [
        call(1, editor._atualizar_numeros),
        call(2, editor.colorir_sintaxe),
    ]


class FakeText:
    def __init__(self, line="", position="1.0"):
        self.line = line
        self.position = position
        self.operations = []

    def index(self, index):
        return self.position

    def get(self, start, end):
        if start == "1.0" and end in {self.position, "1.end"}:
            return self.line
        if start == "1.0" and end == "end":
            return self.line
        return ""

    def delete(self, start, end):
        self.operations.append(("delete", start, end))

    def insert(self, index, text):
        self.operations.append(("insert", index, text))

    def mark_set(self, mark, index):
        self.operations.append(("mark_set", mark, index))


def test_smart_backspace_remove_toda_indentacao():
    editor = EditorComLinhas.__new__(EditorComLinhas)
    editor.caixa_texto = SimpleNamespace(_textbox=FakeText("    ", "1.4"))
    editor.processar_eventos = Mock()

    result = editor.smart_backspace(None)

    assert result == "break"
    assert editor.caixa_texto._textbox.operations == [("delete", "1.0", "1.4")]


def test_auto_identar_preserva_indentacao_atual():
    editor = EditorComLinhas.__new__(EditorComLinhas)
    editor.caixa_texto = SimpleNamespace(_textbox=FakeText("    MoveTo", "1.10"))
    editor.processar_eventos = Mock()

    result = editor.auto_identar_enter(None)

    assert result == "break"
    assert editor.caixa_texto._textbox.operations == [("insert", "insert", "\n    ")]


def test_autocomplete_completa_comando_e_posiciona_cursor():
    editor = EditorComLinhas.__new__(EditorComLinhas)
    editor.caixa_texto = SimpleNamespace(_textbox=FakeText("Mov", "1.3"))
    editor.palavras_chave = ["MoveTo()", "MovePose()"]
    editor.processar_eventos = Mock()

    result = editor.autocompletar_ou_identar(None)

    assert result == "break"
    assert editor.caixa_texto._textbox.operations == [
        ("delete", "1.3 - 3 chars", "1.3"),
        ("insert", "insert", "MoveTo()"),
        ("mark_set", "insert", "insert-1c"),
    ]


def test_autocomplete_insere_quatro_espacos_sem_sugestao():
    editor = EditorComLinhas.__new__(EditorComLinhas)
    editor.caixa_texto = SimpleNamespace(_textbox=FakeText("", "1.0"))
    editor.palavras_chave = []
    editor.processar_eventos = Mock()

    editor.autocompletar_ou_identar(None)

    assert editor.caixa_texto._textbox.operations == [("insert", "insert", "    ")]
