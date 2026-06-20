from PySide6 import QtCore, QtWidgets
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget


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
