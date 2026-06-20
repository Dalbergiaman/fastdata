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

QStatusBar {
    background: #101114;
    color: #aeb4c0;
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

QTextEdit#LogPanel {
    color: #c6ccd8;
    padding: 8px;
}
"""


def apply_app_theme(app: QtWidgets.QApplication) -> None:
    app.setStyleSheet(APP_STYLESHEET)
