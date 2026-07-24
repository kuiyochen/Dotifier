"""Dotifier Qt view responsible for user input, dialogs, and presentation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide2.QtCore import Property, QPropertyAnimation, Qt, Signal
from PySide2.QtGui import QColor, QPainter
from PySide2.QtWidgets import (
    QAction, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QSplitter, QTextBrowser, QVBoxLayout, QWidget,
)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


DEFAULT_LANGUAGE_MAP = {
    "Dotifier": "Dotifier", "File": "File", "Others": "Others", "About": "About",
    "import_picture": "Import Image", "export_picture": "Export Image",
    "import_parameters": "Import Parameters", "export_parameters": "Export Parameters",
    "process_multiple_pictures": "Batch Process Images", "original_image": "Original",
    "discrete_grayscale": "Grayscale", "dotify": "Dotify", "scale": "Scale (%)",
    "discrete_level": "Grayscale Levels", "points_density": "Dot Spacing",
    "staggered": "Staggered", "inversion": "Invert", "Linear": "Linear",
    "Sigmoid_like": "Sigmoid-like", "Reversed_Sigmoid_like": "Reversed Sigmoid-like",
    "Log_like": "Log-like", "Exp_like": "Exp-like", "undo": "Undo", "redo": "Redo",
    "preview": "Live Preview", "calculate": "Calculate", "error_title": "Error",
    "toolbar_home": "Home", "toolbar_back": "Back", "toolbar_forward": "Forward",
    "toolbar_pan": "Pan", "toolbar_zoom": "Zoom", "gamma_map": "Gamma Map",
    "image_file_filter": "Images (*.png *.jpg *.jpeg *.bmp)",
    "save_image_file_filter": "PNG Files (*.png);;JPG Files (*.jpg);;BMP Files (*.bmp)",
    "json_file_filter": "JSON Files (*.json)", "select_image": "Select Image",
    "select_output_image": "Export Image", "select_parameters": "Import Parameters",
    "save_parameters": "Export Parameters", "license_title": "About Dotifier",
    "export_picture_dialog": "The displayed image was not calculated with the latest parameters. Choose an export method:",
    "export_picture_dialog_save_current_img": "Save Displayed Image",
    "export_picture_dialog_save_img_with_current_para": "Recalculate with Current Parameters and Save",
    "process_multiple_pictures_dialog1": "Input:",
    "process_multiple_pictures_dialog1_mode1": "Select Files",
    "process_multiple_pictures_dialog1_mode2": "Select Folder",
    "process_multiple_pictures_dialog2": "Output:",
    "process_multiple_pictures_dialog3": "Parameters:",
    "select_multi_files": "Select Images", "select_input_folder": "Select Input Folder",
    "select_output_folder": "Select Output Folder", "current_parameter": "Use Current Parameters",
    "select_parameter_file": "Import Parameter File", "batch_dialog_title": "Batch Process Images",
    "invalid_parameters": "The parameters are invalid.",
    "calculation_failed": "The image could not be calculated.",
    "image_import_failed": "The image could not be imported.",
    "parameter_import_failed": "The parameter file is invalid or could not be imported.",
    "parameter_export_failed": "The parameters could not be saved.",
    "image_required": "Import an image first.", "image_export_failed": "The image could not be saved.",
    "output_folder_required": "Select an output folder.",
    "input_images_required": "Select at least one image or a folder containing supported images.",
    "batch_complete": "Batch processing complete: {succeeded} succeeded, {failed} failed.",
    "batch_processing_failed": "Batch processing could not be completed.",
    "parameters_saved": "Parameters saved.", "image_saved": "Image saved.",
}


def _load_language_map() -> dict[str, str]:
    """Load local user-facing strings or create the default language file."""
    language_path = Path(__file__).resolve().parent / "language.json"
    if not language_path.exists():
        with language_path.open("w", encoding="utf-8") as target:
            json.dump(DEFAULT_LANGUAGE_MAP, target, ensure_ascii=False, indent=4)
        return DEFAULT_LANGUAGE_MAP.copy()
    try:
        with language_path.open("r", encoding="utf-8") as source:
            translated = json.load(source)
    except (OSError, json.JSONDecodeError):
        translated = {}
    return {**DEFAULT_LANGUAGE_MAP, **translated}


language_map = _load_language_map()
TOOLBAR_KEYS = {
    "Home": "toolbar_home", "Back": "toolbar_back", "Forward": "toolbar_forward",
    "Pan": "toolbar_pan", "Zoom": "toolbar_zoom",
}


def tr(key: str, **values: Any) -> str:
    """Return a localized user-facing string for the supplied key."""
    return language_map.get(key, DEFAULT_LANGUAGE_MAP.get(key, key)).format(**values)


class CustomNavigationToolbar(NavigationToolbar):
    toolitems = [
        (tr(TOOLBAR_KEYS[item[0]]), item[1], item[2], item[3])
        for item in NavigationToolbar.toolitems if item[0] in TOOLBAR_KEYS
    ]


class TriStateToggle(QWidget):
    stateChanged = Signal(int)

    def __init__(self, labels=None, parent=None):
        super().__init__(parent)
        labels = labels or (tr("original_image"), tr("discrete_grayscale"), tr("dotify"))
        self.labels, self._state, self._thumb_pos = labels, 0, 0.0
        self.setMinimumSize(150, 32)
        self.setMaximumSize(1500, 60)
        self._animation = QPropertyAnimation(self, b"thumb_pos", self)
        self._animation.setDuration(150)

    @Property(float)
    def thumb_pos(self):
        return self._thumb_pos

    @thumb_pos.setter
    def thumb_pos(self, value):
        self._thumb_pos = value
        self.update()

    def current_state(self):
        return self._state

    def set_state(self, state):
        state = max(0, min(2, int(state)))
        if state == self._state:
            self._thumb_pos = state / 2.0
            self.update()
            return
        self._state = state
        self._animation.stop()
        self._animation.setStartValue(self._thumb_pos)
        self._animation.setEndValue(state / 2.0)
        self._animation.start()
        self.stateChanged.emit(state)

    def mouseReleaseEvent(self, event):
        width = self.width() / 3
        self.set_state(int(event.pos().x() // width))
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#E5E5EA"))
        painter.drawRoundedRect(rect, rect.height() / 2, rect.height() / 2)
        segment = rect.width() / 3
        thumb = rect.adjusted(int(segment * self._state), 2, -int(segment * (2 - self._state)), -2)
        painter.setBrush(QColor("#007AFF"))
        painter.drawRoundedRect(thumb, max(2, thumb.height() / 2), max(2, thumb.height() / 2))
        for index, label in enumerate(self.labels):
            text_rect = rect.adjusted(int(index * segment), 0, -int((2 - index) * segment), 0)
            painter.setPen(QColor("white") if index == self._state else QColor("#555555"))
            painter.drawText(text_rect, Qt.AlignCenter, label)


class InteractiveCurveCanvas(FigureCanvas):
    coordinatesChanged = Signal()

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(5, 4))
        self.axes = self.figure.add_subplot(111)
        super().__init__(self.figure)
        self.setParent(parent)
        self.xs, self.ys = [0.0, 0.5, 1.0], [0.0, 0.5, 1.0]
        self.undo_stack = [(self.xs.copy(), self.ys.copy())]
        self.redo_stack = []
        self.selected_index = None
        self.dragged = False
        self.axes.set(xlim=(-0.05, 1.05), ylim=(-0.05, 1.05), title=tr("gamma_map"))
        self.axes.grid(True)
        self.line, = self.axes.plot(self.xs, self.ys, "b-", lw=2)
        self.points, = self.axes.plot(self.xs, self.ys, "ro", ms=8, picker=True, pickradius=8)
        self.mpl_connect("button_press_event", self.on_press)
        self.mpl_connect("motion_notify_event", self.on_motion)
        self.mpl_connect("button_release_event", self.on_release)

    @property
    def node_list(self):
        return list(zip(self.xs, self.ys))

    def set_nodes(self, nodes, reset_history=False):
        ordered = sorted((float(x), float(y)) for x, y in nodes)
        self.xs, self.ys = [point[0] for point in ordered], [point[1] for point in ordered]
        if reset_history:
            self.undo_stack, self.redo_stack = [(self.xs.copy(), self.ys.copy())], []
        self.update_plot()

    def update_plot(self):
        self.line.set_data(self.xs, self.ys)
        self.points.set_data(self.xs, self.ys)
        self.draw_idle()

    def save_state(self):
        state = (self.xs.copy(), self.ys.copy())
        if self.undo_stack[-1] != state:
            self.undo_stack.append(state)
            self.redo_stack.clear()

    def undo(self):
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self.xs, self.ys = [*self.undo_stack[-1][0]], [*self.undo_stack[-1][1]]
            self.update_plot()
            self.coordinatesChanged.emit()

    def redo(self):
        if self.redo_stack:
            self.xs, self.ys = [*self.redo_stack[-1][0]], [*self.redo_stack[-1][1]]
            self.undo_stack.append(self.redo_stack.pop())
            self.update_plot()
            self.coordinatesChanged.emit()

    def apply_preset(self, index):
        presets = [
            [(0, 0), (.5, .5), (1, 1)],
            [(0, 0), (.25, .08), (.4, .26), (.5, .5), (.6, .74), (.75, .92), (1, 1)],
            [(0, 0), (.08, .25), (.26, .4), (.5, .5), (.74, .6), (.92, .75), (1, 1)],
            [(0, 0), (.1, .4), (.3, .7), (.6, .9), (1, 1)],
            [(0, 0), (.4, .1), (.7, .3), (.9, .6), (1, 1)],
        ]
        self.set_nodes(presets[index])
        self.save_state()
        self.coordinatesChanged.emit()

    def on_press(self, event):
        if event.inaxes != self.axes:
            return
        contains, attrs = self.points.contains(event)
        if contains:
            index = attrs["ind"][0]
            if event.button == 3 and index not in (0, len(self.xs) - 1):
                self.xs.pop(index); self.ys.pop(index); self.save_state(); self.update_plot(); self.coordinatesChanged.emit()
            else:
                self.selected_index, self.dragged = index, False
        elif event.button == 1 and event.xdata is not None:
            self.xs.append(max(0.0, min(1.0, event.xdata)))
            self.ys.append(max(0.0, min(1.0, event.ydata)))
            pairs = sorted(zip(self.xs, self.ys))
            self.xs, self.ys = [x for x, _ in pairs], [y for _, y in pairs]
            self.save_state(); self.update_plot(); self.coordinatesChanged.emit()

    def on_motion(self, event):
        if self.selected_index is None or event.inaxes != self.axes or event.xdata is None:
            return
        index = self.selected_index
        x, y = max(0.0, min(1.0, event.xdata)), max(0.0, min(1.0, event.ydata))
        if index == 0: x = 0.0
        elif index == len(self.xs) - 1: x = 1.0
        else: x = max(self.xs[index - 1] + .001, min(self.xs[index + 1] - .001, x))
        self.xs[index], self.ys[index], self.dragged = x, y, True
        self.update_plot()

    def on_release(self, event):
        if self.selected_index is not None and self.dragged:
            self.save_state()
            self.coordinatesChanged.emit()
        self.selected_index = None


class LicenseDialog(QDialog):
    def __init__(self, parent, text):
        super().__init__(parent)
        self.setWindowTitle(tr("license_title"))
        self.resize(600, 450)
        layout = QVBoxLayout(self)
        browser = QTextBrowser(self); browser.setPlainText(text); layout.addWidget(browser)
        buttons = QDialogButtonBox(QDialogButtonBox.Close, self); buttons.rejected.connect(self.reject); layout.addWidget(buttons)


class ExportPictureDialog(QDialog):
    CURRENT, RECALCULATE = range(2)

    def __init__(self, parent):
        super().__init__(parent)
        self.strategy = self.CURRENT
        self.setWindowTitle(tr("export_picture"))
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr("export_picture_dialog")))
        current = QPushButton(tr("export_picture_dialog_save_current_img"), self)
        recalculate = QPushButton(tr("export_picture_dialog_save_img_with_current_para"), self)
        current.clicked.connect(lambda: self.choose(self.CURRENT))
        recalculate.clicked.connect(lambda: self.choose(self.RECALCULATE))
        layout.addWidget(current); layout.addWidget(recalculate)

    def choose(self, strategy):
        self.strategy = strategy
        self.accept()


class ProcessMultiplePicturesDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(tr("batch_dialog_title"))
        self.resize(650, 220)
        self.input_paths, self.input_folder, self.output_folder, self.parameter_path = [], "", "", None
        layout = QVBoxLayout(self)
        self.input_display = QLineEdit(self); self.input_display.setReadOnly(True)
        self.output_display = QLineEdit(self); self.output_display.setReadOnly(True)
        self.parameter_display = QLineEdit(tr("current_parameter"), self); self.parameter_display.setReadOnly(True)
        layout.addLayout(self._row(tr("process_multiple_pictures_dialog1"), [(tr("process_multiple_pictures_dialog1_mode1"), self.choose_files), (tr("process_multiple_pictures_dialog1_mode2"), self.choose_folder)], self.input_display))
        layout.addLayout(self._row(tr("process_multiple_pictures_dialog2"), [(tr("select_output_folder"), self.choose_output)], self.output_display))
        layout.addLayout(self._row(tr("process_multiple_pictures_dialog3"), [(tr("current_parameter"), self.use_current), (tr("select_parameter_file"), self.choose_parameter)], self.parameter_display))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); layout.addWidget(buttons)

    def _row(self, title, buttons, display):
        row = QHBoxLayout(); row.addWidget(QLabel(title))
        for text, callback in buttons:
            button = QPushButton(text, self); button.clicked.connect(callback); row.addWidget(button)
        row.addWidget(display); return row

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, tr("select_multi_files"), "", tr("image_file_filter"))
        if paths:
            self.input_paths, self.input_folder = paths, ""
            self.input_display.setText(", ".join(paths))

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, tr("select_input_folder"))
        if folder:
            self.input_folder, self.input_paths = folder, []
            self.input_display.setText(folder)

    def choose_output(self):
        folder = QFileDialog.getExistingDirectory(self, tr("select_output_folder"))
        if folder:
            self.output_folder = folder; self.output_display.setText(folder)

    def use_current(self):
        self.parameter_path = None; self.parameter_display.setText(tr("current_parameter"))

    def choose_parameter(self):
        path, _ = QFileDialog.getOpenFileName(self, tr("select_parameter_file"), "", tr("json_file_filter"))
        if path:
            self.parameter_path = path; self.parameter_display.setText(path)


class DotifierView(QMainWindow):
    parametersChanged = Signal()
    calculateRequested = Signal()
    importImageRequested = Signal()
    exportImageRequested = Signal()
    importParametersRequested = Signal()
    exportParametersRequested = Signal()
    batchRequested = Signal()
    aboutRequested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("Dotifier")); self.resize(1000, 650)
        self._building = False
        self._build_menu(); self._build_content()

    def _build_menu(self):
        file_menu = self.menuBar().addMenu(tr("File"))
        other_menu = self.menuBar().addMenu(tr("Others"))
        self.import_image_action = file_menu.addAction(tr("import_picture"))
        self.export_image_action = file_menu.addAction(tr("export_picture"))
        file_menu.addSeparator()
        self.import_parameters_action = file_menu.addAction(tr("import_parameters"))
        self.export_parameters_action = file_menu.addAction(tr("export_parameters"))
        file_menu.addSeparator(); self.batch_action = file_menu.addAction(tr("process_multiple_pictures"))
        self.about_action = other_menu.addAction(tr("About"))
        self.import_image_action.triggered.connect(self.importImageRequested)
        self.export_image_action.triggered.connect(self.exportImageRequested)
        self.import_parameters_action.triggered.connect(self.importParametersRequested)
        self.export_parameters_action.triggered.connect(self.exportParametersRequested)
        self.batch_action.triggered.connect(self.batchRequested)
        self.about_action.triggered.connect(self.aboutRequested)

    def _build_content(self):
        splitter = QSplitter(Qt.Horizontal, self); self.setCentralWidget(splitter)
        left = QWidget(self); controls = QVBoxLayout(left)
        self.mode_toggle = TriStateToggle(parent=left); controls.addWidget(self.mode_toggle)
        self.scale = self._spin_row(controls, tr("scale"), 10, 500, 100, 10)
        self.level = self._spin_row(controls, tr("discrete_level"), 2, 255, 2)
        self.density = self._spin_row(controls, tr("points_density"), 2, 255, 2)
        self.staggered = QCheckBox(tr("staggered"), left); self.staggered.setChecked(True); controls.addWidget(self.staggered)
        self.inversion = QCheckBox(tr("inversion"), left); controls.addWidget(self.inversion)
        self.preset = QComboBox(left); self.preset.addItems([tr("Linear"), tr("Sigmoid_like"), tr("Reversed_Sigmoid_like"), tr("Log_like"), tr("Exp_like")]); controls.addWidget(self.preset)
        self.undo_button, self.redo_button = QPushButton(tr("undo"), left), QPushButton(tr("redo"), left)
        curve_container = QWidget();curve_container.setStyleSheet("background-color: #ffffff;")
        self.undo_button.setStyleSheet("padding: 4px 8px;border: 2px solid #aaaaaa;border-radius: 6px;")
        self.redo_button.setStyleSheet("padding: 4px 8px;border: 2px solid #aaaaaa;border-radius: 6px;")
        curve_Vlayout = QVBoxLayout(curve_container)
        history = QHBoxLayout(); history.addStretch(); history.addWidget(self.undo_button); history.addWidget(self.redo_button)
        curve_Vlayout.addLayout(history)
        self.curve_canvas = InteractiveCurveCanvas(curve_container); curve_Vlayout.addWidget(self.curve_canvas)
        controls.addWidget(curve_container)
        self.preview = QCheckBox(tr("preview"), left); self.calculate_button = QPushButton(tr("calculate"), left)
        calculation = QHBoxLayout(); calculation.addWidget(self.preview); calculation.addWidget(self.calculate_button); controls.addLayout(calculation)
        right = QWidget(self); right_layout = QVBoxLayout(right)
        self.figure = Figure(); self.image_canvas = FigureCanvas(self.figure); self.image_axes = self.figure.add_subplot(111)
        self.toolbar = CustomNavigationToolbar(self.image_canvas, right)
        self._image_drag_position = None
        self._image_dragged = False
        self._image_base_spans = None
        self._connect_image_navigation()
        right_layout.addWidget(self.image_canvas); right_layout.addWidget(self.toolbar)
        splitter.addWidget(left); splitter.addWidget(right); splitter.setSizes([350, 650])
        self.mode_toggle.stateChanged.connect(self._emit_parameters_changed)
        for widget, signal in ((self.scale, self.scale.valueChanged), (self.level, self.level.valueChanged), (self.density, self.density.valueChanged), (self.staggered, self.staggered.toggled), (self.inversion, self.inversion.toggled), (self.preview, self.preview.toggled)):
            signal.connect(self._emit_parameters_changed)
        self.preset.currentIndexChanged.connect(self.curve_canvas.apply_preset)
        self.curve_canvas.coordinatesChanged.connect(self._emit_parameters_changed)
        self.undo_button.clicked.connect(self.curve_canvas.undo); self.redo_button.clicked.connect(self.curve_canvas.redo)
        self.calculate_button.clicked.connect(self.calculateRequested)

    def _connect_image_navigation(self):
        """Add direct pan and cursor-centred zoom controls to the image canvas."""
        self.image_canvas.mpl_connect("button_press_event", self._start_image_drag)
        self.image_canvas.mpl_connect("motion_notify_event", self._drag_image)
        self.image_canvas.mpl_connect("button_release_event", self._end_image_drag)
        self.image_canvas.mpl_connect("scroll_event", self._zoom_image)

    def _image_navigation_available(self, event):
        toolbar_mode = self.toolbar.mode
        toolbar_is_idle = not toolbar_mode or getattr(toolbar_mode, "name", None) == "NONE"
        return (
            toolbar_is_idle
            and event.inaxes is self.image_axes
            and event.xdata is not None
            and event.ydata is not None
            and self.image_axes.images
        )

    def _start_image_drag(self, event):
        if event.button == 1 and self._image_navigation_available(event):
            self._image_drag_position = (event.xdata, event.ydata)
            self._image_dragged = False
            self.image_canvas.setCursor(Qt.ClosedHandCursor)

    def _drag_image(self, event):
        if self._image_drag_position is None:
            return
        if not self._image_navigation_available(event):
            return
        previous_x, previous_y = self._image_drag_position
        offset_x, offset_y = previous_x - event.xdata, previous_y - event.ydata
        x_start, x_end = self.image_axes.get_xlim()
        y_start, y_end = self.image_axes.get_ylim()
        self.image_axes.set_xlim(x_start + offset_x, x_end + offset_x)
        self.image_axes.set_ylim(y_start + offset_y, y_end + offset_y)
        self._image_drag_position = (event.xdata, event.ydata)
        self._image_dragged = self._image_dragged or offset_x != 0 or offset_y != 0
        self.image_canvas.draw_idle()

    def _end_image_drag(self, event):
        if self._image_drag_position is not None:
            self._image_drag_position = None
            self.image_canvas.unsetCursor()
            if self._image_dragged:
                self.toolbar.push_current()
            self._image_dragged = False

    def _zoom_image(self, event):
        if not self._image_navigation_available(event) or self._image_base_spans is None:
            return
        if event.button not in ("up", "down"):
            return
        zoom_factor = 1.2 if event.button == "up" else 1 / 1.2
        x_start, x_end = self.image_axes.get_xlim()
        y_start, y_end = self.image_axes.get_ylim()
        x_span, y_span = abs(x_end - x_start), abs(y_end - y_start)
        base_x_span, base_y_span = self._image_base_spans
        current_scale = max(base_x_span / x_span, base_y_span / y_span)
        target_scale = max(0.1, min(100.0, current_scale * zoom_factor))
        if target_scale == current_scale:
            return
        scale_change = current_scale / target_scale
        self.image_axes.set_xlim(
            event.xdata + (x_start - event.xdata) * scale_change,
            event.xdata + (x_end - event.xdata) * scale_change,
        )
        self.image_axes.set_ylim(
            event.ydata + (y_start - event.ydata) * scale_change,
            event.ydata + (y_end - event.ydata) * scale_change,
        )
        self.toolbar.push_current()
        self.image_canvas.draw_idle()

    def _spin_row(self, layout, text, minimum, maximum, value, step=1):
        row = QHBoxLayout(); row.addWidget(QLabel(text, self)); spin = QSpinBox(self)
        spin.setRange(minimum, maximum); spin.setValue(value); spin.setSingleStep(step); row.addWidget(spin); layout.addLayout(row); return spin

    def _emit_parameters_changed(self, *args):
        if not self._building:
            self.parametersChanged.emit()

    def read_parameters(self) -> dict[str, Any]:
        return {"version": 1.0, "mode": self.mode_toggle.current_state(), "scale": self.scale.value(), "discrete_level": self.level.value(), "pts_density": self.density.value(), "staggered": self.staggered.isChecked(), "inversion": self.inversion.isChecked(), "combo": self.preset.currentIndex(), "node_list": self.curve_canvas.node_list, "preview": self.preview.isChecked()}

    def present_parameters(self, parameters: dict[str, Any]):
        self._building = True
        try:
            self.scale.setValue(parameters["scale"]); self.level.setValue(parameters["discrete_level"]); self.density.setValue(parameters["pts_density"])
            self.staggered.setChecked(parameters["staggered"]); self.inversion.setChecked(parameters["inversion"])
            self.mode_toggle.set_state(parameters["mode"]); self.preset.setCurrentIndex(parameters["combo"])
            self.curve_canvas.set_nodes(parameters["node_list"], reset_history=True); self.preview.setChecked(parameters["preview"])
        finally:
            self._building = False

    def show_image(self, image):
        self.image_axes.clear()
        if image.ndim == 2: self.image_axes.imshow(image, cmap="gray", vmin=0, vmax=255)
        else: self.image_axes.imshow(image)
        self.image_axes.set_xlabel("X")
        self.image_axes.set_ylabel("Y")
        x_start, x_end = self.image_axes.get_xlim()
        y_start, y_end = self.image_axes.get_ylim()
        self._image_base_spans = (abs(x_end - x_start), abs(y_end - y_start))
        self.toolbar.update()
        self.toolbar.push_current()
        self.image_canvas.draw_idle()

    def choose_open_image(self):
        return QFileDialog.getOpenFileName(self, tr("select_image"), "", tr("image_file_filter"))[0]

    def choose_save_image(self):
        return QFileDialog.getSaveFileName(self, tr("select_output_image"), "", tr("save_image_file_filter"))[0]

    def choose_open_parameters(self):
        return QFileDialog.getOpenFileName(self, tr("select_parameters"), "", tr("json_file_filter"))[0]

    def choose_save_parameters(self):
        return QFileDialog.getSaveFileName(self, tr("save_parameters"), "", tr("json_file_filter"))[0]

    def show_error(self, message_key: str, **values: Any):
        QMessageBox.warning(self, tr("error_title"), tr(message_key, **values))

    def show_info(self, message_key: str, **values: Any):
        QMessageBox.information(self, tr("Dotifier"), tr(message_key, **values))

    @staticmethod
    def text(message_key: str, **values: Any) -> str:
        """Provide localized text to view-owned dialogs."""
        return tr(message_key, **values)
