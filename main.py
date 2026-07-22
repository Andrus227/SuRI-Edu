import logging

import customtkinter as ctk

from suri_edu.app import RobixSupervisorio

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    try:
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        app = RobixSupervisorio()
        app.mainloop()
    except Exception:
        logger.exception("Falha ao iniciar o supervisorio")
