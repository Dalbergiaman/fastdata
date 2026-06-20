from fastdata.config import get_default_config
from fastdata.nodes.base import FastDataNode


class Img2ImgNode(FastDataNode):
    NODE_NAME = "Img2Img"
    CATEGORY = "generate"

    def __init__(self) -> None:
        super().__init__()
        config = get_default_config()
        self.create_property("model", config["model"])
        self.create_property("aspect_ratio", config["aspect_ratio"])
        self.create_property("image_size", config["image_size"])
        self.create_property("only_missing", config["only_missing"])
        self.add_input("folder_path")
        self.add_input("prompt")
        self.add_input("output_folder")
        self.add_output("generated_images")


class Text2ImgNode(FastDataNode):
    NODE_NAME = "Text2Img"
    CATEGORY = "generate"

    def __init__(self) -> None:
        super().__init__()
        config = get_default_config()
        self.create_property("model", config["model"])
        self.create_property("aspect_ratio", config["aspect_ratio"])
        self.create_property("image_size", config["image_size"])
        self.create_property("count", 1)
        self.add_input("prompt")
        self.add_input("output_folder")
        self.add_output("generated_images")
