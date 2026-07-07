"""NodeGraphQt node definitions."""
from fastdata.nodes.base import FastDataNode, NodeStatus
from fastdata.nodes.generation_nodes import Img2ImgGptNode, Img2ImgNode, Text2ImgNode
from fastdata.nodes.image_nodes import ImageToJpgNode, ImageToPngNode, ResizeImageNode, ResizeToReferenceNode
from fastdata.nodes.input_nodes import PathInputNode, PromptInputNode
from fastdata.nodes.output_nodes import OutputFolderNode
from fastdata.nodes.prompt_nodes import PromptBatchGenerateNode


NODE_CLASSES = (
    PathInputNode,
    PromptInputNode,
    OutputFolderNode,
    Img2ImgNode,
    Img2ImgGptNode,
    Text2ImgNode,
    ImageToPngNode,
    ImageToJpgNode,
    ResizeToReferenceNode,
    ResizeImageNode,
    PromptBatchGenerateNode,
)

INPUT_OUTPUT_NODES = (
    PathInputNode,
    PromptInputNode,
    OutputFolderNode,
)

__all__ = [
    "FastDataNode",
    "NodeStatus",
    "PathInputNode",
    "PromptInputNode",
    "OutputFolderNode",
    "Img2ImgNode",
    "Img2ImgGptNode",
    "Text2ImgNode",
    "ImageToPngNode",
    "ImageToJpgNode",
    "ResizeToReferenceNode",
    "ResizeImageNode",
    "PromptBatchGenerateNode",
    "NODE_CLASSES",
    "INPUT_OUTPUT_NODES",
]
