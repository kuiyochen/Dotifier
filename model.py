"""Dotifier data model, image processing, and file access."""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any, Iterable

import cv2
import numpy as np


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".bmp"}
logger = logging.getLogger(__name__)


def default_parameters() -> dict[str, Any]:
    return {
        "version": 1.0,
        "mode": 0,
        "scale": 100,
        "discrete_level": 2,
        "pts_density": 2,
        "staggered": True,
        "inversion": False,
        "combo": 0,
        "node_list": [(0.0, 0.0), (0.5, 0.5), (1.0, 1.0)],
        "preview": False,
    }


class ParameterValidationError(ValueError):
    """Raised when JSON or UI parameters do not match the Dotifier format."""


class DotifierModel:
    """Stores application state and provides Qt-independent business logic."""

    def __init__(self) -> None:
        self.parameters = default_parameters()
        self.original_image: np.ndarray | None = None
        self.current_image: np.ndarray | None = None
        self.last_calculated_parameters: dict[str, Any] | None = None

    @staticmethod
    def validate_parameters(parameters: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(parameters, dict):
            raise ParameterValidationError("Parameters must be a JSON object.")

        required = set(default_parameters())
        missing = required - set(parameters)
        if missing:
            raise ParameterValidationError(f"Parameters are missing fields: {', '.join(sorted(missing))}")
        if float(parameters["version"]) >= 2.0:
            raise ParameterValidationError("Only parameter files with a version below 2.0 are supported.")
        if int(parameters["mode"]) not in (0, 1, 2):
            raise ParameterValidationError("mode must be 0, 1, or 2.")
        if not 10 <= int(parameters["scale"]) <= 500:
            raise ParameterValidationError("scale must be between 10 and 500.")
        if int(parameters["discrete_level"]) < 2 or int(parameters["pts_density"]) < 2:
            raise ParameterValidationError("discrete_level and pts_density must both be at least 2.")
        if not 0 <= int(parameters["combo"]) <= 4:
            raise ParameterValidationError("combo must be between 0 and 4.")

        try:
            nodes = [(float(x), float(y)) for x, y in parameters["node_list"]]
        except (TypeError, ValueError) as exc:
            raise ParameterValidationError("node_list has an invalid format.") from exc
        if len(nodes) < 2 or nodes[0][0] != 0.0 or nodes[-1][0] != 1.0:
            raise ParameterValidationError("Curve nodes must start at x=0 and end at x=1.")
        if any(not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0) for x, y in nodes):
            raise ParameterValidationError("Curve node values must be between 0 and 1.")
        if any(nodes[index][0] >= nodes[index + 1][0] for index in range(len(nodes) - 1)):
            raise ParameterValidationError("Curve node x values must be strictly increasing.")

        validated = copy.deepcopy(parameters)
        validated["version"] = float(validated["version"])
        validated["mode"] = int(validated["mode"])
        validated["scale"] = int(validated["scale"])
        validated["discrete_level"] = int(validated["discrete_level"])
        validated["pts_density"] = int(validated["pts_density"])
        validated["combo"] = int(validated["combo"])
        validated["staggered"] = bool(validated["staggered"])
        validated["inversion"] = bool(validated["inversion"])
        validated["preview"] = bool(validated["preview"])
        validated["node_list"] = nodes
        return validated

    def set_parameters(self, parameters: dict[str, Any]) -> None:
        self.parameters = self.validate_parameters(parameters)

    def parameters_copy(self) -> dict[str, Any]:
        return copy.deepcopy(self.parameters)

    @staticmethod
    def output_signature(parameters: dict[str, Any]) -> tuple[Any, ...]:
        return tuple(
            parameters[key]
            for key in ("mode", "scale", "discrete_level", "pts_density", "staggered", "inversion", "node_list")
        )

    @property
    def result_is_stale(self) -> bool:
        return self.current_image is None or self.last_calculated_parameters is None or (
            self.output_signature(self.parameters) != self.output_signature(self.last_calculated_parameters)
        )

    def load_image(self, file_path: str) -> np.ndarray:
        image = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Unable to read image: {file_path}")
        self.original_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self.current_image = self.original_image.copy()
        self.last_calculated_parameters = {**self.parameters_copy(), "mode": 0}
        return self.current_image.copy()

    def calculate(self, parameters: dict[str, Any] | None = None) -> np.ndarray:
        if self.original_image is None:
            raise ValueError("Import an image before calculating.")
        active = self.validate_parameters(parameters or self.parameters)
        result = self.dotify(active, self.original_image)
        self.current_image = result.copy()
        self.last_calculated_parameters = copy.deepcopy(active)
        return result

    @staticmethod
    def line_function(nodes: Iterable[Iterable[float]]):
        points = np.asarray(list(nodes), dtype=float)
        points = points[np.argsort(points[:, 0])]
        return lambda values: np.interp(values, points[:, 0] * 255, points[:, 1] * 255)

    @staticmethod
    def levelize(image: np.ndarray, levels: int) -> np.ndarray:
        result = np.floor(image * (levels / 255)) * (255 / levels)
        return np.clip(result, 0, 255).astype(np.uint8)

    def dotify(self, parameters: dict[str, Any], image: np.ndarray) -> np.ndarray:
        parameters = self.validate_parameters(parameters)
        if parameters["mode"] == 0:
            return image.copy()
        result = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        scale = parameters["scale"] / 100.0
        result = cv2.resize(
            result,
            None,
            fx=scale,
            fy=scale,
            interpolation=cv2.INTER_AREA if scale <= 1 else cv2.INTER_CUBIC,
        )
        result = self.line_function(parameters["node_list"])(result).astype(np.uint8)
        if parameters["discrete_level"] > 2:
            result = self.levelize(result, parameters["discrete_level"])
        else:
            _, result = cv2.threshold(result, 127, 255, cv2.THRESH_BINARY)

        if parameters["mode"] == 2:
            levels = sorted(np.unique(result).tolist())
            sheets = np.zeros((len(levels), *result.shape), dtype=np.uint8)
            sheets[-1] = 255
            density = parameters["pts_density"]
            for level_index in range(1, len(levels) - 1):
                radius = len(levels) - level_index - 2
                for row_index, y in enumerate(range(0, result.shape[0], density)):
                    shift = density // 2 if parameters["staggered"] and row_index % 2 else 0
                    for x in range(0, result.shape[1], density):
                        cv2.circle(sheets[len(levels) - 1 - level_index], (x + shift, y), radius, 255, -1)
            for index, level in enumerate(levels):
                mask = result == level
                result[mask] = sheets[index][mask]
        if parameters["inversion"]:
            result = 255 - result
        return result

    def load_parameters(self, file_path: str) -> dict[str, Any]:
        with open(file_path, "r", encoding="utf-8") as source:
            parameters = self.validate_parameters(json.load(source))
        return parameters

    def save_parameters(self, file_path: str, parameters: dict[str, Any]) -> None:
        with open(file_path, "w", encoding="utf-8") as target:
            json.dump(self.validate_parameters(parameters), target, ensure_ascii=False, indent=4)

    @staticmethod
    def save_image(file_path: str, image: np.ndarray) -> None:
        output = cv2.cvtColor(image, cv2.COLOR_RGB2BGR) if image.ndim == 3 else image
        success, encoded_img = cv2.imencode(file_path, output)
        if not success:
            raise ValueError(f"Unable to save image: {file_path}")
        encoded_img.tofile(file_path)

    @staticmethod
    def image_files(folder: str) -> list[str]:
        return [str(path) for path in Path(folder).iterdir() if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES]

    def batch_process(self, input_paths: Iterable[str], output_folder: str, parameters: dict[str, Any]) -> tuple[int, list[str]]:
        active = self.validate_parameters(parameters)
        output = Path(output_folder)
        if not output.is_dir():
            raise ValueError("The output folder does not exist.")
        succeeded, failures = 0, []
        for input_path in input_paths:
            try:
                raw = cv2.imdecode(np.fromfile(input_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                if raw is None:
                    raise ValueError("Unable to read image.")
                image = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)
                result = self.dotify(active, image)
                path = Path(input_path)
                self.save_image(str(output / f"{path.stem}_processed{path.suffix}"), result)
                succeeded += 1
            except Exception as exc:  # individual files must not abort a batch
                logger.exception("Unable to process batch image: %s", input_path)
                failures.append(f"{input_path}: {exc}")
        return succeeded, failures
