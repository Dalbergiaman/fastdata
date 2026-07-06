import asyncio
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from PySide6 import QtCore

# aiohttp's ClientSession cleanup can hang on Windows' default ProactorEventLoop.
# SelectorEventLoop is the recommended loop for aiohttp on Windows.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

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
    "img2img-banana",
    "img2img-gpt",
    "Text2Img",
}


NODE_INPUTS: dict[str, list[str]] = {
    "Image To PNG": ["folder_path", "output_folder"],
    "Image To JPG": ["folder_path", "output_folder"],
    "Resize Match": ["reference_folder_path", "target_folder_path", "output_folder"],
    "Resize Image": ["folder_path", "output_folder"],
    "Prompt Batch Generate": ["prompt", "output_folder"],
    "img2img-banana": ["folder_path", "output_folder", "prompt"],
    "img2img-gpt": ["folder_path", "output_folder", "prompt"],
    "Text2Img": ["prompt", "output_folder"],
}

NODE_PARAMS: dict[str, list[str]] = {
    "Image To PNG": ["overwrite"],
    "Image To JPG": ["quality", "overwrite"],
    "Resize Match": ["overwrite"],
    "Resize Image": ["target_width", "target_height", "output_format", "resize_mode", "overwrite"],
    "Prompt Batch Generate": ["count", "filename_prefix"],
    "img2img-banana": ["model", "aspect_ratio", "image_size", "only_missing"],
    "img2img-gpt": ["model", "aspect_ratio", "only_missing"],
    "Text2Img": ["model", "aspect_ratio", "image_size", "count"],
}


@dataclass
class NodeSnapshot:
    name: str
    type_name: str
    params: dict[str, Any] = field(default_factory=dict)
    static_inputs: dict[str, str] = field(default_factory=dict)
    upstream_inputs: dict[str, int] = field(default_factory=dict)


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
        last_emit = 0.0

        def progress_cb(label: str, current: int, total: int) -> None:
            nonlocal last_emit
            now = time.monotonic()
            # Always emit the final tick; otherwise throttle to ~10 Hz so a large
            # batch does not flood the main thread's event queue.
            if current == total or now - last_emit >= 0.1:
                last_emit = now
                self.progress.emit(label, current, total)

        try:
            result = self.runner(progress_cb)
            self.finished.emit(result)
        except BaseException as error:  # noqa: BLE001 — guarantee failed/cleanup always fires
            self.failed.emit(str(error) or "Task aborted.")


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


def resolve_folder_input(snap: NodeSnapshot, input_name: str, context: dict[int, Any]) -> str:
    value = snap.static_inputs.get(input_name)
    if value:
        return value
    if input_name in snap.upstream_inputs:
        output_dir = result_output_dir(context.get(snap.upstream_inputs[input_name]))
        if output_dir:
            return output_dir
    raise NodeExecutionError(f"Missing folder input: {input_name}")


def resolve_output_folder(snap: NodeSnapshot, input_name: str) -> str:
    value = snap.static_inputs.get(input_name)
    if value:
        return value
    raise NodeExecutionError(f"Missing output folder: {input_name}")


def resolve_prompt_input(snap: NodeSnapshot, input_name: str) -> str:
    value = snap.static_inputs.get(input_name)
    if value:
        return value
    raise NodeExecutionError(f"Missing prompt: {input_name}")


def build_generation_config(snap: NodeSnapshot) -> dict[str, Any]:
    config = load_config()
    for key in ("model", "aspect_ratio", "image_size", "only_missing"):
        if key in snap.params:
            config[key] = snap.params[key]
    return config


def build_node_runner(
    snap: NodeSnapshot,
    stop_token: StopToken | None = None,
    context: dict[int, Any] | None = None,
) -> Callable[[Callable[[int, int], None]], Any]:
    context = context if context is not None else {}
    node_name = snap.type_name

    if node_name == "Image To PNG":
        input_dir = resolve_folder_input(snap, "folder_path", context)
        output_dir = resolve_output_folder(snap, "output_folder")
        overwrite = bool(snap.params.get("overwrite"))
        return lambda progress: convert_images_to_png(input_dir, output_dir, overwrite, progress)

    if node_name == "Image To JPG":
        input_dir = resolve_folder_input(snap, "folder_path", context)
        output_dir = resolve_output_folder(snap, "output_folder")
        quality = int(snap.params.get("quality"))
        overwrite = bool(snap.params.get("overwrite"))
        return lambda progress: convert_images_to_jpg(input_dir, output_dir, quality, overwrite, progress)

    if node_name == "Resize Match":
        reference_dir = resolve_folder_input(snap, "reference_folder_path", context)
        target_dir = resolve_folder_input(snap, "target_folder_path", context)
        output_dir = resolve_output_folder(snap, "output_folder")
        overwrite = bool(snap.params.get("overwrite"))
        return lambda progress: resize_folder_to_reference(reference_dir, target_dir, output_dir, overwrite, progress)

    if node_name == "Resize Image":
        input_dir = resolve_folder_input(snap, "folder_path", context)
        output_dir = resolve_output_folder(snap, "output_folder")
        return lambda progress: resize_images(
            input_dir,
            output_dir,
            int(snap.params.get("target_width")),
            int(snap.params.get("target_height")),
            str(snap.params.get("output_format")),
            str(snap.params.get("resize_mode")),
            bool(snap.params.get("overwrite")),
            progress,
        )

    if node_name == "Prompt Batch Generate":
        prompt = resolve_prompt_input(snap, "prompt")
        output_dir = resolve_output_folder(snap, "output_folder")
        count = int(snap.params.get("count"))
        prefix = str(snap.params.get("filename_prefix") or "")
        return lambda progress: generate_prompt_files(prompt, count, output_dir, prefix, progress)

    if node_name in ("img2img-banana", "img2img-gpt"):
        input_dir = resolve_folder_input(snap, "folder_path", context)
        prompt = resolve_prompt_input(snap, "prompt")
        output_dir = resolve_output_folder(snap, "output_folder")
        token = stop_token or StopToken()
        only_missing = bool(snap.params.get("only_missing"))
        config = build_generation_config(snap)
        return lambda progress: asyncio.run(
            generate_images_async(config, input_dir, output_dir, prompt, only_missing, progress, token)
        )

    if node_name == "Text2Img":
        prompt = resolve_prompt_input(snap, "prompt")
        output_dir = resolve_output_folder(snap, "output_folder")
        token = stop_token or StopToken()
        count = int(snap.params.get("count"))
        config = build_generation_config(snap)
        return lambda progress: asyncio.run(
            generate_text_to_images_async(config, output_dir, prompt, count, progress, token)
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


def build_snapshots(plan: list[FastDataNode]) -> list[NodeSnapshot]:
    # Snapshot node params and connections on the main thread so the worker
    # never touches NodeGraphQt (which is not thread-safe).
    snapshots: list[NodeSnapshot] = []
    for node in plan:
        type_name = node_type_name(node)
        params = {key: node.get_property(key) for key in NODE_PARAMS.get(type_name, [])}
        static_inputs: dict[str, str] = {}
        upstream_inputs: dict[str, int] = {}
        for input_name in NODE_INPUTS.get(type_name, []):
            source = connected_node(node, input_name)
            if source is None:
                continue
            if source.has_property("folder_path"):
                static_inputs[input_name] = str(source.get_property("folder_path") or "")
            elif source.has_property("prompt_text"):
                static_inputs[input_name] = str(source.get_property("prompt_text") or "")
            else:
                for src_index, src_node in enumerate(plan):
                    if src_node is source:
                        upstream_inputs[input_name] = src_index
                        break
        snapshots.append(NodeSnapshot(node.name(), type_name, params, static_inputs, upstream_inputs))
    return snapshots


def execute_node_sequence(
    snapshots: list[NodeSnapshot],
    stop_token: StopToken,
    progress_callback: Callable[[str, int, int], None] | None = None,
) -> dict[str, Any]:
    context: dict[int, Any] = {}
    results = []
    total_nodes = len(snapshots)
    for index, snap in enumerate(snapshots):
        if stop_token.is_stopped:
            raise NodeExecutionError("Task stopped by user.")
        node_label = snap.name
        if progress_callback:
            progress_callback(node_label, 0, 1)
        runner = build_node_runner(snap, stop_token, context)
        result = runner(
            lambda current, total: progress_callback(node_label, current, total)
            if progress_callback
            else None
        )
        context[index] = result
        results.append({"node": snap.name, "result": result})
        if progress_callback:
            progress_callback("Workflow", index + 1, total_nodes)
    return {"results": results, "last_result": results[-1]["result"] if results else None}
