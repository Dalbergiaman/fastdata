import asyncio
from typing import Any, Callable

from PySide6 import QtCore

from fastdata.config import load_config
from fastdata.core.convert_jpg import convert_images_to_jpg
from fastdata.core.convert_png import convert_images_to_png
from fastdata.core.generator import StopToken, generate_images_async, generate_text_to_images_async
from fastdata.core.prompt_writer import generate_prompt_files
from fastdata.core.resize_image import resize_images
from fastdata.core.resize_match import resize_folder_to_reference
from fastdata.nodes.base import FastDataNode


class NodeExecutionError(RuntimeError):
    pass


class NodeWorker(QtCore.QObject):
    progress = QtCore.Signal(int, int)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, node: FastDataNode, runner: Callable[[Callable[[int, int], None]], Any]) -> None:
        super().__init__()
        self.node = node
        self.runner = runner

    @QtCore.Slot()
    def run(self) -> None:
        try:
            result = self.runner(lambda current, total: self.progress.emit(current, total))
            self.finished.emit(result)
        except Exception as error:
            self.failed.emit(str(error))


def connected_node(node: FastDataNode, input_name: str) -> FastDataNode | None:
    port = node.inputs().get(input_name)
    if port is None:
        return None
    connected_ports = port.connected_ports()
    if not connected_ports:
        return None
    return connected_ports[0].node()


def require_connected_property(node: FastDataNode, input_name: str, property_name: str) -> Any:
    source = connected_node(node, input_name)
    if source is None:
        raise NodeExecutionError(f"Missing connection: {input_name}")
    value = source.get_property(property_name)
    if value in (None, ""):
        raise NodeExecutionError(f"Missing value: {source.name()} / {property_name}")
    return value


def build_generation_config(node: FastDataNode) -> dict[str, Any]:
    config = load_config()
    for key in (
        "api_key",
        "base_url",
        "model",
        "aspect_ratio",
        "image_size",
        "concurrency",
        "poll_interval",
        "max_retries",
        "only_missing",
    ):
        if node.has_property(key):
            config[key] = node.get_property(key)
    return config


def build_node_runner(node: FastDataNode, stop_token: StopToken | None = None) -> Callable[[Callable[[int, int], None]], Any]:
    node_name = getattr(type(node), "NODE_NAME", node.name())

    if node_name == "Image To PNG":
        input_dir = require_connected_property(node, "folder_path", "folder_path")
        output_dir = require_connected_property(node, "output_folder", "folder_path")
        return lambda progress: convert_images_to_png(input_dir, output_dir, bool(node.get_property("overwrite")), progress)

    if node_name == "Image To JPG":
        input_dir = require_connected_property(node, "folder_path", "folder_path")
        output_dir = require_connected_property(node, "output_folder", "folder_path")
        quality = int(node.get_property("quality"))
        overwrite = bool(node.get_property("overwrite"))
        return lambda progress: convert_images_to_jpg(input_dir, output_dir, quality, overwrite, progress)

    if node_name == "Resize Match":
        reference_dir = require_connected_property(node, "reference_folder_path", "folder_path")
        target_dir = require_connected_property(node, "target_folder_path", "folder_path")
        output_dir = require_connected_property(node, "output_folder", "folder_path")
        return lambda progress: resize_folder_to_reference(reference_dir, target_dir, output_dir, bool(node.get_property("overwrite")), progress)

    if node_name == "Resize Image":
        input_dir = require_connected_property(node, "folder_path", "folder_path")
        output_dir = require_connected_property(node, "output_folder", "folder_path")
        return lambda progress: resize_images(
            input_dir,
            output_dir,
            int(node.get_property("target_width")),
            int(node.get_property("target_height")),
            str(node.get_property("output_format")),
            str(node.get_property("resize_mode")),
            bool(node.get_property("overwrite")),
            progress,
        )

    if node_name == "Prompt Batch Generate":
        prompt = require_connected_property(node, "prompt", "prompt_text")
        output_dir = require_connected_property(node, "output_folder", "folder_path")
        return lambda progress: generate_prompt_files(
            prompt,
            int(node.get_property("count")),
            output_dir,
            str(node.get_property("filename_prefix") or ""),
            progress,
        )

    if node_name == "Img2Img":
        input_dir = require_connected_property(node, "folder_path", "folder_path")
        prompt = require_connected_property(node, "prompt", "prompt_text")
        output_dir = require_connected_property(node, "output_folder", "folder_path")
        token = stop_token or StopToken()
        return lambda progress: asyncio.run(
            generate_images_async(
                build_generation_config(node),
                input_dir,
                output_dir,
                prompt,
                bool(node.get_property("only_missing")),
                progress,
                token,
            )
        )

    if node_name == "Text2Img":
        prompt = require_connected_property(node, "prompt", "prompt_text")
        output_dir = require_connected_property(node, "output_folder", "folder_path")
        token = stop_token or StopToken()
        return lambda progress: asyncio.run(
            generate_text_to_images_async(
                build_generation_config(node),
                output_dir,
                prompt,
                int(node.get_property("count")),
                progress,
                token,
            )
        )

    raise NodeExecutionError(f"Node is not executable: {node_name}")
