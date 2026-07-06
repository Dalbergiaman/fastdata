import argparse
import json
import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from fastdata.ui.graph import GraphWidget, NODE_ALIASES
from fastdata.ui.property_panel import PropertyPanel
from fastdata.ui.settings_dialog import SettingsDialog
from fastdata.ui.theme import apply_app_theme
from fastdata.ui.workers import NodeWorker, build_execution_plan, build_snapshots, execute_node_sequence
from fastdata.core.generator import StopToken
from fastdata.nodes.base import NodeStatus


WINDOW_TITLE = "FastData NodeGraph"
DEFAULT_SIZE = (1440, 900)
MINIMUM_SIZE = (960, 640)
DEFAULT_FONT_FAMILY = "Microsoft YaHei UI"
DEFAULT_FONT_SIZE = 10
APP_ICON_PATH = Path(__file__).resolve().parent.parent / "assets" / "app_icon.svg"


def enable_dpi_awareness() -> None:
    # Qt6/PySide6 sets Windows DPI awareness by default. Calling the Windows
    # DPI API again can print SetProcessDpiAwarenessContext access warnings.
    return


def configure_font(app: QtWidgets.QApplication) -> None:
    app.setFont(QtGui.QFont(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE))


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.setWindowIcon(QtGui.QIcon(str(APP_ICON_PATH)))
        self.resize(*DEFAULT_SIZE)
        self.setMinimumSize(*MINIMUM_SIZE)

        self.graph_widget = GraphWidget(self)
        self.node_library = self._build_node_library()
        self.property_panel = PropertyPanel(self)
        self.log_panel = self._build_log_panel()
        self.node_dock: QtWidgets.QDockWidget | None = None
        self.property_dock: QtWidgets.QDockWidget | None = None
        self.log_dock: QtWidgets.QDockWidget | None = None
        self._worker_thread: QtCore.QThread | None = None
        self._worker: NodeWorker | None = None
        self._stop_token: StopToken | None = None
        self.run_action: QtGui.QAction | None = None
        self.stop_action: QtGui.QAction | None = None
        self.delete_action: QtGui.QAction | None = None
        self.node_panel_action: QtGui.QAction | None = None
        self.property_panel_action: QtGui.QAction | None = None
        self.log_panel_action: QtGui.QAction | None = None
        self.task_progress_label: QtWidgets.QLabel | None = None
        self.task_progress_bar: QtWidgets.QProgressBar | None = None
        self.current_workflow_path: str | None = None
        self.is_workflow_dirty = False
        self._is_loading_workflow = False
        self._saved_workflow_snapshot = ""

        self._build_toolbar()
        self._build_layout()
        self.graph_widget.graph.node_created.connect(self._on_node_created)
        self.graph_widget.graph.node_selection_changed.connect(self._on_node_selection_changed)
        self.graph_widget.graph.session_changed.connect(self._on_graph_session_changed)
        self.property_panel.propertyChanged.connect(self.mark_workflow_dirty)
        self._save_workflow_snapshot()
        self._update_window_title()
        self.set_status("Ready")

    def _build_toolbar(self) -> None:
        toolbar = QtWidgets.QToolBar("Main Toolbar", self)
        toolbar.setMovable(False)
        toolbar.setIconSize(QtCore.QSize(18, 18))
        self.addToolBar(QtCore.Qt.TopToolBarArea, toolbar)

        for label in ("New", "Open", "Save", "Delete", "Run", "Stop", "Settings"):
            action = QtGui.QAction(label, self)
            toolbar.addAction(action)
            if label == "New":
                action.triggered.connect(self.new_workflow)
            elif label == "Open":
                action.triggered.connect(self.open_workflow)
            elif label == "Save":
                action.triggered.connect(self.save_workflow)
            elif label == "Delete":
                self.delete_action = action
                action.triggered.connect(self.delete_selected_nodes)
            elif label == "Run":
                self.run_action = action
                action.triggered.connect(self.run_selected_node)
            elif label == "Stop":
                self.stop_action = action
                action.triggered.connect(self.stop_current_task)
                action.setEnabled(False)
            elif label == "Settings":
                action.triggered.connect(self.open_settings)
            if label in {"Save", "Delete", "Stop"}:
                toolbar.addSeparator()

        spacer = QtWidgets.QWidget(self)
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        toolbar.addWidget(spacer)
        toolbar.addWidget(self._build_task_progress_widget())

        for label, tooltip, icon, callback in (
            (
                "Nodes",
                "Toggle Nodes panel",
                self._build_panel_icon("left"),
                lambda checked: self._set_dock_visible(self.node_dock, checked),
            ),
            (
                "Properties",
                "Toggle Properties panel",
                self._build_panel_icon("right"),
                lambda checked: self._set_dock_visible(self.property_dock, checked),
            ),
            (
                "Log",
                "Toggle Log panel",
                self._build_panel_icon("bottom"),
                lambda checked: self._set_dock_visible(self.log_dock, checked),
            ),
        ):
            action = QtGui.QAction(icon, "", self)
            action.setToolTip(tooltip)
            action.setCheckable(True)
            action.setChecked(True)
            action.triggered.connect(callback)
            toolbar.addAction(action)
            if label == "Nodes":
                self.node_panel_action = action
            elif label == "Properties":
                self.property_panel_action = action
            elif label == "Log":
                self.log_panel_action = action

    def _build_panel_icon(self, side: str) -> QtGui.QIcon:
        pixmap = QtGui.QPixmap(18, 18)
        pixmap.fill(QtCore.Qt.transparent)

        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtGui.QPen(QtGui.QColor("#8e98aa"), 1))
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#20232b")))
        painter.drawRoundedRect(2, 3, 14, 12, 2, 2)

        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QBrush(QtGui.QColor("#7aa2d6")))
        if side == "left":
            painter.drawRect(3, 4, 4, 10)
        elif side == "right":
            painter.drawRect(11, 4, 4, 10)
        elif side == "bottom":
            painter.drawRect(3, 10, 12, 4)
        painter.end()
        return QtGui.QIcon(pixmap)

    def _build_task_progress_widget(self) -> QtWidgets.QWidget:
        container = QtWidgets.QFrame(self)
        container.setObjectName("TaskProgress")
        container.setFixedWidth(240)
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(10, 2, 10, 2)
        layout.setSpacing(4)

        self.task_progress_label = QtWidgets.QLabel("Idle", container)
        self.task_progress_label.setObjectName("TaskProgressText")
        self.task_progress_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        self.task_progress_bar = QtWidgets.QProgressBar(container)
        self.task_progress_bar.setObjectName("TaskProgressBar")
        self.task_progress_bar.setRange(0, 100)
        self.task_progress_bar.setValue(0)
        self.task_progress_bar.setTextVisible(False)
        self.task_progress_bar.setFixedHeight(4)

        layout.addWidget(self.task_progress_label)
        layout.addWidget(self.task_progress_bar)
        return container

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

    def _build_log_panel(self) -> QtWidgets.QTextEdit:
        log = QtWidgets.QTextEdit(self)
        log.setObjectName("LogPanel")
        log.setReadOnly(True)
        log.setMinimumHeight(80)
        return log

    def _build_layout(self) -> None:
        self.setCentralWidget(self.graph_widget)

        self.node_dock = self._build_dock("Nodes", self.node_library, QtCore.Qt.LeftDockWidgetArea)
        self.property_dock = self._build_dock("Properties", self.property_panel, QtCore.Qt.RightDockWidgetArea)
        self.log_dock = self._build_dock("Log", self.log_panel, QtCore.Qt.BottomDockWidgetArea)
        self.node_dock.setMinimumWidth(220)
        self.property_dock.setMinimumWidth(280)
        self.log_dock.setMinimumHeight(110)
        self.node_dock.visibilityChanged.connect(self._sync_node_panel_action)
        self.property_dock.visibilityChanged.connect(self._sync_property_panel_action)
        self.log_dock.visibilityChanged.connect(self._sync_log_panel_action)
        self.resizeDocks([self.node_dock, self.property_dock], [220, 280], QtCore.Qt.Horizontal)
        self.resizeDocks([self.log_dock], [130], QtCore.Qt.Vertical)

    def _build_dock(
        self,
        title: str,
        widget: QtWidgets.QWidget,
        area: QtCore.Qt.DockWidgetArea,
    ) -> QtWidgets.QDockWidget:
        dock = QtWidgets.QDockWidget(title, self)
        dock.setObjectName("PanelDock")
        dock.setWidget(widget)
        dock.setFeatures(
            QtWidgets.QDockWidget.DockWidgetClosable
            | QtWidgets.QDockWidget.DockWidgetMovable
            | QtWidgets.QDockWidget.DockWidgetFloatable
        )
        self.addDockWidget(area, dock)
        return dock

    def _set_dock_visible(self, dock: QtWidgets.QDockWidget | None, visible: bool) -> None:
        if dock is not None:
            dock.setVisible(visible)

    def _sync_node_panel_action(self, visible: bool) -> None:
        if self.node_panel_action:
            self.node_panel_action.setChecked(visible)

    def _sync_property_panel_action(self, visible: bool) -> None:
        if self.property_panel_action:
            self.property_panel_action.setChecked(visible)

    def _sync_log_panel_action(self, visible: bool) -> None:
        if self.log_panel_action:
            self.log_panel_action.setChecked(visible)

    def set_status(self, message: str) -> None:
        self.log_panel.append(message)

    def set_task_progress(self, label: str, current: int = 0, total: int = 0) -> None:
        if self.task_progress_label:
            self.task_progress_label.setText(label)
        if not self.task_progress_bar:
            return
        if total <= 0:
            self.task_progress_bar.setValue(0)
            return
        value = max(0, min(100, int((current / total) * 100)))
        self.task_progress_bar.setValue(value)

    def _on_workflow_progress(self, label: str, current: int, total: int) -> None:
        if label == "Workflow":
            self.set_task_progress(f"Running Workflow {current}/{total}", current, total)
            return
        self.set_task_progress(f"Running {label} {current}/{total}", current, total)

    def add_node_to_graph(self, node_name: str) -> None:
        try:
            self.graph_widget.create_node(node_name)
        except ValueError as error:
            self.set_status(str(error))
            return

    def new_workflow(self) -> None:
        if not self._confirm_discard_unsaved_changes():
            return
        self._is_loading_workflow = True
        self.graph_widget.graph.clear_session()
        self._is_loading_workflow = False
        self.current_workflow_path = None
        self.property_panel.set_node(None)
        self._save_workflow_snapshot()
        self.set_status("New workflow")

    def open_workflow(self) -> None:
        if not self._confirm_discard_unsaved_changes():
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Workflow", "workflows", "Workflow (*.json)")
        if not path:
            return
        self._is_loading_workflow = True
        try:
            self.graph_widget.graph.load_session(path)
            self._bind_all_node_dirty_callbacks()
            self.current_workflow_path = path
            self.property_panel.set_node(None)
            self._save_workflow_snapshot()
            self.set_status(f"Opened workflow: {path}")
        except Exception as error:
            self.set_status(f"Failed to open workflow: {error}")
            QtWidgets.QMessageBox.warning(self, "Open Workflow", f"Could not open workflow:\n{error}")
            # Re-baseline the dirty snapshot against the (possibly partial) state
            # so dirty tracking keeps working.
            self._save_workflow_snapshot()
        finally:
            self._is_loading_workflow = False

    def save_workflow(self) -> bool:
        path = self.current_workflow_path
        if not path:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Workflow", "workflows/workflow.json", "Workflow (*.json)")
        if not path:
            return False
        self.graph_widget.graph.save_session(path)
        self.current_workflow_path = path
        self._save_workflow_snapshot()
        self.set_status(f"Saved workflow: {path}")
        return True

    def open_settings(self) -> None:
        dialog = SettingsDialog(self)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            self.set_status("Settings saved")

    def delete_selected_nodes(self) -> None:
        if self._worker_thread is not None:
            self.set_status("Cannot delete nodes while a task is running.")
            return
        selected = self.graph_widget.graph.selected_nodes()
        if not selected:
            self.set_status("Select node(s) to delete.")
            return
        self.graph_widget.graph.delete_nodes(selected)
        self.property_panel.set_node(None)
        self.set_status(f"Deleted {len(selected)} node(s)")

    def mark_workflow_dirty(self) -> None:
        if self._is_loading_workflow:
            return
        self._refresh_workflow_dirty_state()

    def _bind_node_dirty_callback(self, node) -> None:
        if hasattr(node, "on_property_changed"):
            node.on_property_changed = self.mark_workflow_dirty

    def _bind_all_node_dirty_callbacks(self) -> None:
        for node in self.graph_widget.graph.all_nodes():
            self._bind_node_dirty_callback(node)

    def _on_node_created(self, node) -> None:
        self._bind_node_dirty_callback(node)
        if not self._is_loading_workflow:
            self.set_status(f"Created node: {node.name()}")
            self.mark_workflow_dirty()

    def _on_graph_session_changed(self, _path: str = "") -> None:
        self.mark_workflow_dirty()

    def _serialize_workflow_snapshot(self) -> str:
        return json.dumps(self.graph_widget.graph.serialize_session(), sort_keys=True, ensure_ascii=False)

    def _save_workflow_snapshot(self) -> None:
        self._saved_workflow_snapshot = self._serialize_workflow_snapshot()
        self._set_workflow_dirty(False)

    def _refresh_workflow_dirty_state(self) -> None:
        self._set_workflow_dirty(self._serialize_workflow_snapshot() != self._saved_workflow_snapshot)

    def _set_workflow_dirty(self, dirty: bool) -> None:
        if self.is_workflow_dirty == dirty:
            return
        self.is_workflow_dirty = dirty
        self._update_window_title()

    def _update_window_title(self) -> None:
        marker = "*" if self.is_workflow_dirty else ""
        if self.current_workflow_path:
            self.setWindowTitle(f"{marker}{WINDOW_TITLE} - {self.current_workflow_path}")
            return
        self.setWindowTitle(f"{marker}{WINDOW_TITLE}")

    def _confirm_discard_unsaved_changes(self) -> bool:
        if not self.is_workflow_dirty:
            return True

        response = QtWidgets.QMessageBox.warning(
            self,
            "Unsaved Workflow",
            "The current workflow has unsaved changes.",
            QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel,
            QtWidgets.QMessageBox.Save,
        )
        if response == QtWidgets.QMessageBox.Save:
            return self.save_workflow()
        if response == QtWidgets.QMessageBox.Discard:
            return True
        return False

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if not self._confirm_discard_unsaved_changes():
            event.ignore()
            return
        self._abort_running_worker()
        event.accept()

    def _abort_running_worker(self) -> None:
        if self._stop_token:
            self._stop_token.stop()
        thread = self._worker_thread
        if thread is None:
            return
        thread.quit()
        # With interruptible stop the worker returns within moments; the timeout
        # covers a worker stuck mid network call, and terminate() is safe because
        # the process is shutting down.
        if not thread.wait(3000):
            thread.terminate()
            thread.wait(2000)
        self._worker = None
        self._worker_thread = None
        self._stop_token = None

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() in (QtCore.Qt.Key_Delete, QtCore.Qt.Key_Backspace):
            self.delete_selected_nodes()
            event.accept()
            return
        super().keyPressEvent(event)

    def _on_node_selection_changed(self, selected_nodes, deselected_nodes) -> None:
        del deselected_nodes
        if not selected_nodes:
            self.property_panel.set_node(None)
            return
        self.property_panel.set_node(selected_nodes[-1])

    def run_selected_node(self) -> None:
        if self._worker_thread is not None:
            self.set_status("A node is already running.")
            return

        selected_nodes = self.graph_widget.graph.selected_nodes()
        if not selected_nodes:
            self.set_status("Select a node to run.")
            return

        node = selected_nodes[-1]
        self._stop_token = StopToken()
        try:
            plan = build_execution_plan(node)
            snapshots = build_snapshots(plan)
            runner = lambda progress: execute_node_sequence(snapshots, self._stop_token, progress)
        except Exception as error:
            node.set_status(NodeStatus.ERROR, str(error))
            self.set_status(str(error))
            return

        for plan_node in plan:
            plan_node.set_status(NodeStatus.RUNNING, "Queued")
        self.set_status(f"Running to selected: {' -> '.join(plan_node.name() for plan_node in plan)}")
        self.set_task_progress(f"Running 0/{len(plan)}", 0, len(plan))
        self._worker_thread = QtCore.QThread(self)
        self._worker = NodeWorker(node, runner)
        self._worker.moveToThread(self._worker_thread)
        self._worker_thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_workflow_progress)
        self._worker.finished.connect(lambda result: self._on_node_finished(plan, result))
        self._worker.failed.connect(lambda message: self._on_node_failed(node, message))
        self._worker.finished.connect(self._cleanup_worker)
        self._worker.failed.connect(self._cleanup_worker)
        self._worker_thread.start()
        if self.run_action:
            self.run_action.setEnabled(False)
        if self.stop_action:
            self.stop_action.setEnabled(True)
        if self.delete_action:
            self.delete_action.setEnabled(False)

    def stop_current_task(self) -> None:
        if self._stop_token:
            self._stop_token.stop()
            self.set_task_progress("Stopping...")
            self.set_status("Stop requested.")

    def _on_node_finished(self, plan, result) -> None:
        for node in plan:
            node.set_status(NodeStatus.SUCCESS, "Done")
        count = len(result.get("results", [])) if isinstance(result, dict) else 1
        output_count = self._count_result_items(result)
        self.set_task_progress(f"Done {output_count} item(s)", 1, 1)
        message = f"Workflow finished: {count} node(s), {output_count} item(s)"
        self.set_status(message)

    def _on_node_failed(self, node, message: str) -> None:
        node.set_status(NodeStatus.ERROR, message)
        self.set_task_progress("Failed", 1, 1)
        self.set_status(f"{node.name()} failed: {message}")

    def _count_result_items(self, result) -> int:
        if not isinstance(result, dict):
            return 1
        items = result.get("results", [])
        total = 0
        for item in items:
            node_result = item.get("result") if isinstance(item, dict) else None
            total += len(node_result) if isinstance(node_result, list) else 1
        return total

    def _cleanup_worker(self) -> None:
        if self._worker_thread:
            self._worker_thread.quit()
            # Bound the wait so a worker slow to exit can never freeze the UI on
            # the finish transition; terminate() is the last resort.
            if not self._worker_thread.wait(3000):
                self.set_status("Worker did not exit cleanly; forcing termination.")
                self._worker_thread.terminate()
                self._worker_thread.wait(1000)
        if self._worker:
            self._worker.deleteLater()
        if self._worker_thread:
            self._worker_thread.deleteLater()
        self._worker = None
        self._worker_thread = None
        self._stop_token = None
        if self.run_action:
            self.run_action.setEnabled(True)
        if self.stop_action:
            self.stop_action.setEnabled(False)
        if self.delete_action:
            self.delete_action.setEnabled(True)


class NodeLibraryItem(QtWidgets.QLabel):
    nodeRequested = QtCore.Signal(str)

    def __init__(self, node_name: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(node_name, parent)
        self.node_name = node_name
        self._drag_start_pos = QtCore.QPoint()
        self.setObjectName("NodeLibraryItem")
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == QtCore.Qt.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        if not event.buttons() & QtCore.Qt.LeftButton:
            super().mouseMoveEvent(event)
            return

        distance = (event.pos() - self._drag_start_pos).manhattanLength()
        if distance < QtWidgets.QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return

        alias = NODE_ALIASES.get(self.node_name)
        if alias is None:
            return

        mime_data = QtCore.QMimeData()
        mime_data.setData("nodegraphqt/nodes", f"nodegraphqt::node:{alias}".encode("utf-8"))

        drag = QtGui.QDrag(self)
        drag.setMimeData(mime_data)
        drag.setPixmap(self.grab())
        drag.setHotSpot(event.pos())
        drag.exec(QtCore.Qt.CopyAction)

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
    window.showMaximized()
    if args.smoke_test:
        QtCore.QTimer.singleShot(1000, app.quit)
    return app.exec()
