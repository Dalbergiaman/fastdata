from fastdata.nodes.base import FastDataNode


class OutputFolderNode(FastDataNode):
    NODE_NAME = "Output Folder"
    CATEGORY = "output"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("folder_path", "")
        self.add_output("output_folder")
