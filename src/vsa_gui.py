"""
Copyright The Jackson Laboratory, 2023
authors: Jim Peterson

This application is for Void Spot Analysis (VSA).
The images are pictures of mouse cage paper liners that
have been stained by voiding.  The purpose of this program
is to do the following:
    1. Load image
    2. Segment paper/background and measure resize
    4. Identify and segment voiding spots
    5. Identify overlapped spots
    6. Measure areas/volumes
    7. Create per sample results
    8. Compile summary results

To Do:
    - Add tests for all functions
    - add comment block to each function
    - save masks and polys and annotated image, optionally
"""

import os
import sys
import configparser
import numpy as np
import cv2
import json
from datetime import datetime

from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QFileDialog,
    QLabel,
    QGroupBox,
    QCheckBox,
    QSlider,
    QSpinBox,
    QDoubleSpinBox,
    QLineEdit,
    QFrame,
    QLineEdit,
    QMessageBox,
    QMenuBar)
from vsa import VsaProcessor
from vsa_viewer import VsaViewer, VsaView
import polygon_tools as pt
from area_volume_map import AreaVolumeMap


class MainWin(QWidget):
    '''
    This class implents the main graphical user interface (GUI) for the application.
    '''
    def __init__(self):
        '''
        The UI elements are defined here and layed out.
        '''
        super().__init__()
        self.vsa_processor = VsaProcessor()
        self.version_string = "0.023"
        self.vol_cal_points = []  # list of (cm^2, uL) points
        self.volume_mapper = AreaVolumeMap()
        self.pathname = ""
        self.need_to_save = False

        # Main layout
        self.setGeometry(100,100,1200,600)
        self.setWindowTitle(f"Spotifind - version {self.version_string}")
        hbox_main = QHBoxLayout()
        self.setLayout(hbox_main)

        # File menu
        menubar = QMenuBar()
        hbox_main.addWidget(menubar)
        file_menu = menubar.addMenu("File")
        action_open_image = file_menu.addAction("Open image...")
        action_open_image.triggered.connect(self.action_open_image)
        file_menu.addSeparator()
        action_load_calibration = file_menu.addAction("Load calibration...")
        action_load_calibration.triggered.connect(self.load_calibration)
        action_save_calibration = file_menu.addAction("Save calibration...")
        action_save_calibration.triggered.connect(self.save_calibration)
        file_menu.addSeparator()
        action_save_summary = file_menu.addAction("Save summary results...")
        action_save_summary.triggered.connect(self.save_summary_results)
        action_save_sample_results = file_menu.addAction("Save sample results...")
        action_save_sample_results.triggered.connect(self.save_sample_results)
        file_menu.addSeparator()
        action_save_session = file_menu.addAction("Save Session...")
        action_save_session.triggered.connect(self.save_session)
        action_load_session = file_menu.addAction("Load Session...")
        action_load_session.triggered.connect(self.load_session)

        file_menu.addSeparator()
        action_save_all = file_menu.addAction("Save All...")
        action_save_all.triggered.connect(self.save_all)

        # Viewer
        self.viewer = VsaViewer()
        hbox_main.addWidget(self.viewer)

        # Sample, Paper Identification, Void spot Identification, and Calibration groupboxs
        layout_controls = QVBoxLayout()
        hbox_main.addLayout(layout_controls)
        layout_controls.addWidget(self.create_sample_groupbox())
        layout_controls.addWidget(self.create_paper_groupbox())
        layout_controls.addWidget(self.create_void_spots_groupbox())
        layout_controls.addWidget(self.create_calibration_groupbox())
        layout_controls.insertStretch(-1)

        # Set main layout stretch rule
        hbox_main.setStretch(0, 255)
        hbox_main.setStretch(1, 1)


    def closeEvent(self, event):
        '''
        This function catches the application close event.
        This gives us a chance to prompt the user for saving the session.
        '''
        if (self.vsa_processor.img is None) or (not self.need_to_save):
            return
        msg = "The results and/or session have not been saved.\n"
        msg += "Do you want to save the session?"
        ans = self.message_box_yes_no(msg, "")
        if ans == QMessageBox.StandardButton.Yes:
            self.save_session()
        return


    def resizeEvent(self, event):
        '''
        This function is called when the main window is resized.
        The controls are resized automatically.  If there is an image
        open and it will not fill the new window size, then it will be
        rescaled to fit.
        '''
        if self.vsa_processor.img is None:
            return
        self.viewer.set_min_scale()
        img_height, img_width = self.vsa_processor.get_img_dim()
        view_width, view_height = self.viewer.get_view_size()
        w_scale = view_width/img_width
        h_scale = view_height/img_height
        scale = min(w_scale, h_scale)
        current_scale = self.viewer.get_scale()
        if scale > current_scale:
            self.viewer.set_scale(scale)


    def create_sample_groupbox(self):
        '''
        This function lays out the "Sample" groupbox in the main window.
        '''
        image_box = QGroupBox("Sample")
        layout_000 = QVBoxLayout()
        image_box.setLayout(layout_000)

        layout_001 = QHBoxLayout()
        layout_001.addWidget(QLabel("Sample ID:"))
        self.line_edit_sample_id = QLineEdit()
        layout_001.addWidget(self.line_edit_sample_id)
        layout_001.addWidget(QLabel("Mouse ID:"))
        self.line_edit_mouse_id = QLineEdit()
        layout_001.addWidget(self.line_edit_mouse_id)
        layout_000.addLayout(layout_001)

        layout_002 = QHBoxLayout()
        self.spinbox_micro_void_thresh = QDoubleSpinBox()
        self.spinbox_micro_void_thresh.setToolTip("void spots smaller than this μL threshold are deemed micro-voids")
        self.spinbox_micro_void_thresh.setRange(0.0, 100.0)
        self.spinbox_micro_void_thresh.setValue(22.0)
        self.spinbox_micro_void_thresh.valueChanged[float].connect(self.micro_void_thresh_changed)
        layout_002.addWidget(QLabel("micro-void threshold (μL):"))
        layout_002.addWidget(self.spinbox_micro_void_thresh)
        layout_000.addLayout(layout_002)

        self.spinbox_nano_void_thresh = QDoubleSpinBox()
        self.spinbox_nano_void_thresh.setToolTip("spots smaller than this threshold are are deemed micro-voids.")
        self.spinbox_nano_void_thresh.setRange(0.00, 25.0)
        self.spinbox_nano_void_thresh.setSingleStep(0.1)
        self.spinbox_nano_void_thresh.setValue(2.0)
        self.spinbox_nano_void_thresh.valueChanged[float].connect(self.nano_void_thresh_changed)
        layout_002.addWidget(QLabel("nano-void size (μL):"))
        layout_002.addWidget(self.spinbox_nano_void_thresh)
        layout_002.insertStretch(-1)

        self.spinbox_min_void_size = QDoubleSpinBox()
        self.spinbox_min_void_size.setToolTip("spots smaller than this threshold are not recorded.")
        self.spinbox_min_void_size.setRange(0.00, 5.0)
        self.spinbox_min_void_size.setSingleStep(0.01)
        self.spinbox_min_void_size.setValue(0.1)
        self.spinbox_min_void_size.valueChanged[float].connect(self.min_void_thresh_changed)
        layout_002.addWidget(QLabel("minimum void size (μL):"))
        layout_002.addWidget(self.spinbox_min_void_size)
        layout_002.insertStretch(-1)

        line0 = QFrame()
        line0.setFrameShape(QFrame.Shape.HLine)
        line0.setFrameShadow(QFrame.Shadow.Sunken)
        layout_000.addWidget(line0)

        self.label_spot_count = QLabel("count: 0\nvolume: 0.0 μl\naverage distance to edge: 0.0 cm")
        layout_000.addWidget(self.label_spot_count)
        return image_box


    def create_paper_groupbox(self):
        '''
        This function lays out the "Paper Identification" groupbox in the main window
        '''
        paper_box = QGroupBox("Paper Identification")
        layout_000 = QVBoxLayout()
        paper_box.setLayout(layout_000)
        layout_001 = QHBoxLayout()
        layout_000.addLayout(layout_001)
        layout_001.addWidget(QLabel("threshold adjustment:"))
        self.spinbox_paper_threshold = QSpinBox()
        self.spinbox_paper_threshold.setRange(0, 255)
        self.spinbox_paper_threshold.valueChanged[int].connect(self.paper_threshold_change)
        self.spinbox_paper_threshold.setToolTip("fixed threshold for identification of paper")
        layout_001.addWidget(self.spinbox_paper_threshold)
        button_reset_paper_threshold = QPushButton("reset")
        button_reset_paper_threshold.clicked.connect(self.reset_paper_threshold)
        button_reset_paper_threshold.setToolTip("reset default threshold based on current image")
        layout_001.addWidget(button_reset_paper_threshold)
        layout_001.insertStretch(-1)
        return paper_box


    def create_void_spots_groupbox(self):
        '''
        This function lays out the "Void Spot Identification" groupbox in the main window.
        '''
        spot_box = QGroupBox("Void Spot Identification")
        layout_000 = QVBoxLayout()
        spot_box.setLayout(layout_000)
        #Identify all spots
        button_identify_voids = QPushButton("identify")
        button_identify_voids.clicked.connect(self.identify_voids)
        layout_001 = QHBoxLayout()
        layout_000.addLayout(layout_001)
        # Add button
        button_add_spot = QPushButton("add")
        button_add_spot.clicked.connect(self.add_void_spots_to_list)
        layout_001.addWidget(button_identify_voids)
        layout_001.addWidget(button_add_spot)
        # Delete button
        button_delete = QPushButton("clear")
        button_delete.clicked.connect(self.clear_selection)
        layout_001.addWidget(button_delete)
        # Fill button
        button_fill = QPushButton("fill")
        button_fill.clicked.connect(self.fill_selection)
        layout_001.addWidget(button_fill)
        layout_001.insertStretch(-1)
        '''
        # Reset button
        button_reset_params = QPushButton("reset parameters")
        button_reset_params.clicked.connect(self.reset_params)
        layout_001.addWidget(button_reset_params)
        layout_001.insertStretch(-1)
        '''
        # Sensitivity control
        layout_002 = QHBoxLayout()
        self.spinbox_spot_threshold_adj = QSpinBox()
        self.spinbox_spot_threshold_adj.setRange(-99, 99)
        self.spinbox_spot_threshold_adj.setValue(0)
        self.spinbox_spot_threshold_adj.valueChanged[int].connect(self.spot_thresh_adj_change)
        layout_002.addWidget(QLabel("threshold adjustment:"))
        layout_002.addWidget(self.spinbox_spot_threshold_adj)
        layout_002.insertStretch(-1)
        layout_000.addLayout(layout_002)
        self.spinbox_min_range = QSpinBox()
        self.spinbox_min_range.setRange(1, 255)
        self.spinbox_min_range.setValue(25)
        self.spinbox_min_range.valueChanged[int].connect(self.spot_range_change)
        layout_003 = QHBoxLayout()
        layout_003.addWidget(QLabel("minimum range:"))
        layout_003.addWidget(self.spinbox_min_range)
        layout_003.insertStretch(-1)
        layout_000.addLayout(layout_003)
        self.spinbox_min_dist_from_median = QSpinBox()
        self.spinbox_min_dist_from_median.setRange(0, 200)
        self.spinbox_min_dist_from_median.setValue(10)
        self.spinbox_min_dist_from_median.valueChanged[int].connect(self.spot_range_change)
        layout_005 = QHBoxLayout()
        layout_005.addWidget(QLabel("threshold-median difference:"))
        layout_005.addWidget(self.spinbox_min_dist_from_median)
        layout_005.insertStretch(-1)
        layout_000.addLayout(layout_005)

        layout_006 = QHBoxLayout()
        button_reset_params = QPushButton("reset parameters")
        button_reset_params.clicked.connect(self.reset_params)
        layout_006.addWidget(button_reset_params)
        layout_006.insertStretch(-1)
        layout_000.addLayout(layout_006)

        return spot_box

    def create_calibration_groupbox(self):
        '''
        This function lays out the Calibration groupbox.
        '''
        calibration_box = QGroupBox("Calibration")
        layout_000 = QVBoxLayout()
        calibration_box.setLayout(layout_000)

        layout_001 = QHBoxLayout()

        layout_001.addWidget(QLabel("object size (cm):"))
        self.spinbox_known_length = QDoubleSpinBox()
        self.spinbox_known_length.setToolTip("length (in centimeters) of the selection box in the image")
        self.spinbox_known_length.setRange(0.25, 25.0)
        self.spinbox_known_length.setValue(5.0)
        layout_001.addWidget(self.spinbox_known_length)
        button_pixcal = QPushButton("compute")
        button_pixcal.setToolTip("Compute pixel size based on the selection in the image of an object of known length.")
        button_pixcal.clicked.connect(self.calibrate_pixel_size)
        layout_001.addWidget(button_pixcal)
        self.spinbox_resolution = QDoubleSpinBox()
        self.spinbox_resolution.setToolTip("resolution of the input image, measured in pixels per centimeter")
        self.spinbox_resolution.setRange(0.1, 1000.0)
        self.spinbox_resolution.setValue(1.0)
        self.spinbox_resolution.setToolTip("Pixel size can be entered here if known, or computed from an object of know size in an image")
        self.spinbox_resolution.valueChanged[float].connect(self.resolution_changed)
        layout_001.addWidget(QLabel("pixels/cm:"))
        layout_001.addWidget(self.spinbox_resolution)
        layout_001.insertStretch(-1)
        layout_000.addLayout(layout_001)

        line0 = QFrame()
        line0.setFrameShape(QFrame.Shape.HLine)
        line0.setFrameShadow(QFrame.Shadow.Sunken)
        layout_000.addWidget(line0)

        layout_002 = QHBoxLayout()
        layout_002.addWidget(QLabel("vol (μL):"))
        self.spinbox_known_volume = QDoubleSpinBox()
        self.spinbox_known_volume.setToolTip("volume (in μL) of an identified object in the image")
        self.spinbox_known_volume.setRange(0.001, 1000.0)
        self.spinbox_known_volume.setValue(50.0)
        layout_002.addWidget(self.spinbox_known_volume)

        model_str = "V=(0.0)*A^2 + (0.0)*A"
        self.label_model = QLabel(model_str)
        self.label_model.setToolTip("area to volume mapping based on current data points")
        layout_002.addWidget(self.label_model)

        layout_002.insertStretch(-1)
        layout_000.addLayout(layout_002)

        layout_003 = QHBoxLayout()
        button_volcal = QPushButton("add")
        tip_str = "Adds the (area, volume) data point for modeling,\n"
        tip_str += "based on the identified object and the specified known volume."
        button_volcal.setToolTip(tip_str)
        button_volcal.clicked.connect(self.calibrate_volume_per_pixel)
        layout_003.addWidget(button_volcal)

        button_volcal_del = QPushButton("del")
        button_volcal_del.setToolTip("Delete the last data point added.")
        button_volcal_del.clicked.connect(self.calibrate_volume_per_pixel_del)
        layout_003.addWidget(button_volcal_del)

        self.lineEdit_cal_points = QLineEdit()
        self.lineEdit_cal_points.setReadOnly(True)
        layout_003.addWidget(self.lineEdit_cal_points)
        layout_000.addLayout(layout_003)

        return calibration_box


    def reset_params(self):
        self.spinbox_spot_threshold_adj.setValue(0)
        self.spinbox_min_range.setValue(25)
        self.spinbox_min_dist_from_median.setValue(10)

    def action_open_image(self):
        '''
        Called when the "File/Open image..." menu item is selected.
        '''
        pathname_tupple = QFileDialog.getOpenFileName(self, 'Open file', '.',"image files (*.tif *.jpg)")
        if not pathname_tupple:
            return
        self.pathname = pathname_tupple[0]
        if not self.pathname:
            return
        if self.open_image():
            self.line_edit_mouse_id.setText("mouse_0000")



    def open_image(self):
        '''
        This function is called when a new image is loaded, whether this via the "File/Open Image..." menu, or via opening
        a session file.
        '''
        if not self.vsa_processor.open_image(self.pathname):
            return False
        fname = os.path.basename(self.pathname)
        base = os.path.splitext(fname)[0]
        self.line_edit_sample_id.setText(base)
        self.line_edit_mouse_id.setText("mouse_0000")

        paper_threshold = self.vsa_processor.get_default_paper_threshold()
        self.spinbox_paper_threshold.setValue(paper_threshold)
        img_height, img_width = self.vsa_processor.get_img_dim()
        self.viewer.set_image(self.vsa_processor.get_img())
        self.viewer.set_title(f"{self.pathname}  ({img_width} x {img_height})")
        view_width, view_height = self.viewer.get_view_size()
        w_scale = view_width/img_width
        h_scale = view_height/img_height
        scale = min(w_scale, h_scale)
        self.viewer.set_scale(scale)
        self.generate_paper_mask()
        return True


    def micro_void_thresh_changed(self):
        self.update_measurements()

    def nano_void_thresh_changed(self):
        self.update_measurements()

    def min_void_thresh_changed(self):
        self.update_measurements()

    def calibrate_pixel_size(self):
        '''
        This is called when the user initiates the pixel/cm calibration.
        '''
        selection = self.viewer.get_selection_rect()
        pix_length = max(selection[2], selection[3])
        if pix_length <= 0:
            msg = "To calculate pixel calibration:\n"
            msg += "    1. Open an image containing an object of known length (e.g. a ruler)\n"
            msg += "    2. Enter the known length in centimeters in the spin box.\n"
            msg += "    3. Identify the object with the selection tool.\n"
            msg += "    4. Press the 'Calculate' button.\n"
            msg += "The resulting value will be entered in the 'pixels/cm' spin box."
            self.message_box(msg)
            return False
        cm_length = self.spinbox_known_length.value()
        pix_per_cm = pix_length / cm_length
        self.spinbox_resolution.setValue(pix_per_cm)
        return True


    def calibrate_volume_per_pixel(self):
        '''
        This is called when the user adds a data point to the list of (area, volume) points used
        the calibrate the area->volume mapping.  After each point is added the model for the
        mapping is recomputed.
        '''
        if len(self.vsa_processor.spot_polygons) <= 0:
            print("No objects identified")
            return False
        size_thresh_list = [self.spinbox_min_void_size.value(), self.spinbox_nano_void_thresh.value(), self.spinbox_micro_void_thresh.value()]
        object_size_in_pix2 = self.vsa_processor.measure_spots(self.volume_mapper, self.spinbox_resolution.value(), size_thresh_list)
        object_volume_in_uL = self.spinbox_known_volume.value()
        pix_per_cm = self.spinbox_resolution.value()
        object_size_in_cm2 = object_size_in_pix2 / (pix_per_cm*pix_per_cm)

        point = (object_size_in_cm2, object_volume_in_uL)
        self.vol_cal_points.append(point)
        self.volume_mapper.compute_model(self.vol_cal_points)
        model_str = f"V=({self.volume_mapper.c2:.3f})*A^2 + ({self.volume_mapper.c1:.3f})*A"
        self.label_model.setText(model_str)

        str_all_pts = ""
        for pt in self.vol_cal_points:
            str_pt = f"({pt[0]:.2f}, {pt[1]})"
            str_all_pts += str_pt
        self.lineEdit_cal_points.setText(str_all_pts)
        self.update_measurements()

        # Dump test data
        '''
        test_str = ""
        test_str += f"C1, {self.volume_mapper.c1:.4f}\n"
        test_str += f"C2, {self.volume_mapper.c2:.4f}\n\n\n"
        test_str += "Area, Volume\n"
        for pt in self.vol_cal_points:
            test_str += f"{pt[0]:.3f}, {pt[1]:.3f}\n"
        test_str += "\n\n"
        a = 0.0
        test_str += "Area, Volume\n"
        while a < 50.0:
            v = self.volume_mapper.map_area(a)
            test_str += f"{a:.3f}, {v:.3f}\n"
            a += 0.5
        f = open("test_map.csv", mode="w")
        f.write(test_str)
        f.close()
        '''
        return True


    def calibrate_volume_per_pixel_del(self):
        '''
        This function is called when the user initiates removing the last point added.
        '''
        if len(self.vol_cal_points) <= 0:
            return
        self.vol_cal_points = self.vol_cal_points[0:-1]
        self.volume_mapper.compute_model(self.vol_cal_points)
        model_str = f"V=({self.volume_mapper.c2:.3f})*A^2 + ({self.volume_mapper.c1:.3f})*A"
        self.label_model.setText(model_str)
        self.update_measurements()

        str_all_pts = ""
        for pt in self.vol_cal_points:
            str_pt = f"({pt[0]:.2f}, {pt[1]})"
            str_all_pts += str_pt
        self.lineEdit_cal_points.setText(str_all_pts)
        self.update_measurements()


    def save_calibration(self):
        '''
        Prompts for a file to write to, and saves the calibration data to the file in JSON format.
        '''
        file_tup = QFileDialog.getSaveFileName()
        filename = file_tup[0]
        if not filename:
            return False
        json_dict = {}
        pixels_per_cm = self.spinbox_resolution.value()
        json_dict['pixels_per_cm'] = pixels_per_cm
        json_dict['volume_calibration_data'] = self.vol_cal_points

        json_str = json.dumps(json_dict, indent=4)
        with open(filename, "w") as file:
            file.write(json_str)
        return True


    def load_calibration(self):
        '''
        Prompts for a file, and reads the calibration data.  The data is assumed to be in JSON format.
        '''
        file_tup = QFileDialog.getOpenFileName()
        filename = file_tup[0]
        if not filename:
            return False
        json_str = ""
        with open(filename, "r") as file:
            json_str = file.read()
        json_dict = json.loads(json_str)
        if 'pixels_per_cm' in json_dict:
            pixels_per_cm = json_dict['pixels_per_cm']
            self.spinbox_resolution.setValue(pixels_per_cm)
        if 'volume_calibration_data' in json_dict:
            self.vol_cal_points = json_dict['volume_calibration_data']
            self.volume_mapper.compute_model(self.vol_cal_points)
            model_str = f"V=({self.volume_mapper.c2:.3f})*A^2 + ({self.volume_mapper.c1:.3f})*A"
            self.label_model.setText(model_str)
            str_all_pts = ""
            for pt in self.vol_cal_points:
                str_pt = f"({pt[0]:.2f}, {pt[1]})"
                str_all_pts += str_pt
            self.lineEdit_cal_points.setText(str_all_pts)
            self.update_measurements()
        return True

    def volume_calibration_changed(self, value):
        self.update_measurements()
        return

    def add_void_spots_to_list(self):
        self.vsa_processor.save_roi_spots()
        self.update_measurements()
        self.viewer.set_spot_annotation(self.vsa_processor.spot_polygon_properties)
        return

    '''
    def get_selection(self):
        poly = self.viewer.get_selection_poly()
        if len(poly) == 0:
            selection = self.viewer.get_selection_rect()
            if (selection[2] > 0) and (selection[3] > 0):
                x = selection[0]
                y = selection[1]
                w = selection[2]
                h = selection[3]
                poly.append([x, y])
                poly.append([x+w, y])
                poly.append([x+w, y+h])
                poly.append([x, y+h])
        return poly
    '''



    def clear_selection(self):
        poly = self.viewer.get_selection()
        if len(poly) < 3:
            return
        self.vsa_processor.clear_poly_selection(poly)
        self.update_measurements()
        self.viewer.set_spot_annotation(self.vsa_processor.spot_polygon_properties)
        self.viewer.clear_selection_annotation()
        return

    def fill_selection(self):
        poly = self.viewer.get_selection()
        if len(poly) < 3:
            return
        self.vsa_processor.fill_poly_selection(poly)
        self.update_measurements()
        self.viewer.set_spot_annotation(self.vsa_processor.spot_polygon_properties)
        self.viewer.clear_selection_annotation()
        return

    def resolution_changed(self, value):
        """ Called when the user changes the resolution value. """
        self.update_measurements()

    def generate_paper_mask(self):
        paper_threshold = self.spinbox_paper_threshold.value()
        if not self.vsa_processor.segment_paper(paper_threshold):
            return False
        self.update_measurements()
        self.viewer.set_paper_annotation([self.vsa_processor.paper_polygon])

    def paper_threshold_change(self):
        if self.spinbox_paper_threshold.value() < 0:
            self.spinbox_paper_threshold.setValue(0)
        if self.vsa_processor.paper_mask is not None:
            self.generate_paper_mask()

    def reset_paper_threshold(self):
        paper_threshold = self.vsa_processor.get_default_paper_threshold()
        self.spinbox_paper_threshold.setValue(paper_threshold)
        return

    def spot_thresh_adj_change(self):
        selection = self.viewer.get_selection_rect()
        if (selection[2] > 0) and (selection[3] > 0):
            self.identify_voids()
        return

    def spot_range_change(self):
        selection = self.viewer.get_selection_rect()
        if (selection[2] > 0) and (selection[3] > 0):
            self.identify_voids()
        return

    def identify_voids(self):
        threshold_adjustment = self.spinbox_spot_threshold_adj.value()
        min_range = self.spinbox_min_range.value()
        #win_size = self.spinbox_win_size.value()
        min_dist_from_median = self.spinbox_min_dist_from_median.value()
        selection = self.viewer.get_selection_rect()
        if selection[0] < 0:
            selection[2] += selection[0]
            selection[0] = 0
        if selection[1] < 0:
            selection[3] += selection[1]
            selection[1] = 0
        if ((selection[0] < 0) or (selection[1] < 0) or (selection[2] <=0) or (selection[3] <= 0)):
            self.vsa_processor.segment_spots(threshold_adjustment, min_range, min_dist_from_median)
            self.update_measurements()
            self.viewer.set_spot_annotation(self.vsa_processor.spot_polygon_properties)
        else:
            self.vsa_processor.segment_spots_in_roi(selection, threshold_adjustment, min_range, min_dist_from_median)
            self.viewer.set_candidate_annotation(self.vsa_processor.roi_polygons)


    def update_measurements(self):
        '''
        Updates display of measurements.  This is called when the image changes,
        or any of the user input that would affect measurements.
        '''
        size_thresh_list = [self.spinbox_min_void_size.value(), self.spinbox_nano_void_thresh.value(), self.spinbox_micro_void_thresh.value()]
        area_pix = self.vsa_processor.measure_spots(self.volume_mapper, self.spinbox_resolution.value(), size_thresh_list)


        # JGP - finish this...
        props_primary = [p for p in self.vsa_processor.spot_polygon_properties if p['class']=='primary']
        props_micro = [p for p in self.vsa_processor.spot_polygon_properties if p['class']=='micro']
        props_nano = [p for p in self.vsa_processor.spot_polygon_properties if p['class']=='nano']
        count = len(self.vsa_processor.spot_polygons)
        count_str = f"{count} ({len(props_primary)}, {len(props_micro)}, {len(props_nano)})"

        vol_primary = 0.0
        vol_micro = 0.0
        vol_nano = 0.0
        area_cm2 = 0.0
        weighted_distance = 0.0
        for poly in self.vsa_processor.spot_polygon_properties:
            if poly['class'] == 'junk':
                continue
            elif poly['class'] == 'nano':
                vol_nano += poly['volume_ul']
            elif poly['class'] == 'micro':
                vol_micro += poly['volume_ul']
            else:
                vol_primary += poly['volume_ul']

            
            area_cm2 += poly['area_cm2']
            weighted_distance += (poly['area_cm2'] * poly['ave_dist_to_edge_cm'])
        vol_total = vol_primary + vol_micro + vol_nano
        vol_str = f"{vol_total:.3f} ({vol_primary:.3f}, {vol_micro:.3f}, {vol_nano:.3f})"
        if area_cm2 > 0.001:
            ave_dist = weighted_distance / area_cm2
        else:
            ave_dist = 0.0
			
        self.label_spot_count.setText(f"count: {count_str}\nvolume: {vol_str} μl\ndistance from edge: {ave_dist:.1f} cm")
        self.viewer.set_spot_annotation(self.vsa_processor.spot_polygon_properties)
        self.need_to_save = True


    def message_box(self, msg: str):
        '''
        Display a simple message box with the specified message.
        '''
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.setWindowTitle("VSA message")
        msg_box.setText(msg)
        msg_box.exec()

    def message_box_yes_no(self, question_msg: str, information_msg: str):
        '''
        Display a simple yes/no/cancel message box.  The question_msg string poses the question to
        the user.  The information_msg explains the consequences of each answer.
        '''
        msg_box = QMessageBox()
        msg_box.setText(question_msg)
        msg_box.setInformativeText(information_msg)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setWindowTitle("VSA message")
        return msg_box.exec()

    def message_box_yes_no_cancel(self, question_msg: str, information_msg: str):
        '''
        Display a simple yes/no/cancel message box.  The question_msg string poses the question to
        the user.  The information_msg explains the consequences of each answer.
        '''
        msg_box = QMessageBox()
        msg_box.setText(question_msg)
        msg_box.setInformativeText(information_msg)
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setWindowTitle("VSA message")
        return msg_box.exec()


    def save_sample_results(self, filename=False):
        '''
        '''
        if not filename:
            file_tup = QFileDialog.getSaveFileName(options=QFileDialog.Option.DontConfirmOverwrite)
            filename = file_tup[0]
            if not filename:
                return False
        sample_id = self.line_edit_sample_id.text()
        mouse_id = self.line_edit_mouse_id.text()
        heading_list = ['void_class','img_x', 'img_y', 'img_w', 'img_h',
                        'perimeter_cm', 'area_cm2', 'volume_ul',
                        'circularity', 'distance_to_edge']

        csv_data = []
        csv_data.append(['sample_id', sample_id])
        csv_data.append(['mouse_id', mouse_id])
        csv_data.append(['date_time', datetime.now().strftime("%Y/%m/%d:%H:%M:%S")])
        csv_data.append(['file_name', self.pathname])
        csv_data.append([])
        csv_data.append(heading_list)

        for poly_props in self.vsa_processor.spot_polygon_properties:
            if poly_props['class'] == 'junk':
                continue
            vc = poly_props['class']
            x = poly_props['img_x']
            y = poly_props['img_y']
            w = poly_props['img_w']
            h = poly_props['img_h']
            perim_cm = poly_props['perimeter_cm']
            area_cm2 = poly_props['area_cm2']
            volume_ul = poly_props['volume_ul']
            circ = poly_props['circularity']
            dist_cm = poly_props['ave_dist_to_edge_cm']
            csv_data.append([vc, f'{x}', f'{y}', f'{w}', f'{h}', f'{perim_cm:.2f}', f'{area_cm2:.2f}', f'{volume_ul:.2f}', f'{circ:.4f}', f'{dist_cm:.2f}'])

        try:
            with open(filename, mode="w") as csv_file:
                for row in csv_data:
                    csv_file.write(", ".join(row)+"\n")
        except:
            self.message_box(f"The sample results file could not be written:\n    {filename}")
            return False
        self.need_to_save = False
        return True


    def save_summary_results(self, filename=False):
        '''
        The result for the current sample is saved in CSV format.  The result is combined with any
        other results when the selected file exists.
        '''
        if not filename:
            file_tup = QFileDialog.getSaveFileName(options=QFileDialog.Option.DontConfirmOverwrite)
            filename = file_tup[0]
            if not filename:
                return False
        csv_data = []
        try:
            with open(filename) as csv_file:
                for line in csv_file:
                    record = []
                    for token in line.split(','):
                        record.append(token.strip())
                    csv_data.append(record)
        except:
            csv_data = [['sample_id', 'mouse_id', 'date_time', 'paper_area',
                         'micro_void_thresh_ul', 'nano_void_thresh_ul', 'min_void_size_ul',
                         'primary_count', 'micro_count', 'nano_count', 'total_count',
                         'primary_volume_ul', 'micro_volume_ul', 'nano_volume_ul', 
                         'primary_ave_volume_ul', 'micro_ave_volume_ul', 'nano_ave_volume_ul', 
                         'primary_ave_circularity', 'micro_ave_circularity', 'nano_ave_circularity', 
                         'primary_ave_distance_to_edge', 'micro_ave_distance_to_edge', 'nano_ave_distance_to_edge', 
                         'total_volume_ul', 'ave_volume', 'ave_circularity', 'ave_distance_to_edge']]

        sample_id = self.line_edit_sample_id.text()
        mouse_id = self.line_edit_mouse_id.text()
        if sample_id in [record[0] for record in csv_data]:
            ret = self.message_box_yes_no_cancel("Sample_id already exists in results file.  Do you want to remove previous instances?",
                "Press 'yes' to remove previous instances, 'no' to retain and append new record, or 'cancel' to do nothing.")

            if (ret == QMessageBox.StandardButton.Cancel):
                return
            if (ret == QMessageBox.StandardButton.Yes):
                csv_data = [record for record in csv_data if (record[0]!=sample_id)]

        micro_void_thresh_ul = self.spinbox_micro_void_thresh.value()
        nano_void_thresh_ul = self.spinbox_nano_void_thresh.value()
        min_void_size_ul = self.spinbox_min_void_size.value()
        pix_per_cm = self.spinbox_resolution.value()
        primary_count = 0
        micro_count = 0
        nano_count = 0
        vol_primary = 0.0
        vol_micro = 0.0
        vol_nano = 0.0
        circ_primary = 0.0
        circ_micro = 0.0
        circ_nano = 0.0
        dist_primary = 0.0
        dist_micro = 0.0
        dist_nano = 0.0

        for poly_props in self.vsa_processor.spot_polygon_properties:
            area_cm2 = poly_props['area_cm2']
            volume_ul = poly_props['volume_ul']
            if poly_props['class'] == 'nano':
                nano_count += 1
                vol_nano += volume_ul
                circ_nano += poly_props['circularity']
                dist_nano += poly_props['ave_dist_to_edge_cm']
            elif poly_props['class'] == 'micro':
                micro_count += 1
                vol_micro += volume_ul
                circ_micro += poly_props['circularity']
                dist_micro += poly_props['ave_dist_to_edge_cm']
            elif poly_props['class'] == 'primary':
                primary_count += 1
                vol_primary += volume_ul
                circ_primary += poly_props['circularity']
                dist_primary += poly_props['ave_dist_to_edge_cm']
        ave_circularity = (circ_primary + circ_micro + circ_nano)/(primary_count + micro_count + nano_count)
        ave_dist = (dist_primary + dist_micro + dist_nano)/(primary_count + micro_count + nano_count)
        vol_total = vol_primary + vol_micro + vol_nano
        if primary_count==0:
            ave_primary_vol=np.nan
            ave_primary_circ=np.nan
            ave_primary_dist=np.nan
        else:
            ave_primary_vol=vol_primary/primary_count
            ave_primary_circ=circ_primary/primary_count
            ave_primary_dist=dist_primary/primary_count
        if micro_count==0:
            ave_micro_vol=np.nan
            ave_micro_circ=np.nan
            ave_micro_dist=np.nan
        else:
            ave_micro_vol=vol_micro/micro_count
            ave_micro_circ=circ_micro/micro_count
            ave_micro_dist=dist_micro/micro_count
        if nano_count==0:
            ave_nano_vol=np.nan
            ave_nano_circ=np.nan
            ave_nano_dist=np.nan
        else:
            ave_nano_vol=vol_nano/nano_count
            ave_nano_circ=circ_nano/nano_count
            ave_nano_dist=dist_nano/nano_count

        record = []
        record.append(sample_id)                                        # sample_id
        record.append(mouse_id)                                         # mouse_id
        record.append(datetime.now().strftime("%Y/%m/%d:%H:%M:%S"))     # date_time
        record.append(f"{pt.polygon_area(self.vsa_processor.paper_polygon):1f}")
        record.append(f"{micro_void_thresh_ul:.1f}")                    # micro_void_thresh_ul
        record.append(f"{nano_void_thresh_ul:.1f}") 
        record.append(f"{min_void_size_ul:.1f}") 

        record.append(str(primary_count))                               # primary_count
        record.append(str(micro_count))   
        record.append(str(nano_count))                                 # micro_count
        record.append(str(primary_count+micro_count))                   # total_count

        record.append(f"{vol_primary:.1f}")                             # primary_volume_ul
        record.append(f"{vol_micro:.1f}")                               # micro_volume_ul
        record.append(f"{vol_nano:.1f}") 

        record.append(f"{ave_primary_vol:.3f}")               # primary_ave_volume_ul
        record.append(f"{ave_micro_vol:.3f}")                   # micro_ave_volume_ul
        record.append(f"{ave_nano_vol:.3f}")

        record.append(f"{ave_primary_circ:.3f}")              # primary_ave_circularity_ul
        record.append(f"{ave_micro_circ:.3f}")                  # micro_ave_circularity_ul
        record.append(f"{ave_nano_circ:.3f}")

        record.append(f"{ave_primary_dist:.3f}")              # primary_ave_distance_to_edge_ul
        record.append(f"{ave_micro_dist:.3f}")                  # micro_ave_distance_to_edge_ul
        record.append(f"{ave_nano_dist:.3f}")

        record.append(f"{vol_total:.1f}")                               # total_volume_ul
        record.append(f"{vol_total/(primary_count+micro_count+nano_count):.3f}")   # total_ave_volume_ul
        record.append(f"{ave_circularity:.3f}")                         # ave_circularity
        record.append(f"{ave_dist:.1f}")                                # ave_distance_to_edge

        csv_data.append(record)

        try:
            with open(filename, mode="w") as csv_file:
                for row in csv_data:
                    csv_file.write(", ".join(row)+"\n")
        except:
            self.message_box(f"The results file could not be written:\n    {filename}")
            return False

        self.need_to_save = False
        return True


    def save_session(self, filename=False):

        if not filename:
            file_tup = QFileDialog.getSaveFileName()
            filename = file_tup[0]
            if not filename:
                return False

        json_dict = {}
        json_dict['version'] = self.version_string
        json_dict['image_pathname'] = self.pathname
        json_dict['sample_id'] = self.line_edit_sample_id.text()
        json_dict['mouse_id'] = self.line_edit_mouse_id.text()
        json_dict['micro_void_threshold'] = self.spinbox_micro_void_thresh.value()
        json_dict['nano_void_threshold'] = self.spinbox_nano_void_thresh.value()
        json_dict['min_void_size'] = self.spinbox_min_void_size.value()
        json_dict['paper_threshold'] = self.spinbox_paper_threshold.value()
        json_dict['spot_seg_thresh_adj'] = self.spinbox_spot_threshold_adj.value()
        json_dict['spot_seg_min_range'] = self.spinbox_min_range.value()
        json_dict['spot_seg_median_deviation'] = self.spinbox_min_dist_from_median.value()
        json_dict['cal_known_length'] = self.spinbox_known_length.value()
        json_dict['cal_pix_per_cm'] = self.spinbox_resolution.value()
        json_dict['cal_known_vol'] = self.spinbox_known_volume.value()
        json_dict['volume_calibration_data'] = self.vol_cal_points
        json_dict['spot_polygons'] = self.vsa_processor.spot_polygons

        json_str = json.dumps(json_dict, indent=4)
        with open(filename, "w") as file:
            file.write(json_str)

        self.need_to_save = False
        return True


    def load_session(self):
        file_tup = QFileDialog.getOpenFileName()
        filename = file_tup[0]
        if not filename:
            return False
        json_str = ""
        with open(filename, "r") as file:
            json_str = file.read()
        json_dict = json.loads(json_str)
        if 'image_pathname' in json_dict:
            self.pathname = json_dict['image_pathname']
            if (not os.path.isfile(self.pathname)):
                self.pathname = ""
                self.message_box("specified image file does not exist: " + self.pathname)
            else:
                if not self.open_image():
                    self.message_box("specified image file could not be opened: " + self.pathname)

        if 'sample_id' in json_dict:
            self.line_edit_sample_id.setText(json_dict['sample_id'])
        if 'mouse_id' in json_dict:
            self.line_edit_mouse_id.setText(json_dict['mouse_id'])
        if 'micro_void_threshold' in json_dict:
            self.spinbox_micro_void_thresh.setValue(json_dict['micro_void_threshold'])
        if 'nano_void_threshold' in json_dict:
            self.spinbox_nano_void_thresh.setValue(json_dict['nano_void_threshold'])
        if 'min_void_size' in json_dict:
            self.spinbox_min_void_size.setValue(json_dict['min_void_size'])
        if 'paper_threshold' in json_dict:
            self.spinbox_paper_threshold.setValue(json_dict['paper_threshold'])
        if 'spot_seg_thresh_adj' in json_dict:
            self.spinbox_spot_threshold_adj.setValue(json_dict['spot_seg_thresh_adj'])
        if 'spot_seg_min_range' in json_dict:
            self.spinbox_min_range.setValue(json_dict['spot_seg_min_range'])
        if 'spot_seg_median_deviation' in json_dict:
            self.spinbox_min_dist_from_median.setValue(json_dict['spot_seg_median_deviation'])
        if 'cal_obj_length' in json_dict:
            self.spinbox_known_length.setValue(json_dict['cal_obj_length'])
        if 'cal_pix_per_cm' in json_dict:
            self.spinbox_resolution.setValue(json_dict['cal_pix_per_cm'])
        if 'cal_known_vol' in json_dict:
            self.spinbox_known_volume.setValue(json_dict['cal_known_vol'])
        if 'volume_calibration_data' in json_dict:
            self.vol_cal_points = json_dict['volume_calibration_data']
            self.volume_mapper.compute_model(self.vol_cal_points)
            model_str = f"V=({self.volume_mapper.c2:.3f})*A^2 + ({self.volume_mapper.c1:.3f})*A"
            self.label_model.setText(model_str)
            str_all_pts = ""
            for pt in self.vol_cal_points:
                str_pt = f"({pt[0]:.2f}, {pt[1]})"
                str_all_pts += str_pt
            self.lineEdit_cal_points.setText(str_all_pts)
        if 'spot_polygons' in json_dict:
            self.vsa_processor.set_spot_polygons(json_dict['spot_polygons'])
            size_thresh_list = [self.spinbox_min_void_size.value(), self.spinbox_nano_void_thresh.value(), self.spinbox_resolution.value()]
            self.vsa_processor.measure_spots(self.volume_mapper, self.spinbox_resolution.value(), size_thresh_list)
            self.viewer.set_spot_annotation(self.vsa_processor.spot_polygon_properties)
        self.update_measurements()
        return True
    
    def save_all(self):
        """
        The purpose of this function is to combine the save session, save summary, and save sample
        functionalities in an effort to improve the user experience.  the file names should be
        automatically generated.
        """
        mouse_id = self.line_edit_mouse_id.text()
        sample_id = self.line_edit_sample_id.text()
        base_dir = os.path.dirname(self.pathname) if self.pathname else os.getcwd()
        # 1. save the session
        session_filename = f"{mouse_id}_session.json"
        self.save_session(filename=os.path.join(base_dir, session_filename))
        # 2. save the summary
        summary_filename = "summary.csv"
        self.save_summary_results(os.path.join(base_dir, summary_filename))
        # 3. save the sample

        sample_filename = f"{mouse_id}_{sample_id}_sample.csv"
        self.save_sample_results(os.path.join(base_dir, sample_filename))

        message = "Files saved to:\n"
        message += f"{base_dir}\n"
        # Show the message box
        self.message_box(message)


def main():
    """
    This is the main entry-point of the program.
    The QT application is created as is the main window,
    which is a custom class derived from QWidget
    """
    app = QApplication(sys.argv)

    win = MainWin()
    win.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
