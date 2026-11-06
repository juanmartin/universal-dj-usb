import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest

qt_widgets = pytest.importorskip("PySide6.QtWidgets")
QApplication = qt_widgets.QApplication
QLabel = qt_widgets.QLabel

from universal_dj_usb import __version__
from universal_dj_usb.gui import AboutDialog


def test_about_dialog_has_repository_and_signature_links() -> None:
    app = QApplication.instance() or QApplication([])
    dialog = AboutDialog()
    text = "\n".join(label.text() for label in dialog.findChildren(QLabel))

    assert "Universal DJ USB" in text
    assert f"Version {__version__}" in text
    assert "Hecho con amor, pasión, y desinterés por" in text
    assert 'href="https://soundcloud.com/jaunmatrin"' in text
    assert 'href="https://github.com/juanmartin/universal-dj-usb"' in text

    dialog.close()
    app.quit()
