"""Dotifier controller that coordinates view events and model operations."""

from __future__ import annotations
import logging
from pathlib import Path

from PySide6.QtWidgets import QDialog

from model import DotifierModel
from view import ExportPictureDialog, LicenseDialog, ProcessMultiplePicturesDialog


logger = logging.getLogger(__name__)


class DotifierController:
    """Converts user actions into model operations and requests view updates."""

    def __init__(self, model: DotifierModel, view) -> None:
        self.model, self.view = model, view
        self._connect_signals()
        self.view.present_parameters(self.model.parameters_copy())

    def _connect_signals(self) -> None:
        self.view.parametersChanged.connect(self.update_parameters)
        self.view.calculateRequested.connect(self.calculate)
        self.view.importImageRequested.connect(self.import_image)
        self.view.exportImageRequested.connect(self.export_image)
        self.view.importParametersRequested.connect(self.import_parameters)
        self.view.exportParametersRequested.connect(self.export_parameters)
        self.view.batchRequested.connect(self.process_multiple_images)
        self.view.aboutRequested.connect(self.show_about)

    def update_parameters(self) -> None:
        try:
            self.model.set_parameters(self.view.read_parameters())
            if self.model.parameters["preview"] and self.model.original_image is not None:
                self._calculate_and_present()
        except Exception:
            logger.exception("Unable to update parameters")
            self.view.show_error("invalid_parameters")

    def calculate(self) -> None:
        if self.model.parameters["preview"]:
            return
        self._calculate_and_present()

    def _calculate_and_present(self) -> None:
        try:
            self.view.show_image(self.model.calculate())
        except Exception:
            logger.exception("Unable to calculate image")
            self.view.show_error("calculation_failed")

    def import_image(self) -> None:
        path = self.view.choose_open_image()
        if not path:
            return
        try:
            image = self.model.load_image(path)
            if self.model.parameters["preview"]:
                image = self.model.calculate()
            self.view.show_image(image)
        except Exception:
            logger.exception("Unable to import image")
            self.view.show_error("image_import_failed")

    def import_parameters(self) -> None:
        path = self.view.choose_open_parameters()
        if not path:
            return
        try:
            parameters = self.model.load_parameters(path)
            self.model.set_parameters(parameters)
            self.view.present_parameters(parameters)
            if parameters["preview"] and self.model.original_image is not None:
                self._calculate_and_present()
        except Exception:
            logger.exception("Unable to import parameters")
            self.view.show_error("parameter_import_failed")

    def export_parameters(self) -> None:
        path = self.view.choose_save_parameters()
        if not path:
            return
        try:
            self.model.set_parameters(self.view.read_parameters())
            self.model.save_parameters(path, self.model.parameters)
            self.view.show_info("parameters_saved")
        except Exception:
            logger.exception("Unable to export parameters")
            self.view.show_error("parameter_export_failed")

    def export_image(self) -> None:
        if self.model.original_image is None or self.model.current_image is None:
            self.view.show_error("image_required")
            return
        try:
            self.model.set_parameters(self.view.read_parameters())
            recalculated = False
            if self.model.result_is_stale:
                dialog = ExportPictureDialog(self.view)
                if dialog.exec() != QDialog.DialogCode.Accepted:
                    return
                recalculated = dialog.strategy == ExportPictureDialog.RECALCULATE
            path = self.view.choose_save_image()
            if not path:
                return
            image = self.model.calculate() if recalculated else self.model.current_image
            self.model.save_image(path, image)
            self.view.show_info("image_saved")
        except Exception:
            logger.exception("Unable to export image")
            self.view.show_error("image_export_failed")

    def process_multiple_images(self) -> None:
        dialog = ProcessMultiplePicturesDialog(self.view)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            if not dialog.output_folder:
                self.view.show_error("output_folder_required")
                return
            paths = dialog.input_paths
            if dialog.input_folder:
                paths = self.model.image_files(dialog.input_folder)
            if not paths:
                self.view.show_error("input_images_required")
                return
            parameters = self.model.load_parameters(dialog.parameter_path) if dialog.parameter_path else self.view.read_parameters()
            succeeded, failures = self.model.batch_process(paths, dialog.output_folder, parameters)
            self.view.show_info("batch_complete", succeeded=succeeded, failed=len(failures))
        except Exception:
            logger.exception("Unable to batch process images")
            self.view.show_error("batch_processing_failed")

    def show_about(self) -> None:
        license_path = Path(__file__).resolve().parent / "LICENSE"
        with open(license_path, "r", encoding="utf-8") as license_file:
            text = license_file.read()
        LicenseDialog(self.view, text).exec()
        
