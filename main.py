import base64
import ctypes
import sys

from PySide2.QtGui import QIcon, QPixmap
from PySide2.QtWidgets import QApplication

from controller import DotifierController
from model import DotifierModel
from view import DotifierView


ICON_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAB4AAAAeCAMAAAAM7l6QAAAATlBMVEVHcEwAAAAAAAAAAAAAAAABAQEAAAAAAAAAAAABAQEAAAAAAAAAAAAAAAABAQEAAAAAAAABAQEBAQEBAQEBAQEAAAAAAAABAQECAgIAAADSzu12AAAAGXRSTlMA/Ofw3w/3Y3dUiaTSsBgix5EzQLuaSSoG6PwvWgAAARpJREFUKM+Vk1mShSAMRZkRZBJxYP8bbYqAvGdpVzc/GA8JNwMI/X05uW3SvdEYclnpePGtNGfLH7EEmsV+JzxGh3TDeUIuxhHilIFSI5cLT4bSoDqeRI1pcAsOH1QCPQj8xgy2ZmbjviTlZSEYMz03E0P4qWPtNCUT7zhDdIW7dyoihO1YrFAOAyZtlzIKe2q57VUTs135XM+Z2DM7Fsa2OMqyzsxof9WlmMSuA++WlOOdqhqMXMFtvZyBMuS7NNakCdgDvyU2Fze6zd+dG2XhT2W5iro9evt2Z+/FrSVIVqU0NA04VG3karhKjCQ1xkEGwuw6hun0nn8OE/f+vA9cT1Csj5PK06+DjI5U/LH1b8+EK60V/8er+wGQ+CckYtym0AAAAABJRU5ErkJggg=="


def main() -> int:
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
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
