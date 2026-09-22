import asyncio
import base64
from pathlib import Path
from typing import Callable

import aiohttp

from fastdata.core.common import ensure_output_dir, get_image_files, should_skip


class StopToken:
    def __init__(self) -> None:
        self.is_stopped = False

    def stop(self) -> None:
        self.is_stopped = True


async def _interruptible_sleep(seconds: float, stop_token: StopToken | None) -> None:
    if stop_token is None:
        await asyncio.sleep(seconds)
        return
    step = 0.1
    elapsed = 0.0
    while elapsed < seconds:
        if stop_token.is_stopped:
            return
        await asyncio.sleep(min(step, seconds - elapsed))
        elapsed += step


def _require_api_key(config: dict) -> str:
    api_key = config.get("api_key", "")
    if not api_key:
        raise RuntimeError("API Key is not configured.")
    return api_key


def _build_api_url(config: dict) -> str:
    base_url = config.get("base_url", "https://grsai.dakka.com.cn").rstrip("/")
    return f"{base_url}/v1/api/generate"


def _result_url(api_url: str) -> str:
    return api_url.replace("/v1/api/generate", "/v1/api/result")


def _generation_payload(config: dict, prompt: str, images: list[str] | None = None) -> dict:
    model = config.get("model", "nano-banana-2")
    payload = {
        "model": model,
        "prompt": prompt,
        "aspectRatio": config.get("aspect_ratio", "auto"),
        "replyType": "async",
    }
    if images is not None:
        payload["images"] = images
    # gpt-image-2 uses aspectRatio (ratio or pixel value) for resolution and
    # does not accept imageSize; banana-family models keep imageSize.
    if not model.startswith("gpt-image"):
        payload["imageSize"] = config.get("image_size", "2K")
    return payload


def _encode_image(image_path: Path) -> str:
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


async def _submit_task(session: aiohttp.ClientSession, api_url: str, headers: dict, payload: dict) -> str:
    async with session.post(api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
        if response.status != 200:
            raise RuntimeError(f"Submit task HTTP {response.status}")
        result = await response.json()
    task_id = result.get("id")
    if not task_id:
        raise RuntimeError("Submit task response did not include id.")
    return task_id


async def _poll_task(
    session: aiohttp.ClientSession,
    result_url: str,
    headers: dict,
    task_id: str,
    poll_interval: int,
    max_retries: int,
    stop_token: StopToken | None = None,
) -> str:
    for _ in range(max_retries):
        if stop_token and stop_token.is_stopped:
            raise RuntimeError("Task stopped by user.")
        await _interruptible_sleep(poll_interval, stop_token)
        if stop_token and stop_token.is_stopped:
            raise RuntimeError("Task stopped by user.")
        async with session.get(
            result_url,
            headers=headers,
            params={"id": task_id},
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            if response.status != 200:
                continue
            result = await response.json()
        status = result.get("status")
        if status == "succeeded":
            results = result.get("results") or []
            if not results or not results[0].get("url"):
                # Some providers expose the terminal status before the image
                # URL is populated. Keep polling until the retry budget is
                # exhausted instead of failing the item immediately.
                continue
            return results[0]["url"]
        if status in {"failed", "violation"}:
            raise RuntimeError(f"Task {status}: {result.get('error', status)}")
    raise RuntimeError("Timeout waiting for result.")


async def _download_image(session: aiohttp.ClientSession, image_url: str, output_path: Path) -> None:
    async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=60)) as response:
        if response.status != 200:
            raise RuntimeError(f"Download image HTTP {response.status}")
        output_path.write_bytes(await response.read())


async def _run_payload(
    session: aiohttp.ClientSession,
    api_url: str,
    headers: dict,
    payload: dict,
    output_path: Path,
    config: dict,
    stop_token: StopToken | None = None,
) -> dict:
    try:
        task_id = await _submit_task(session, api_url, headers, payload)
        image_url = await _poll_task(
            session,
            _result_url(api_url),
            headers,
            task_id,
            int(config.get("poll_interval", 2)),
            int(config.get("max_retries", 300)),
            stop_token,
        )
        await _download_image(session, image_url, output_path)
        return {"success": True, "output": str(output_path)}
    except Exception as error:
        return {"success": False, "output": str(output_path), "error": str(error)}


async def generate_images_async(
    config: dict,
    input_dir: str,
    output_dir: str,
    prompt: str,
    only_missing: bool = True,
    progress_callback: Callable[[int, int], None] | None = None,
    stop_token: StopToken | None = None,
) -> list[dict]:
    all_image_files = get_image_files(input_dir)
    output_path = ensure_output_dir(output_dir)
    skipped_results = [
        {
            "success": True,
            "skipped": True,
            "input": str(image_file),
            "output": str(output_path / image_file.name),
        }
        for image_file in all_image_files
        if only_missing and should_skip(output_path / image_file.name, overwrite=False)
    ]
    image_files = [
        image_file
        for image_file in all_image_files
        if not (only_missing and should_skip(output_path / image_file.name, overwrite=False))
    ]

    if not image_files:
        if progress_callback:
            progress_callback(len(skipped_results), len(all_image_files))
        return skipped_results

    api_key = _require_api_key(config)
    api_url = _build_api_url(config)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    semaphore = asyncio.Semaphore(int(config.get("concurrency", 5)))

    if progress_callback:
        progress_callback(len(skipped_results), len(all_image_files))

    completed = len(skipped_results)

    async def process(image_file: Path) -> dict:
        nonlocal completed
        async with semaphore:
            payload = _generation_payload(config, prompt, [_encode_image(image_file)])
            result = await _run_payload(session, api_url, headers, payload, output_path / image_file.name, config, stop_token)
            result["input"] = str(image_file)
            completed += 1
            if progress_callback:
                progress_callback(completed, len(all_image_files))
            return result

    async with aiohttp.ClientSession() as session:
        processed_results = await asyncio.gather(*(process(image_file) for image_file in image_files))
    return skipped_results + processed_results


async def generate_images_with_reference_async(
    config: dict,
    input_dir: str,
    reference_image_path: str,
    output_dir: str,
    prompt: str,
    only_missing: bool = True,
    progress_callback: Callable[[int, int], None] | None = None,
    stop_token: StopToken | None = None,
) -> list[dict]:
    source_files = get_image_files(input_dir)
    if not source_files:
        raise ValueError("No input images found.")

    reference_path = Path(reference_image_path)
    if not reference_path.is_file():
        raise ValueError(f"Reference image does not exist: {reference_path}")

    output_path = ensure_output_dir(output_dir)
    skipped_results = [
        {
            "success": True,
            "skipped": True,
            "input": str(image_file),
            "output": str(output_path / image_file.name),
        }
        for image_file in source_files
        if only_missing and should_skip(output_path / image_file.name, overwrite=False)
    ]
    image_files = [
        image_file
        for image_file in source_files
        if not (only_missing and should_skip(output_path / image_file.name, overwrite=False))
    ]
    if not image_files:
        if progress_callback:
            progress_callback(len(skipped_results), len(source_files))
        return skipped_results

    api_key = _require_api_key(config)
    api_url = _build_api_url(config)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    semaphore = asyncio.Semaphore(int(config.get("concurrency", 5)))
    reference_image = _encode_image(reference_path)
    completed = len(skipped_results)

    if progress_callback:
        progress_callback(completed, len(source_files))

    async def process(image_file: Path) -> dict:
        nonlocal completed
        async with semaphore:
            payload = _generation_payload(config, prompt, [_encode_image(image_file), reference_image])
            result = await _run_payload(session, api_url, headers, payload, output_path / image_file.name, config, stop_token)
            result["input"] = str(image_file)
            result["reference"] = str(reference_path)
            completed += 1
            if progress_callback:
                progress_callback(completed, len(source_files))
            return result

    async with aiohttp.ClientSession() as session:
        processed_results = await asyncio.gather(*(process(image_file) for image_file in image_files))
    return skipped_results + processed_results


async def generate_text_to_images_async(
    config: dict,
    output_dir: str,
    prompt: str,
    count: int = 1,
    progress_callback: Callable[[int, int], None] | None = None,
    stop_token: StopToken | None = None,
) -> list[dict]:
    if count <= 0:
        raise ValueError("count must be a positive integer.")

    api_key = _require_api_key(config)
    output_path = ensure_output_dir(output_dir)
    api_url = _build_api_url(config)
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    semaphore = asyncio.Semaphore(int(config.get("concurrency", 5)))

    if progress_callback:
        progress_callback(0, count)

    completed = 0

    async def process(index: int) -> dict:
        nonlocal completed
        async with semaphore:
            payload = _generation_payload(config, prompt)
            result = await _run_payload(session, api_url, headers, payload, output_path / f"{index}.png", config, stop_token)
            completed += 1
            if progress_callback:
                progress_callback(completed, count)
            return result

    async with aiohttp.ClientSession() as session:
        return await asyncio.gather(*(process(index) for index in range(1, count + 1)))
