import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


APP_DIR = get_app_dir()
CONFIG_DIR = APP_DIR / "config"
CONFIG_PATH = CONFIG_DIR / "config.json"


def get_default_config() -> dict[str, Any]:
    return {
        "api_key": "",
        "base_url": "https://grsai.dakka.com.cn",
        "model": "nano-banana-2",
        "aspect_ratio": "auto",
        "image_size": "2K",
        "concurrency": 5,
        "poll_interval": 2,
        "max_retries": 300,
        "only_missing": True,
        "prompt": "",
        "theme": "dark",
        "paths": {
            "generation_input": "data/image_generation/input_images",
            "generation_output": "data/image_generation/output_images",
            "convert_input": "data/png_conversion/input_images",
            "convert_output": "data/png_conversion/output_images",
            "resize_reference": "data/resize_match/reference_images",
            "resize_target": "data/resize_match/target_images",
            "resize_match_output": "data/resize_match/output_images",
            "resize_input": "data/resize/input_images",
            "resize_output": "data/resize/output_images",
            "prompt_output": "data/prompt_generation/output_prompts",
        },
    }


def get_config_path() -> Path:
    return CONFIG_PATH


def _deep_merge(defaults: dict[str, Any], overrides: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config() -> dict[str, Any]:
    default_config = get_default_config()
    if not CONFIG_PATH.exists():
        return default_config

    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        config = json.load(file)
    return _deep_merge(default_config, config)


def save_config(config: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=2)


def mask_api_key(api_key: str) -> str:
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "***"
    return f"{api_key[:4]}...{api_key[-4:]}"
