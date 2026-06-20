from enum import StrEnum
from typing import Any

from NodeGraphQt import BaseNode


class NodeStatus(StrEnum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


NODE_COLORS = {
    "input": (64, 70, 84),
    "prompt": (78, 73, 95),
    "generate": (78, 84, 102),
    "image": (79, 86, 104),
    "output": (76, 93, 81),
    "error": (130, 67, 67),
    "running": (104, 94, 68),
    "success": (72, 104, 82),
}


class FastDataNode(BaseNode):
    __identifier__ = "fastdata.nodes"
    NODE_NAME = "FastData Node"
    CATEGORY = "base"

    def __init__(self) -> None:
        super().__init__()
        self._base_color = NODE_COLORS.get(self.CATEGORY, NODE_COLORS["image"])
        self.set_color(*self._base_color)
        self.create_property("status", NodeStatus.IDLE.value)
        self.create_property("last_message", "")

    def set_status(self, status: NodeStatus | str, message: str = "") -> None:
        status_value = status.value if isinstance(status, NodeStatus) else status
        self.set_property("status", status_value)
        self.set_property("last_message", message)

        if status_value == NodeStatus.RUNNING.value:
            self.set_color(*NODE_COLORS["running"])
        elif status_value == NodeStatus.SUCCESS.value:
            self.set_color(*NODE_COLORS["success"])
        elif status_value == NodeStatus.ERROR.value:
            self.set_color(*NODE_COLORS["error"])
        else:
            self.set_color(*self._base_color)

    def parameter_values(self) -> dict[str, Any]:
        builtin_keys = {"name", "color", "disabled", "selected", "visible", "status", "last_message"}
        return {
            key: value
            for key, value in self.properties().items()
            if key not in builtin_keys
        }
