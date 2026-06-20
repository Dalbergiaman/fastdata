from pathlib import Path
from typing import Callable

from PIL import Image

from fastdata.core.common import ensure_output_dir, get_image_files, should_skip


def convert_image_to_png(input_path: Path, output_dir: Path, overwrite: bool = False) -> dict:
    output_path = output_dir / f"{input_path.stem}.png"
    if should_skip(output_path, overwrite):
        return {"success": True, "skipped": True, "input": str(input_path), "output": str(output_path)}

    try:
        with Image.open(input_path) as image:
            image.convert("RGB").save(output_path, "PNG")
        return {"success": True, "input": str(input_path), "output": str(output_path)}
    except Exception as error:
        return {"success": False, "input": str(input_path), "error": str(error)}


def convert_images_to_png(
    input_dir: str,
    output_dir: str,
    overwrite: bool = False,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict]:
    image_files = get_image_files(input_dir)
    output_path = ensure_output_dir(output_dir)

    if progress_callback:
        progress_callback(0, len(image_files))

    results = []
    for index, image_file in enumerate(image_files, start=1):
        results.append(convert_image_to_png(image_file, output_path, overwrite))
        if progress_callback:
            progress_callback(index, len(image_files))
    return results
