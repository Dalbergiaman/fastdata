from fastdata.nodes.base import FastDataNode


class ImageToPngNode(FastDataNode):
    NODE_NAME = "Image To PNG"
    CATEGORY = "image"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("overwrite", False)
        self.add_input("folder_path")
        self.add_input("output_folder")
        self.add_output("png_images")


class ImageToJpgNode(FastDataNode):
    NODE_NAME = "Image To JPG"
    CATEGORY = "image"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("quality", 95)
        self.create_property("overwrite", False)
        self.add_input("folder_path")
        self.add_input("output_folder")
        self.add_output("jpg_images")


class ResizeToReferenceNode(FastDataNode):
    NODE_NAME = "Resize To Reference"
    CATEGORY = "image"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("overwrite", False)
        self.add_input("reference_folder_path")
        self.add_input("source_folder_path")
        self.add_input("output_folder")
        self.add_output("matched_images")


class ResizeImageNode(FastDataNode):
    NODE_NAME = "Resize Image"
    CATEGORY = "image"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("target_width", 1024)
        self.create_property("target_height", 1024)
        self.create_property("output_format", "png")
        self.create_property("resize_mode", "fill_crop")
        self.create_property("overwrite", False)
        self.add_input("folder_path")
        self.add_input("output_folder")
        self.add_output("resized_images")
