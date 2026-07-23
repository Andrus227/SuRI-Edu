import json

from suri_edu.method_library import LIBRARY_VERSION, MethodLibrary


def test_biblioteca_salva_e_carrega_metodos(tmp_path):
    path = tmp_path / "dados" / "metodos.json"
    library = MethodLibrary(path)
    methods = {"Abrir": "metodo Abrir:\n    MoveTo(6, 30)\n"}

    library.save(methods)

    assert library.load() == methods
    assert json.loads(path.read_text(encoding="utf-8"))["version"] == LIBRARY_VERSION


def test_biblioteca_ausente_ou_invalida_retorna_vazia(tmp_path):
    path = tmp_path / "metodos.json"
    library = MethodLibrary(path)

    assert library.load() == {}
    path.write_text("{inválido", encoding="utf-8")
    assert library.load() == {}


def test_biblioteca_ignora_entradas_com_tipos_invalidos(tmp_path):
    path = tmp_path / "metodos.json"
    path.write_text(
        json.dumps({"methods": {"Valido": "metodo Valido:\n", "Invalido": 123}}),
        encoding="utf-8",
    )

    assert MethodLibrary(path).load() == {"Valido": "metodo Valido:\n"}
