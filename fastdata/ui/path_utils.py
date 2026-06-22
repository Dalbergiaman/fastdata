from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets


def _dialog_parent(widget: QtWidgets.QWidget | None) -> QtWidgets.QWidget | None:
    if widget is None:
        return QtWidgets.QApplication.activeWindow()
    return widget.window() or QtWidgets.QApplication.activeWindow() or widget


LIGHT_DIALOG_STYLESHEET = """
QDialog, QWidget {
    background: #f7f7f8;
    color: #111111;
}
QLabel {
    color: #111111;
}
QLineEdit, QTreeView, QHeaderView::section {
    background: #ffffff;
    color: #111111;
    border: 1px solid #c8ccd3;
}
QPushButton {
    background: #ffffff;
    color: #111111;
    border: 1px solid #c8ccd3;
    padding: 5px 10px;
}
QPushButton:hover {
    background: #eef3f8;
}
"""


class FolderPickerDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None, initial_path: str = "") -> None:
        super().__init__(parent)
        self.setWindowTitle("Select Folder")
        self.resize(820, 560)
        self.setStyleSheet(LIGHT_DIALOG_STYLESHEET)

        start_path = Path(initial_path).expanduser() if initial_path.strip() else Path.home()
        if start_path.is_file():
            start_path = start_path.parent
        if not start_path.exists():
            start_path = Path.home()

        self.model = QtWidgets.QFileSystemModel(self)
        self.model.setRootPath(str(start_path))
        self.model.setFilter(
            QtCore.QDir.AllDirs
            | QtCore.QDir.Files
            | QtCore.QDir.NoDotAndDotDot
            | QtCore.QDir.Readable
        )

        self.path_edit = QtWidgets.QLineEdit(str(start_path), self)
        self.path_edit.returnPressed.connect(self._select_typed_path)

        self.tree = QtWidgets.QTreeView(self)
        self.tree.setModel(self.model)
        self.tree.setRootIndex(self.model.index(str(start_path)))
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(0, QtCore.Qt.AscendingOrder)
        self.tree.doubleClicked.connect(self._handle_double_click)
        self.tree.selectionModel().currentChanged.connect(self._handle_current_changed)
        self.tree.setColumnWidth(0, 320)

        browse_home = QtWidgets.QPushButton("Home", self)
        browse_home.clicked.connect(lambda: self._set_current_folder(str(Path.home())))
        up_button = QtWidgets.QPushButton("Up", self)
        up_button.clicked.connect(self._go_up)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        top = QtWidgets.QHBoxLayout()
        top.addWidget(QtWidgets.QLabel("Folder:", self))
        top.addWidget(self.path_edit, 1)
        top.addWidget(up_button)
        top.addWidget(browse_home)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addLayout(top)
        layout.addWidget(self.tree, 1)
        layout.addWidget(buttons)

    def selected_folder(self) -> str:
        path = Path(self.path_edit.text()).expanduser()
        if path.is_file():
            path = path.parent
        return str(path)

    def _handle_current_changed(self, current: QtCore.QModelIndex) -> None:
        path = Path(self.model.filePath(current))
        if path.is_file():
            path = path.parent
        self.path_edit.setText(str(path))

    def _handle_double_click(self, index: QtCore.QModelIndex) -> None:
        path = Path(self.model.filePath(index))
        if path.is_dir():
            self._set_current_folder(str(path))
        else:
            self.path_edit.setText(str(path.parent))

    def _select_typed_path(self) -> None:
        path = Path(self.path_edit.text()).expanduser()
        if path.is_file():
            path = path.parent
        if path.exists():
            self._set_current_folder(str(path))

    def _set_current_folder(self, folder: str) -> None:
        index = self.model.index(folder)
        if not index.isValid():
            return
        self.tree.setRootIndex(index)
        self.path_edit.setText(folder)

    def _go_up(self) -> None:
        path = Path(self.path_edit.text()).expanduser()
        if path.is_file():
            path = path.parent
        parent = path.parent
        if parent != path and parent.exists():
            self._set_current_folder(str(parent))
def choose_folder(parent: QtWidgets.QWidget, initial_path: str = "") -> str:
    dialog = FolderPickerDialog(_dialog_parent(parent), initial_path)
    if dialog.exec() != QtWidgets.QDialog.Accepted:
        return ""
    return dialog.selected_folder()


def open_path(parent: QtWidgets.QWidget, path_text: str) -> bool:
    dialog_parent = _dialog_parent(parent)
    path = Path(path_text).expanduser()
    if not path_text.strip():
        QtWidgets.QMessageBox.information(dialog_parent, "Open Folder", "Current path is empty.")
        return False
    if not path.exists():
        QtWidgets.QMessageBox.warning(dialog_parent, "Open Folder", f"Path does not exist:\n{path}")
        return False
    return QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))
