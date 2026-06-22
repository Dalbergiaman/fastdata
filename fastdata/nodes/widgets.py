from PySide6 import QtCore, QtWidgets
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget

from fastdata.ui.path_utils import choose_folder, open_path


class FolderPathWidget(NodeBaseWidget):
    def __init__(self, parent=None, name: str = "folder_path", label: str = "Folder", path: str = "") -> None:
        super().__init__(parent, name, label)
        container = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.editor = QtWidgets.QLineEdit(path)
        self.editor.setMinimumWidth(210)
        self.editor.setPlaceholderText("Folder path")
        self.editor.editingFinished.connect(self.on_value_changed)

        browse_button = QtWidgets.QPushButton("...")
        browse_button.setFixedSize(28, 24)
        browse_button.setToolTip("Choose folder")
        browse_button.pressed.connect(self.choose_folder)

        open_button = QtWidgets.QPushButton(">")
        open_button.setFixedSize(28, 24)
        open_button.setToolTip("Open current folder")
        open_button.pressed.connect(lambda: open_path(container, self.get_value()))

        layout.addWidget(self.editor, 1)
        layout.addWidget(browse_button)
        layout.addWidget(open_button)
        self.set_custom_widget(container)
        container.setAttribute(QtCore.Qt.WA_Hover, True)
        self.setAcceptedMouseButtons(QtCore.Qt.LeftButton)

    def get_value(self) -> str:
        return self.editor.text()

    def set_value(self, path: str) -> None:
        if self.editor.text() == path:
            return
        blocker = QtCore.QSignalBlocker(self.editor)
        self.editor.setText(path)
        del blocker

    def choose_folder(self) -> None:
        folder = choose_folder(self.editor, self.get_value())
        if not folder:
            return
        self.editor.setText(folder)
        self.on_value_changed()

    def mousePressEvent(self, event) -> None:
        event.accept()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        event.accept()
        super().mouseReleaseEvent(event)


class PromptTextWidget(NodeBaseWidget):
    def __init__(self, parent=None, name: str = "prompt_text", label: str = "Prompt", text: str = "") -> None:
        super().__init__(parent, name, label)
        editor = QtWidgets.QPlainTextEdit()
        editor.setPlainText(text)
        editor.setMinimumSize(260, 160)
        editor.setPlaceholderText("Prompt")
        editor.textChanged.connect(self.on_value_changed)
        self.set_custom_widget(editor)

    def get_value(self) -> str:
        return self.get_custom_widget().toPlainText()

    def set_value(self, text: str) -> None:
        editor = self.get_custom_widget()
        if editor.toPlainText() == text:
            return
        blocker = QtCore.QSignalBlocker(editor)
        editor.setPlainText(text)
        del blocker
