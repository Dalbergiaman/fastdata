from PySide6 import QtWidgets
from NodeGraphQt import NodeGraph

from fastdata.nodes import NODE_CLASSES


NODE_ALIASES = {
    "Path Input": "fastdata.path_input",
    "Prompt Input": "fastdata.prompt_input",
    "Output Folder": "fastdata.output_folder",
    "img2img-banana": "fastdata.img2img_banana",
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

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.graph.widget)

    def _register_nodes(self) -> None:
        for node_class in NODE_CLASSES:
            self.graph.register_node(node_class, alias=NODE_ALIASES[node_class.NODE_NAME])

    def create_node(self, node_name: str, pos: list[int] | None = None):
        alias = NODE_ALIASES.get(node_name)
        if alias is None:
            raise ValueError(f"Unknown node type: {node_name}")
        return self.graph.create_node(alias, name=node_name, pos=pos or [0, 0])
