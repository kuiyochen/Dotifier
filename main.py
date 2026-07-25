import base64
import ctypes
import logging
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from controller import DotifierController
from model import DotifierModel
from view import DotifierView


ICON_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAMAAAAM7l6QAAAATlBMVEVHcEwAAAAAAAAAAAAAAAABAQEAAAAAAAAAAAABAQEAAAAAAAAAAAAAAAABAQEAAAAAAAABAQEBAQEBAQEBAQEAAAAAAAABAQECAgIAAADSzu12AAAAGXRSTlMA/Ofw3w/3Y3dUiaTSsBgix5EzQLuaSSoG6PwvWgAAARpJREFUKM+Vk1mShSAMRZkRZBJxYP8bbYqAvGdpVzc/GA8JNwMI/X05uW3SvdEYclnpePGtNGfLH7EEmsV+JzxGh3TDeUIuxhHilIFSI5cLT4bSoDqeRI1pcAsOH1QCPQj8xgy2ZmbjviTlZSEYMz03E0P4qWPtNCUT7zhDdIW7dyoihO1YrFAOAyZtlzIKe2q57VUTs135XM+Z2DM7Fsa2OMqyzsxof9WlmMSuA++WlOOdqhqMXMFtvZyBMuS7NNakCdgDvyU2Fze6zd+dG2XhT2W5iro9evt2Z+/FrSVIVqU0NA04VG3karhKjCQ1xkEGwuw6hun0nn8OE/f+vA9cT1Csj5PK06+DjI5U/LH1b8+EK60V/8er+wGQ+CckYtym0AAAAABJRU5ErkJggg=="


def configure_error_logging() -> None:
    """Write application exceptions and Qt errors to Dotifier.log."""
    logging.getLogger().setLevel(logging.ERROR)
    handler = logging.FileHandler(Path(__file__).resolve().parent / "Dotifier.log", encoding="utf-8")
    handler.setLevel(logging.ERROR)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s\n%(message)s"))
    logging.getLogger().addHandler(handler)

    def log_unhandled_exception(exc_type, exc_value, exc_traceback) -> None:
        logging.getLogger(__name__).error(
            "Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    def log_thread_exception(args: threading.ExceptHookArgs) -> None:
        logging.getLogger(__name__).error(
            "Unhandled thread exception", exc_info=(args.exc_type, args.exc_value, args.exc_traceback)
        )

    def log_qt_message(message_type, _context, message) -> None:
        if message_type in (QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            logging.getLogger("Qt").error("%s", message)

    sys.excepthook = log_unhandled_exception
    threading.excepthook = log_thread_exception
    qInstallMessageHandler(log_qt_message)


def main() -> int:
    configure_error_logging()
    app = QApplication(sys.argv)
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FablabTainan.Dotifier.1.0")
    except AttributeError:
        pass
    pixmap = QPixmap(); pixmap.loadFromData(base64.b64decode(ICON_BASE64))
    icon = QIcon(pixmap); app.setWindowIcon(icon)
    model = DotifierModel()
    view = DotifierView(); view.setWindowIcon(icon)
    controller = DotifierController(model, view)
    view._controller = controller  # retain controller for the application's lifetime
    view.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
