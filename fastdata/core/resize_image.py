from pathlib import Path
from typing import Callable

from PIL import Image, ImageOps

from fastdata.core.common import ensure_output_dir, get_image_files, should_skip


OUTPUT_FORMATS = {"png", "jpg", "keep"}
RESIZE_MODES = {"stretch", "fit", "fill_crop"}


def _get_output_path(input_path: Path, output_dir: Path, output_format: str) -> Path:
    if output_format == "keep":
        suffix = input_path.suffix.lower()
        if suffix in {".jpeg"}:
            suffix = ".jpg"
        if suffix not in {".png", ".jpg"}:
            suffix = ".png"
    else:
        suffix = ".jpg" if output_format == "jpg" else ".png"
    return output_dir / f"{input_path.stem}{suffix}"


def _resize(image: Image.Image, width: int, height: int, resize_mode: str) -> Image.Image:
    if resize_mode == "stretch":
        return image.resize((width, height), Image.Resampling.LANCZOS)
    if resize_mode == "fit":
        resized = image.copy()
        resized.thumbnail((width, height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (width, height), (255, 255, 255))
        x = (width - resized.width) // 2
        y = (height - resized.height) // 2
        canvas.paste(resized, (x, y))
        return canvas
    return ImageOps.fit(image, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))


def resize_single_image(
    input_path: Path,
    output_dir: Path,
    width: int,
    height: int,
    output_format: str = "png",
    resize_mode: str = "fill_crop",
    overwrite: bool = False,
) -> dict:
    output_path = _get_output_path(input_path, output_dir, output_format)
    if should_skip(output_path, overwrite):
        return {"success": True, "skipped": True, "input": str(input_path), "output": str(output_path)}

    try:
        with Image.open(input_path) as image:
            image = image.convert("RGB")
            resized = _resize(image, width, height, resize_mode)
            if output_path.suffix.lower() == ".jpg":
                resized.save(output_path, "JPEG", quality=95)
            else:
                resized.save(output_path, "PNG")
        return {"success": True, "input": str(input_path), "output": str(output_path)}
    except Exception as error:
        return {"success": False, "input": str(input_path), "error": str(error)}


def resize_images(
    input_dir: str,
    output_dir: str,
    width: int,
    height: int,
    output_format: str = "png",
    resize_mode: str = "fill_crop",
    overwrite: bool = False,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict]:
    if width <= 0 or height <= 0:
        raise ValueError("width and height must be positive integers.")
    if output_format not in OUTPUT_FORMATS:
        raise ValueError(f"output_format must be one of: {', '.join(sorted(OUTPUT_FORMATS))}")
    if resize_mode not in RESIZE_MODES:
        raise ValueError(f"resize_mode must be one of: {', '.join(sorted(RESIZE_MODES))}")

    image_files = get_image_files(input_dir)
    output_path = ensure_output_dir(output_dir)

    if progress_callback:
        progress_callback(0, len(image_files))

    results = []
    for index, image_file in enumerate(image_files, start=1):
        results.append(resize_single_image(image_file, output_path, width, height, output_format, resize_mode, overwrite))
        if progress_callback:
            progress_callback(index, len(image_files))
    return results
