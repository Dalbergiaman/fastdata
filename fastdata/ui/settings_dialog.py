from typing import Any

from PySide6 import QtWidgets

from fastdata.config import load_config, save_config


class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(460)
        self.config = load_config()

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        form.setSpacing(10)
        layout.addLayout(form)

        self.api_key = QtWidgets.QLineEdit(str(self.config.get("api_key", "")), self)
        self.api_key.setEchoMode(QtWidgets.QLineEdit.Password)
        form.addRow("API Key", self.api_key)

        self.base_url = QtWidgets.QLineEdit(str(self.config.get("base_url", "")), self)
        form.addRow("Base URL", self.base_url)

        self.concurrency = self._spin("concurrency", 1, 64)
        form.addRow("Concurrency", self.concurrency)

        self.poll_interval = self._spin("poll_interval", 1, 120)
        form.addRow("Poll Interval", self.poll_interval)

        self.max_retries = self._spin("max_retries", 1, 10000)
        form.addRow("Max Retries", self.max_retries)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _spin(self, key: str, minimum: int, maximum: int) -> QtWidgets.QSpinBox:
        spin = QtWidgets.QSpinBox(self)
        spin.setRange(minimum, maximum)
        spin.setValue(int(self.config.get(key, minimum)))
        return spin

    def values(self) -> dict[str, Any]:
        config = dict(self.config)
        for key in ("model", "aspect_ratio", "image_size", "only_missing"):
            config.pop(key, None)
        config.update({
            "api_key": self.api_key.text(),
            "base_url": self.base_url.text(),
            "concurrency": self.concurrency.value(),
            "poll_interval": self.poll_interval.value(),
            "max_retries": self.max_retries.value(),
        })
        return config

    def accept(self) -> None:
        save_config(self.values())
        super().accept()
