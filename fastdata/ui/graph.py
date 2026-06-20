from PySide6 import QtWidgets
from NodeGraphQt import NodeGraph

from fastdata.nodes import NODE_CLASSES


NODE_ALIASES = {
    "Path Input": "fastdata.path_input",
    "Prompt Input": "fastdata.prompt_input",
    "Output Folder": "fastdata.output_folder",
    "Img2Img": "fastdata.img2img",
    "Text2Img": "fastdata.text2img",
    "Image To PNG": "fastdata.image_to_png",
    "Image To JPG": "fastdata.image_to_jpg",
    "Resize Match": "fastdata.resize_match",
    "Resize Image": "fastdata.resize_image",
    "Prompt Batch Generate": "fastdata.prompt_batch_generate",
}


class GraphWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.graph = NodeGraph()
        self._register_nodes()
        self._build_start_graph()

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.graph.widget)

    def _register_nodes(self) -> None:
        for node_class in NODE_CLASSES:
            self.graph.register_node(node_class, alias=NODE_ALIASES[node_class.NODE_NAME])

    def _build_start_graph(self) -> None:
        self.create_node("Path Input", pos=[-360, -100])
        self.create_node("Prompt Input", pos=[-360, 80])
        self.create_node("Output Folder", pos=[20, 0])

    def create_node(self, node_name: str, pos: list[int] | None = None):
        alias = NODE_ALIASES.get(node_name)
        if alias is None:
            raise ValueError(f"Unknown node type: {node_name}")
        return self.graph.create_node(alias, name=node_name, pos=pos or [0, 0])
