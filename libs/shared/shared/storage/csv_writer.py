"""CSV writer/reader for tabular experiment results.

Uses Pydantic model_dump for serialization, CSV for git-friendly line-per-record format.
"""

import csv
from pathlib import Path
from typing import List, Sequence, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def save_csv(rows: Sequence[BaseModel], path: str | Path) -> Path:
    """Save a list of Pydantic models to a CSV file.

    Each model becomes one row. Field names from the first model's model_fields
    are used as the CSV header. Empty list writes just the header.

    Args:
        rows: List of Pydantic BaseModel instances (same type)
        path: Output file path

    Returns:
        The resolved Path object
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        # Write empty file with no header
        path.write_text("")
        return path

    fieldnames = list(rows[0].model_fields.keys())
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row.model_dump(mode="json"))

    return path


def load_csv(path: str | Path, model_class: Type[T]) -> List[T]:
    """Load a CSV file into a list of Pydantic models.

    Args:
        path: Input file path
        model_class: Pydantic BaseModel subclass

    Returns:
        List of validated model instances
    """
    path = Path(path)
    if path.stat().st_size == 0:
        return []

    results: List[T] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Pydantic handles type coercion from strings
            results.append(model_class.model_validate(row))

    return results
