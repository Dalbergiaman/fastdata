import argparse
import importlib.util
import sys
import types
from pathlib import Path


def install_distutils_looseversion_shim() -> None:
    """
    NodeGraphQt still imports distutils.version.LooseVersion.
    Python 3.14 no longer ships distutils, so this shim provides the tiny
    piece NodeGraphQt needs for import-time compatibility.
    """
    if importlib.util.find_spec("distutils.version") is not None:
        return

    if "distutils.version" in sys.modules:
        return

    class LooseVersion:
        def __init__(self, version: str):
            self.version = version

        def _parts(self):
            parts = []
            for chunk in self.version.replace("-", ".").split("."):
                if chunk.isdigit():
                    parts.append(int(chunk))
                else:
                    parts.append(chunk)
            return tuple(parts)

        def __lt__(self, other):
            return self._parts() < other._parts()

        def __le__(self, other):
            return self._parts() <= other._parts()

        def __eq__(self, other):
            return self._parts() == other._parts()

        def __ne__(self, other):
            return self._parts() != other._parts()

        def __gt__(self, other):
            return self._parts() > other._parts()

        def __ge__(self, other):
            return self._parts() >= other._parts()

        def __repr__(self):
            return f"LooseVersion('{self.version}')"

    distutils_module = types.ModuleType("distutils")
    version_module = types.ModuleType("distutils.version")
    version_module.LooseVersion = LooseVersion
    distutils_module.version = version_module
    sys.modules["distutils"] = distutils_module
    sys.modules["distutils.version"] = version_module


install_distutils_looseversion_shim()

from Qt import QtCore, QtWidgets  # noqa: E402
from NodeGraphQt import BaseNode, NodeGraph  # noqa: E402


class SourceNode(BaseNode):
    __identifier__ = "fastdata.demo"
    NODE_NAME = "Source"

    def __init__(self):
        super().__init__()
        self.set_color(70, 75, 89)
        self.add_output("images")
        self.add_text_input("folder_path", "Folder", str(Path.cwd()))


class PromptNode(BaseNode):
    __identifier__ = "fastdata.demo"
    NODE_NAME = "Prompt"

    def __init__(self):
        super().__init__()
        self.set_color(79, 93, 117)
        self.add_output("prompt")
        self.add_text_input("prompt", "Prompt", "demo prompt")


class GenerateNode(BaseNode):
    __identifier__ = "fastdata.demo"
    NODE_NAME = "Generate"

    def __init__(self):
        super().__init__()
        self.set_color(96, 67, 119)
        self.add_input("images")
        self.add_input("prompt")
        self.add_output("output")
        self.add_combo_menu("model", "Model", ["nano-banana-2", "nano-banana-fast"])


def build_graph() -> NodeGraph:
    graph = NodeGraph()
    graph.register_node(SourceNode, alias="demo.source")
    graph.register_node(PromptNode, alias="demo.prompt")
    graph.register_node(GenerateNode, alias="demo.generate")

    source = graph.create_node("demo.source", name="Input Images", pos=[-220, -40])
    prompt = graph.create_node("demo.prompt", name="Prompt Text", pos=[-220, 140])
    generate = graph.create_node("demo.generate", name="Async Generate", pos=[120, 40])

    source.output(0).connect_to(generate.input(0))
    prompt.output(0).connect_to(generate.input(1))
    return graph


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a minimal NodeGraphQt demo.")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Open the graph briefly and close automatically.",
    )
    args = parser.parse_args()

    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    graph = build_graph()
    viewer = graph.widget
    viewer.setWindowTitle("FastData NodeGraph Demo")
    viewer.resize(1200, 720)
    viewer.show()

    if args.smoke_test:
        QtCore.QTimer.singleShot(1000, app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
