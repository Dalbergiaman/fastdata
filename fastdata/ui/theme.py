from PySide6 import QtWidgets


APP_STYLESHEET = """
QMainWindow,
QWidget {
    background: #101114;
    color: #e6e8ec;
}

QToolBar {
    background: #15171c;
    border: 0;
    border-bottom: 1px solid #2a2d35;
    spacing: 6px;
    padding: 6px;
}

QToolButton {
    background: #20232b;
    border: 1px solid #333744;
    border-radius: 4px;
    padding: 6px 10px;
    color: #e6e8ec;
}

QToolButton:hover {
    background: #2a2e38;
}

QToolButton:checked {
    background: #26364b;
    border-color: #5f7fa8;
}

QStatusBar {
    background: #101114;
    color: #aeb4c0;
}

QDockWidget {
    color: #f2f4f8;
}

QDockWidget::title {
    background: #15171c;
    border: 1px solid #2a2d35;
    border-bottom: 0;
    padding: 7px 9px;
    text-align: left;
}

QFrame#SidePanel,
QTextEdit#LogPanel {
    background: #17191f;
    border: 1px solid #2a2d35;
    border-radius: 4px;
}

QLabel#PanelTitle {
    color: #f2f4f8;
    font-size: 14px;
    font-weight: 600;
}

QLabel#GroupTitle {
    color: #8e98aa;
    font-size: 11px;
    text-transform: uppercase;
    margin-top: 8px;
}

QLabel#NodeLibraryItem {
    background: #20232b;
    border: 1px solid #313644;
    border-radius: 4px;
    padding: 7px 9px;
    color: #dce0e8;
}

QLabel#MutedText {
    color: #9aa3b2;
}

QLineEdit,
QPlainTextEdit,
QComboBox,
QSpinBox {
    color: #d8deea;
    background: #20232b;
    border: 1px solid #313644;
    border-radius: 4px;
    padding: 5px 7px;
    selection-background-color: #4f678a;
}

QPushButton {
    color: #d8deea;
    background: #252a34;
    border: 1px solid #3a4150;
    border-radius: 4px;
    padding: 5px 8px;
}

QPushButton:hover {
    background: #303746;
}

QTextEdit#LogPanel {
    color: #c6ccd8;
    padding: 8px;
}
"""


def apply_app_theme(app: QtWidgets.QApplication) -> None:
    app.setStyleSheet(APP_STYLESHEET)
