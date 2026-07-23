from pathlib import Path

from suri_edu.help_content import HELP_TOPICS
from suri_edu.routine_examples import ROUTINE_EXAMPLES

ROOT = Path(__file__).parents[1]
DOCS = ROOT / "Instrucoes"


def test_manual_item_um_e_ajuda_integrada_informam_repositorio():
    repository = "https://github.com/Andrus227/SuRI-Edu"
    help_markdown = (DOCS / "HELP.md").read_text(encoding="utf-8")

    assert repository in help_markdown.split("## 2.", maxsplit=1)[0]
    assert repository in HELP_TOPICS["1. Visão Geral"]


def test_readme_documenta_contato_e_ativacao_por_terminal():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "André Victor Lucio" in readme
    assert "andrelucio.ifmt@gmail.com" in readme
    assert r".\.venv\Scripts\Activate.ps1" in readme
    assert r".venv\Scripts\activate.bat" in readme
    assert "source .venv/Scripts/activate" in readme


def test_documentacao_nao_trata_stop_como_emergencia_fisica():
    documents = [
        (ROOT / "README.md").read_text(encoding="utf-8"),
        (DOCS / "HELP.md").read_text(encoding="utf-8"),
        (DOCS / "PROTOCOL.md").read_text(encoding="utf-8"),
    ]

    for documentation in documents:
        assert "não substitu" in documentation
        assert "posição" in documentation
        assert "<ACK,STOP,id>" in documentation


def test_documentacao_registra_evolucoes_visuais_e_de_telemetria():
    manual = (DOCS / "HELP.md").read_text(encoding="utf-8")

    assert "telemetria" in manual
    assert "visualização esquemática ou 3D" in manual
    assert "estado desejado, comandado e confirmado" in manual


def test_documentacao_registra_contratos_operacionais_essenciais():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (DOCS / "HELP.md").read_text(encoding="utf-8")
    protocol = (DOCS / "PROTOCOL.md").read_text(encoding="utf-8")
    integrated_help = "\n".join(HELP_TOPICS.values())

    for documentation in (readme, manual, protocol, integrated_help):
        assert "90 graus" in documentation
        assert "115200" in documentation

    assert "1 segundo" in manual
    assert "FIFO" in protocol
    assert "31 bytes" in protocol
    assert "não é atômico" in manual
    assert "UTF-8" in manual


def test_catalogo_de_metodos_esta_documentado_nos_tres_manuais():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (DOCS / "HELP.md").read_text(encoding="utf-8")
    integrated_help = "\n".join(HELP_TOPICS.values())

    for example in ROUTINE_EXAMPLES:
        assert example.method_name in readme
        assert example.method_name in manual
        assert example.method_name in integrated_help


def test_documentacao_explica_biblioteca_persistente_e_execucao_dos_exemplos():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (DOCS / "HELP.md").read_text(encoding="utf-8")
    integrated_help = "\n".join(HELP_TOPICS.values())

    for documentation in (readme, manual, integrated_help):
        assert "~/.suri_edu/metodos.json" in documentation
        assert "F6" in documentation
        assert "F9" in documentation


def test_documentacao_explica_suavizacao_global_e_suas_excecoes():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    manual = (DOCS / "HELP.md").read_text(encoding="utf-8")
    protocol = (DOCS / "PROTOCOL.md").read_text(encoding="utf-8")

    for documentation in (readme, manual, protocol):
        assert "aceleração" in documentation
        assert "firmware" in documentation
        assert "STOP" in documentation
        assert "90 graus" in documentation

    examples_help = HELP_TOPICS["7. Exemplos"]
    assert "aceleração" in examples_help
    assert "frenagem" in examples_help
    assert "passos intermediários" in examples_help
