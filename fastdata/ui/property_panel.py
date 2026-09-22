from typing import Any

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from fastdata.nodes.base import FastDataNode


MODEL_CHOICES = [
    "nano-banana",
    "nano-banana-fast",
    "nano-banana-2",
    "nano-banana-2-cl",
    "nano-banana-2-4k-cl",
    "nano-banana-pro",
    "nano-banana-pro-cl",
    "nano-banana-pro-vip",
    "nano-banana-pro-4k-vip",
]

ASPECT_RATIO_CHOICES = [
    "auto",
    "1:1",
    "16:9",
    "9:16",
    "4:3",
    "3:4",
    "3:2",
    "2:3",
    "5:4",
    "4:5",
    "21:9",
    "1:4",
    "4:1",
    "1:8",
    "8:1",
]

GPT_ASPECT_RATIO_CHOICES = [
    "1024x1024",
    "1024x1792",
    "1792x1024",
    "2048x2048",
    "1:1",
    "16:9",
    "9:16",
    "4:3",
    "3:4",
    "3:2",
    "2:3",
]


NODE_PARAMETER_SCHEMAS = {
    "Path Input": [
        {"key": "folder_path", "label": "Folder Path", "type": "path"},
    ],
    "Prompt Input": [
        {"key": "prompt_text", "label": "Prompt", "type": "multiline"},
    ],
    "Output Folder": [
        {"key": "folder_path", "label": "Folder Path", "type": "path"},
    ],
    "img2img-banana": [
        {"key": "model", "label": "Model", "type": "model"},
        {"key": "aspect_ratio", "label": "Aspect Ratio", "type": "aspect_ratio"},
        {"key": "image_size", "label": "Image Size", "type": "choice", "choices": ["1K", "2K", "4K"]},
        {"key": "only_missing", "label": "Only Missing", "type": "bool"},
    ],
    "img2img-gpt": [
        {"key": "model", "label": "Model", "type": "choice", "choices": ["gpt-image-2", "gpt-image-2-vip"]},
        {"key": "aspect_ratio", "label": "Aspect Ratio", "type": "choice", "choices": GPT_ASPECT_RATIO_CHOICES},
        {"key": "only_missing", "label": "Only Missing", "type": "bool"},
    ],
    "Reference Img2Img": [
        {"key": "reference_image_path", "label": "Reference Image", "type": "file_path"},
        {"key": "model", "label": "Model", "type": "model"},
        {"key": "aspect_ratio", "label": "Aspect Ratio", "type": "aspect_ratio"},
        {"key": "image_size", "label": "Image Size", "type": "choice", "choices": ["1K", "2K", "4K"]},
        {"key": "only_missing", "label": "Only Missing", "type": "bool"},
    ],
    "Text2Img": [
        {"key": "model", "label": "Model", "type": "model"},
        {"key": "aspect_ratio", "label": "Aspect Ratio", "type": "aspect_ratio"},
        {"key": "image_size", "label": "Image Size", "type": "choice", "choices": ["1K", "2K", "4K"]},
        {"key": "count", "label": "Count", "type": "int", "minimum": 1, "maximum": 10000},
    ],
    "Image To PNG": [
        {"key": "overwrite", "label": "Overwrite", "type": "bool"},
    ],
    "Image To JPG": [
        {"key": "quality", "label": "Quality", "type": "int", "minimum": 1, "maximum": 100},
        {"key": "overwrite", "label": "Overwrite", "type": "bool"},
    ],
    "Resize To Reference": [
        {"key": "overwrite", "label": "Overwrite", "type": "bool"},
    ],
    "Resize Image": [
        {"key": "target_width", "label": "Width", "type": "int", "minimum": 1, "maximum": 16384},
        {"key": "target_height", "label": "Height", "type": "int", "minimum": 1, "maximum": 16384},
        {"key": "output_format", "label": "Output Format", "type": "choice", "choices": ["png", "jpg", "keep"]},
        {"key": "resize_mode", "label": "Resize Mode", "type": "choice", "choices": ["stretch", "fit", "fill_crop"]},
        {"key": "overwrite", "label": "Overwrite", "type": "bool"},
    ],
    "Prompt Batch Generate": [
        {"key": "count", "label": "Count", "type": "int", "minimum": 1, "maximum": 100000},
        {"key": "filename_prefix", "label": "Filename Prefix", "type": "text"},
    ],
}


class PropertyPanel(QtWidgets.QFrame):
    propertyChanged = QtCore.Signal()

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("SidePanel")
        self._node: FastDataNode | None = None

        self._layout = QtWidgets.QVBoxLayout(self)
        self._layout.setContentsMargins(14, 14, 14, 14)
        self._layout.setSpacing(10)

        title = QtWidgets.QLabel("Properties", self)
        title.setObjectName("PanelTitle")
        self._layout.addWidget(title)

        self._body = QtWidgets.QWidget(self)
        self._form = QtWidgets.QFormLayout(self._body)
        self._form.setContentsMargins(0, 0, 0, 0)
        self._form.setSpacing(10)
        self._form.setLabelAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)
        self._layout.addWidget(self._body)

        self._placeholder = QtWidgets.QLabel("Select a node to edit its parameters.", self)
        self._placeholder.setObjectName("MutedText")
        self._placeholder.setWordWrap(True)
        self._layout.addWidget(self._placeholder)
        self._layout.addStretch(1)

        self.set_node(None)

    def set_node(self, node: FastDataNode | None) -> None:
        self._node = node
        self._clear_form()

        if node is None:
            self._body.hide()
            self._placeholder.show()
            return

        self._placeholder.hide()
        self._body.show()

        node_type_name = getattr(type(node), "NODE_NAME", node.name())
        schema = NODE_PARAMETER_SCHEMAS.get(node_type_name, [])
        if not schema:
            note = QtWidgets.QLabel("No editable parameters for this node.", self._body)
            note.setObjectName("MutedText")
            note.setWordWrap(True)
            self._form.addRow(note)
            return

        for field in schema:
            self._add_field(field)

    def _clear_form(self) -> None:
        while self._form.rowCount():
            self._form.removeRow(0)

    def _clear_layout(self, layout: QtWidgets.QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)

    def _add_field(self, field: dict[str, Any]) -> None:
        key = field["key"]
        value = "" if self._node is None else self._node.get_property(key) or ""
        field_type = field["type"]

        if field_type == "path":
            widget = self._build_path_field(key, str(value))
        elif field_type == "file_path":
            widget = self._build_file_path_field(key, str(value))
        elif field_type == "password":
            widget = self._build_text_field(key, str(value), password=True)
        elif field_type == "model":
            widget = self._build_choice_field(key, str(value), MODEL_CHOICES)
        elif field_type == "aspect_ratio":
            widget = self._build_choice_field(key, str(value), ASPECT_RATIO_CHOICES)
        elif field_type == "choice":
            widget = self._build_choice_field(key, str(value), field["choices"])
        elif field_type == "int":
            widget = self._build_int_field(key, int(value), field["minimum"], field["maximum"])
        elif field_type == "bool":
            widget = self._build_bool_field(key, bool(value))
        elif field_type == "multiline":
            widget = self._build_multiline_field(key, str(value))
        else:
            widget = self._build_text_field(key, str(value))

        self._form.addRow(field["label"], widget)

    def _build_text_field(self, key: str, value: str, password: bool = False) -> QtWidgets.QLineEdit:
        editor = QtWidgets.QLineEdit(value, self._body)
        if password:
            editor.setEchoMode(QtWidgets.QLineEdit.Password)
        editor.editingFinished.connect(lambda: self._set_node_property(key, editor.text()))
        return editor

    def _build_multiline_field(self, key: str, value: str) -> QtWidgets.QPlainTextEdit:
        editor = QtWidgets.QPlainTextEdit(value, self._body)
        editor.setMinimumHeight(140)
        editor.textChanged.connect(lambda: self._set_node_property(key, editor.toPlainText()))
        return editor

    def _build_choice_field(self, key: str, value: str, choices: list[str]) -> QtWidgets.QComboBox:
        editor = QtWidgets.QComboBox(self._body)
        editor.addItems(choices)
        if value in choices:
            editor.setCurrentText(value)
        editor.currentTextChanged.connect(lambda text: self._set_node_property(key, text))
        return editor

    def _build_int_field(self, key: str, value: int, minimum: int, maximum: int) -> QtWidgets.QSpinBox:
        editor = QtWidgets.QSpinBox(self._body)
        editor.setRange(minimum, maximum)
        editor.setValue(value)
        editor.valueChanged.connect(lambda number: self._set_node_property(key, number))
        return editor

    def _build_bool_field(self, key: str, value: bool) -> QtWidgets.QCheckBox:
        editor = QtWidgets.QCheckBox(self._body)
        editor.setChecked(value)
        editor.toggled.connect(lambda checked: self._set_node_property(key, checked))
        return editor

    def _build_path_field(self, key: str, value: str) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget(self._body)
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        editor = QtWidgets.QLineEdit(value, container)
        editor.editingFinished.connect(lambda: self._set_node_property(key, editor.text()))
        button = QtWidgets.QPushButton("Browse", container)
        button.clicked.connect(lambda: self._choose_folder(key, editor))
        open_button = QtWidgets.QPushButton("Open", container)
        open_button.clicked.connect(lambda: self._open_folder(editor.text()))

        layout.addWidget(editor, 1)
        layout.addWidget(button)
        layout.addWidget(open_button)
        return container

    def _build_file_path_field(self, key: str, value: str) -> QtWidgets.QWidget:
        container = QtWidgets.QWidget(self._body)
        layout = QtWidgets.QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        editor = QtWidgets.QLineEdit(value, container)
        editor.editingFinished.connect(lambda: self._set_node_property(key, editor.text()))
        button = QtWidgets.QPushButton("Browse", container)
        button.clicked.connect(lambda: self._choose_file(key, editor))

        layout.addWidget(editor, 1)
        layout.addWidget(button)
        return container

    def _choose_folder(self, key: str, editor: QtWidgets.QLineEdit) -> None:
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder", editor.text())
        if not folder:
            return
        editor.setText(folder)
        self._set_node_property(key, folder)

    def _choose_file(self, key: str, editor: QtWidgets.QLineEdit) -> None:
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Reference Image",
            editor.text(),
            "Images (*.png *.jpg *.jpeg *.webp *.bmp);;All Files (*)",
        )
        if not path:
            return
        editor.setText(path)
        self._set_node_property(key, path)

    def _open_folder(self, path_text: str) -> None:
        if not path_text.strip():
            QtWidgets.QMessageBox.information(self, "Open Folder", "Current path is empty.")
            return
        path = Path(path_text).expanduser()
        if not path.exists():
            QtWidgets.QMessageBox.warning(self, "Open Folder", f"Path does not exist:\n{path}")
            return
        QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(path)))

    def _set_node_property(self, key: str, value: Any) -> None:
        if self._node is None:
            return
        old_value = self._node.get_property(key)
        self._node.set_property(key, value)
        if old_value != value:
            self.propertyChanged.emit()
