import runpy
from unittest.mock import Mock

import customtkinter as ctk

from suri_edu import app


def test_bootstrap_configura_tema_e_inicia_loop(monkeypatch):
    window = Mock()
    factory = Mock(return_value=window)
    set_appearance_mode = Mock()
    set_default_color_theme = Mock()
    monkeypatch.setattr(app, "RobixSupervisorio", factory)
    monkeypatch.setattr(ctk, "set_appearance_mode", set_appearance_mode)
    monkeypatch.setattr(ctk, "set_default_color_theme", set_default_color_theme)

    runpy.run_module("main", run_name="__main__")

    set_appearance_mode.assert_called_once_with("Dark")
    set_default_color_theme.assert_called_once_with("blue")
    factory.assert_called_once_with()
    window.mainloop.assert_called_once_with()


def test_bootstrap_registra_falha_no_log(monkeypatch, caplog):
    monkeypatch.setattr(app, "RobixSupervisorio", Mock(side_effect=RuntimeError("falha")))

    runpy.run_module("main", run_name="__main__")

    assert "Falha ao iniciar o supervisorio" in caplog.text
