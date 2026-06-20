import ctypes
import argparse
import sys

from PySide6 import QtCore, QtGui, QtWidgets

from fastdata.ui.graph import GraphWidget
from fastdata.ui.theme import apply_app_theme


WINDOW_TITLE = "FastData NodeGraph"
DEFAULT_SIZE = (1440, 900)
MINIMUM_SIZE = (1100, 700)
DEFAULT_FONT_FAMILY = "Microsoft YaHei UI"
DEFAULT_FONT_SIZE = 10


def enable_dpi_awareness() -> None:
    if sys.platform != "win32":
        return

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def configure_font(app: QtWidgets.QApplication) -> None:
    app.setFont(QtGui.QFont(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(*DEFAULT_SIZE)
        self.setMinimumSize(*MINIMUM_SIZE)

        self.graph_widget = GraphWidget(self)
        self.node_library = self._build_node_library()
        self.property_panel = self._build_property_panel()
        self.log_panel = self._build_log_panel()

        self._build_toolbar()
        self._build_layout()
        self.set_status("Ready")

    def _build_toolbar(self) -> None:
        toolbar = QtWidgets.QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QtCore.QSize(18, 18))
        self.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)

        for label in ("New", "Open", "Save", "Run", "Stop", "Settings"):
            action = QtGui.QAction(label, self)
            toolbar.addAction(action)
            if label in {"Save", "Stop"}:
                toolbar.addSeparator()

    def _build_node_library(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QFrame(self)
        panel.setObjectName("SidePanel")
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QtWidgets.QLabel("Nodes", panel)
        title.setObjectName("PanelTitle")
        layout.addWidget(title)

        groups = {
            "Input": ["Path Input", "Prompt Input", "Output Folder"],
            "Generate": ["Img2Img", "Text2Img"],
            "Image": ["Image To PNG", "Image To JPG", "Resize Match", "Resize Image"],
            "Prompt": ["Prompt Batch Generate"],
        }
        for group_name, nodes in groups.items():
            group_label = QtWidgets.QLabel(group_name, panel)
            group_label.setObjectName("GroupTitle")
            layout.addWidget(group_label)
            for node_name in nodes:
                item = NodeLibraryItem(node_name, panel)
                item.nodeRequested.connect(self.add_node_to_graph)
                layout.addWidget(item)

        layout.addStretch(1)
        return panel

    def _build_property_panel(self) -> QtWidgets.QWidget:
        panel = QtWidgets.QFrame(self)
        panel.setObjectName("SidePanel")
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        title = QtWidgets.QLabel("Properties", panel)
        title.setObjectName("PanelTitle")
        layout.addWidget(title)

        placeholder = QtWidgets.QLabel("Select a node to edit its parameters.", panel)
        placeholder.setObjectName("MutedText")
        placeholder.setWordWrap(True)
        layout.addWidget(placeholder)
        layout.addStretch(1)
        return panel

    def _build_log_panel(self) -> QtWidgets.QTextEdit:
        log = QtWidgets.QTextEdit(self)
        log.setObjectName("LogPanel")
        log.setReadOnly(True)
        log.setFixedHeight(96)
        return log

    def _build_layout(self) -> None:
        central = QtWidgets.QWidget(self)
        root_layout = QtWidgets.QVBoxLayout(central)
        root_layout.setContentsMargins(10, 10, 10, 10)
        root_layout.setSpacing(10)

        content_layout = QtWidgets.QHBoxLayout()
        content_layout.setSpacing(10)

        self.node_library.setFixedWidth(220)
        self.property_panel.setFixedWidth(280)
        content_layout.addWidget(self.node_library)
        content_layout.addWidget(self.graph_widget, 1)
        content_layout.addWidget(self.property_panel)

        root_layout.addLayout(content_layout, 1)
        root_layout.addWidget(self.log_panel)
        self.setCentralWidget(central)

    def set_status(self, message: str) -> None:
        self.statusBar().showMessage(message)
        self.log_panel.append(message)

    def add_node_to_graph(self, node_name: str) -> None:
        try:
            self.graph_widget.create_node(node_name)
        except ValueError as error:
            self.set_status(str(error))
            return
        self.set_status(f"Created node: {node_name}")


class NodeLibraryItem(QtWidgets.QLabel):
    nodeRequested = QtCore.Signal(str)

    def __init__(self, node_name: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(node_name, parent)
        self.node_name = node_name
        self.setObjectName("NodeLibraryItem")
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self.nodeRequested.emit(self.node_name)
        super().mouseDoubleClickEvent(event)


def create_app(argv: list[str] | None = None) -> QtWidgets.QApplication:
    enable_dpi_awareness()
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(argv or sys.argv)
    configure_font(app)
    apply_app_theme(app)
    return app


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the FastData NodeGraph application.")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Open the main window briefly and close automatically.",
    )
    args = parser.parse_args(argv)

    app = create_app(argv)
    window = MainWindow()
    window.show()
    if args.smoke_test:
        QtCore.QTimer.singleShot(1000, app.quit)
    return app.exec()
