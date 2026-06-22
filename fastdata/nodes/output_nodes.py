from fastdata.nodes.base import FastDataNode
from fastdata.nodes.widgets import FolderPathWidget


class OutputFolderNode(FastDataNode):
    NODE_NAME = "Output Folder"
    CATEGORY = "output"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("folder_path", "")
        widget = FolderPathWidget(self.view, "folder_path", "Folder", "")
        widget.value_changed.connect(lambda key, value: self.set_property(key, value))
        self.view.add_widget(widget)
        self.view.draw_node()
        self.add_output("output_folder")
