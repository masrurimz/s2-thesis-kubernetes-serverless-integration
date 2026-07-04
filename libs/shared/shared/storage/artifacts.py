"""YAML artifact writer/reader for experiment metadata and configs.

Uses Pydantic model_dump for serialization, YAML for human-readable output.
"""

from pathlib import Path
from typing import Type, TypeVar

import yaml
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def save_yaml(model: BaseModel, path: str | Path) -> Path:
    """Save a Pydantic model to a YAML file.

    Args:
        model: Pydantic BaseModel instance
        path: Output file path

    Returns:
        The resolved Path object
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = model.model_dump(mode="json")
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return path


def load_yaml(path: str | Path, model_class: Type[T]) -> T:
    """Load a YAML file into a Pydantic model.

    Args:
        path: Input file path
        model_class: Pydantic BaseModel subclass

    Returns:
        Validated model instance
    """
    path = Path(path)
    with open(path) as f:
        data = yaml.safe_load(f)
    return model_class.model_validate(data)
