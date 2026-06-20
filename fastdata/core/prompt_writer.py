from pathlib import Path
from typing import Callable


def generate_prompt_files(
    prompt: str,
    count: int,
    output_dir: str,
    filename_prefix: str = "",
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict]:
    if count <= 0:
        raise ValueError("count must be a positive integer.")

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback(0, count)

    results = []
    for index in range(1, count + 1):
        file_path = output_path / f"{filename_prefix}{index}.txt"
        try:
            file_path.write_text(prompt, encoding="utf-8")
            results.append({"success": True, "output": str(file_path)})
        except Exception as error:
            results.append({"success": False, "output": str(file_path), "error": str(error)})
        if progress_callback:
            progress_callback(index, count)
    return results
