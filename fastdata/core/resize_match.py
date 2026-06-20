from pathlib import Path
from typing import Callable

from PIL import Image

from fastdata.core.common import IMAGE_EXTENSIONS, should_skip


def get_image_file_map(directory: str | Path) -> dict[str, Path]:
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"图片目录不存在：{path}")
    if not path.is_dir():
        raise NotADirectoryError(f"输入路径不是文件夹：{path}")
    return {
        file.name: file
        for file in path.iterdir()
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS
    }


def resize_image_to_reference(target_image_path: Path, reference_image_path: Path, output_path: Path) -> dict:
    try:
        with Image.open(reference_image_path) as reference_image:
            reference_width, reference_height = reference_image.size

        with Image.open(target_image_path) as target_image:
            target_image = target_image.convert("RGB")
            target_width, target_height = target_image.size
            scale = max(reference_width / target_width, reference_height / target_height)
            resized_width = round(target_width * scale)
            resized_height = round(target_height * scale)
            resized_image = target_image.resize((resized_width, resized_height), Image.Resampling.LANCZOS)

            left = (resized_width - reference_width) // 2
            top = (resized_height - reference_height) // 2
            cropped_image = resized_image.crop((left, top, left + reference_width, top + reference_height))

            output_path.parent.mkdir(parents=True, exist_ok=True)
            cropped_image.save(output_path)

        return {"success": True, "input": str(target_image_path), "output": str(output_path)}
    except Exception as error:
        return {"success": False, "input": str(target_image_path), "error": str(error)}


def resize_folder_to_reference(
    reference_dir: str,
    target_dir: str,
    output_dir: str,
    overwrite: bool = False,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict]:
    reference_files = get_image_file_map(reference_dir)
    target_files = get_image_file_map(target_dir)
    matched_names = sorted(set(reference_files) & set(target_files))
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback(0, len(matched_names))

    results = []
    for index, filename in enumerate(matched_names, start=1):
        result_path = output_path / filename
        if should_skip(result_path, overwrite):
            results.append({"success": True, "skipped": True, "input": str(target_files[filename]), "output": str(result_path)})
        else:
            results.append(resize_image_to_reference(target_files[filename], reference_files[filename], result_path))
        if progress_callback:
            progress_callback(index, len(matched_names))
    return results
