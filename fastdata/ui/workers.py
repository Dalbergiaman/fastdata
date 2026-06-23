import asyncio
from pathlib import Path
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


EXECUTABLE_NODE_NAMES = {
    "Image To PNG",
    "Image To JPG",
    "Resize Match",
    "Resize Image",
    "Prompt Batch Generate",
    "Img2Img",
    "Text2Img",
}


class NodeWorker(QtCore.QObject):
    progress = QtCore.Signal(str, int, int)
    finished = QtCore.Signal(object)
    failed = QtCore.Signal(str)

    def __init__(self, node: FastDataNode, runner: Callable[[Callable[[str, int, int], None]], Any]) -> None:
        super().__init__()
        self.node = node
        self.runner = runner

    @QtCore.Slot()
    def run(self) -> None:
        try:
            result = self.runner(lambda label, current, total: self.progress.emit(label, current, total))
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


def node_type_name(node: FastDataNode) -> str:
    return getattr(type(node), "NODE_NAME", node.name())


def is_executable_node(node: FastDataNode) -> bool:
    return node_type_name(node) in EXECUTABLE_NODE_NAMES


def require_connected_property(node: FastDataNode, input_name: str, property_name: str) -> Any:
    source = connected_node(node, input_name)
    if source is None:
        raise NodeExecutionError(f"Missing connection: {input_name}")
    value = source.get_property(property_name)
    if value in (None, ""):
        raise NodeExecutionError(f"Missing value: {source.name()} / {property_name}")
    return value


def result_output_dir(result: Any) -> str | None:
    if not isinstance(result, list):
        return None
    output_paths = [
        Path(item["output"])
        for item in result
        if isinstance(item, dict) and item.get("output")
    ]
    if not output_paths:
        return None
    return str(output_paths[0].parent)


def resolve_folder_input(node: FastDataNode, input_name: str, context: dict[int, Any]) -> str:
    source = connected_node(node, input_name)
    if source is None:
        raise NodeExecutionError(f"Missing connection: {input_name}")

    folder_path = source.get_property("folder_path") if source.has_property("folder_path") else None
    if folder_path:
        return str(folder_path)

    output_dir = result_output_dir(context.get(id(source)))
    if output_dir:
        return output_dir

    raise NodeExecutionError(f"Missing folder input from: {source.name()}")


def resolve_prompt_input(node: FastDataNode, input_name: str) -> str:
    source = connected_node(node, input_name)
    if source is None:
        raise NodeExecutionError(f"Missing connection: {input_name}")
    prompt = source.get_property("prompt_text") if source.has_property("prompt_text") else None
    if not prompt:
        raise NodeExecutionError(f"Missing prompt from: {source.name()}")
    return str(prompt)


def build_generation_config(node: FastDataNode) -> dict[str, Any]:
    config = load_config()
    for key in (
        "model",
        "aspect_ratio",
        "image_size",
        "only_missing",
    ):
        if node.has_property(key):
            config[key] = node.get_property(key)
    return config


def build_node_runner(
    node: FastDataNode,
    stop_token: StopToken | None = None,
    context: dict[int, Any] | None = None,
) -> Callable[[Callable[[int, int], None]], Any]:
    context = context if context is not None else {}
    node_name = node_type_name(node)

    if node_name == "Image To PNG":
        input_dir = resolve_folder_input(node, "folder_path", context)
        output_dir = require_connected_property(node, "output_folder", "folder_path")
        return lambda progress: convert_images_to_png(input_dir, output_dir, bool(node.get_property("overwrite")), progress)

    if node_name == "Image To JPG":
        input_dir = resolve_folder_input(node, "folder_path", context)
        output_dir = require_connected_property(node, "output_folder", "folder_path")
        quality = int(node.get_property("quality"))
        overwrite = bool(node.get_property("overwrite"))
        return lambda progress: convert_images_to_jpg(input_dir, output_dir, quality, overwrite, progress)

    if node_name == "Resize Match":
        reference_dir = resolve_folder_input(node, "reference_folder_path", context)
        target_dir = resolve_folder_input(node, "target_folder_path", context)
        output_dir = require_connected_property(node, "output_folder", "folder_path")
        return lambda progress: resize_folder_to_reference(reference_dir, target_dir, output_dir, bool(node.get_property("overwrite")), progress)

    if node_name == "Resize Image":
        input_dir = resolve_folder_input(node, "folder_path", context)
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
        prompt = resolve_prompt_input(node, "prompt")
        output_dir = require_connected_property(node, "output_folder", "folder_path")
        return lambda progress: generate_prompt_files(
            prompt,
            int(node.get_property("count")),
            output_dir,
            str(node.get_property("filename_prefix") or ""),
            progress,
        )

    if node_name == "Img2Img":
        input_dir = resolve_folder_input(node, "folder_path", context)
        prompt = resolve_prompt_input(node, "prompt")
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
        prompt = resolve_prompt_input(node, "prompt")
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


def upstream_nodes(node: FastDataNode) -> list[FastDataNode]:
    sources = []
    for port in node.inputs().values():
        for connected_port in port.connected_ports():
            sources.append(connected_port.node())
    return sources


def build_execution_plan(target_node: FastDataNode) -> list[FastDataNode]:
    if not is_executable_node(target_node):
        raise NodeExecutionError(f"Node is not executable: {target_node.name()}")

    plan = []
    visiting = set()
    visited = set()

    def visit(node: FastDataNode) -> None:
        node_key = id(node)
        if node_key in visiting:
            raise NodeExecutionError("Cycle detected in workflow.")
        if node_key in visited:
            return
        visiting.add(node_key)
        for source in upstream_nodes(node):
            if is_executable_node(source):
                visit(source)
        visiting.remove(node_key)
        visited.add(node_key)
        if is_executable_node(node):
            plan.append(node)

    visit(target_node)
    return plan


def execute_node_sequence(
    nodes: list[FastDataNode],
    stop_token: StopToken,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> dict[str, Any]:
    context: dict[int, Any] = {}
    results = []
    total_nodes = len(nodes)
    for index, node in enumerate(nodes, start=1):
        if stop_token.is_stopped:
            raise NodeExecutionError("Task stopped by user.")
        node_label = node.name()
        if progress_callback:
            progress_callback(node_label, 0, 1)
        runner = build_node_runner(node, stop_token, context)
        result = runner(
            lambda current, total: progress_callback(node_label, current, total)
            if progress_callback
            else None
        )
        context[id(node)] = result
        results.append({"node": node.name(), "result": result})
        if progress_callback:
            progress_callback("Workflow", index, total_nodes)
    return {"results": results, "last_result": results[-1]["result"] if results else None}
