"""NodeGraphQt node definitions."""
from fastdata.nodes.base import FastDataNode, NodeStatus
from fastdata.nodes.input_nodes import PathInputNode, PromptInputNode
from fastdata.nodes.output_nodes import OutputFolderNode


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
    "INPUT_OUTPUT_NODES",
]
