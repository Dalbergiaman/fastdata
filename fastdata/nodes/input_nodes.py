from fastdata.nodes.base import FastDataNode
from fastdata.nodes.widgets import PromptTextWidget


class PathInputNode(FastDataNode):
    NODE_NAME = "Path Input"
    CATEGORY = "input"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("folder_path", "")
        self.create_property("path_role", "images")
        self.create_property("include_extensions", ".png,.jpg,.jpeg,.webp,.bmp,.gif,.tiff,.tif")
        self.add_output("folder_path")
        self.add_output("images")
        self.add_output("files")


class PromptInputNode(FastDataNode):
    NODE_NAME = "Prompt Input"
    CATEGORY = "prompt"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("prompt_text", "")
        widget = PromptTextWidget(self.view, "prompt_text", "Prompt", "")
        widget.value_changed.connect(lambda key, value: self.set_property(key, value))
        self.view.add_widget(widget)
        self.view.draw_node()
        self.add_output("prompt")
