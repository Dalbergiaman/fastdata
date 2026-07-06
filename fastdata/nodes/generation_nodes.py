from fastdata.nodes.base import FastDataNode


DEFAULT_MODEL = "nano-banana-2"
DEFAULT_ASPECT_RATIO = "auto"
DEFAULT_IMAGE_SIZE = "2K"

DEFAULT_GPT_MODEL = "gpt-image-2"
DEFAULT_GPT_ASPECT_RATIO = "1024x1024"


class Img2ImgNode(FastDataNode):
    NODE_NAME = "img2img-banana"
    CATEGORY = "generate"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("model", DEFAULT_MODEL)
        self.create_property("aspect_ratio", DEFAULT_ASPECT_RATIO)
        self.create_property("image_size", DEFAULT_IMAGE_SIZE)
        self.create_property("only_missing", True)
        self.add_input("folder_path")
        self.add_input("output_folder")
        self.add_input("prompt")
        self.add_output("generated_images")


class Img2ImgGptNode(FastDataNode):
    NODE_NAME = "img2img-gpt"
    CATEGORY = "generate"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("model", DEFAULT_GPT_MODEL)
        self.create_property("aspect_ratio", DEFAULT_GPT_ASPECT_RATIO)
        self.create_property("only_missing", True)
        self.add_input("folder_path")
        self.add_input("output_folder")
        self.add_input("prompt")
        self.add_output("generated_images")


class Text2ImgNode(FastDataNode):
    NODE_NAME = "Text2Img"
    CATEGORY = "generate"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("model", DEFAULT_MODEL)
        self.create_property("aspect_ratio", DEFAULT_ASPECT_RATIO)
        self.create_property("image_size", DEFAULT_IMAGE_SIZE)
        self.create_property("count", 1)
        self.add_input("prompt")
        self.add_input("output_folder")
        self.add_output("generated_images")
