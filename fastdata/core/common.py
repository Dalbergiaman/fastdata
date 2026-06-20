from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tiff", ".tif"}


def get_image_files(directory: str | Path) -> list[Path]:
    path = Path(directory)
    if not path.exists():
        raise FileNotFoundError(f"输入目录不存在：{path}")
    if not path.is_dir():
        raise NotADirectoryError(f"输入路径不是文件夹：{path}")
    return sorted(
        file
        for file in path.iterdir()
        if file.is_file() and file.suffix.lower() in IMAGE_EXTENSIONS
    )


def ensure_output_dir(output_dir: str | Path) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def should_skip(output_path: Path, overwrite: bool) -> bool:
    return output_path.exists() and not overwrite
