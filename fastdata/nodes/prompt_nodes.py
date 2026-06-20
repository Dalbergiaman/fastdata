from fastdata.nodes.base import FastDataNode


class PromptBatchGenerateNode(FastDataNode):
    NODE_NAME = "Prompt Batch Generate"
    CATEGORY = "prompt"

    def __init__(self) -> None:
        super().__init__()
        self.create_property("count", 1)
        self.create_property("filename_prefix", "")
        self.add_input("prompt")
        self.add_input("output_folder")
        self.add_output("prompt_files")
