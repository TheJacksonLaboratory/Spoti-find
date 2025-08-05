import numpy as np
import cv2

from PyQt6 import QtCore
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPixmap, QImage, QPen, QColor, QPolygonF
from PyQt6.QtWidgets import (QGraphicsRectItem, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem,
    QGroupBox, QVBoxLayout, QHBoxLayout, QCheckBox, QDoubleSpinBox, QLabel, QSlider, QRadioButton)
from . import polygon_tools as pt

class VsaViewer(QGroupBox):

    def __init__(self):
        super().__init__()
        self.selection = [-1, -1, 0, 0]
        layout_000 = QVBoxLayout()
        self.setLayout(layout_000)
        self.view = VsaView()
        layout_000.addWidget(self.view)

        layout_001 = QHBoxLayout()
        layout_001.addWidget(QLabel("annotation:"))
        self.checkbox_paper = QCheckBox("paper")
        self.checkbox_paper.setToolTip("when checked, an outline of the paper is displayed")
        self.checkbox_paper.stateChanged.connect(self.checkbox_state_change_paper)
        self.checkbox_paper.setChecked(True)
        layout_001.addWidget(self.checkbox_paper)
        self.checkbox_spots = QCheckBox("spot")
        self.checkbox_spots.stateChanged.connect(self.checkbox_state_change_spots)
        self.checkbox_spots.setChecked(True)
        layout_001.addWidget(self.checkbox_spots)
        self.radio_selection_mode_rect = QRadioButton("rectange")
        self.radio_selection_mode_poly = QRadioButton("polygon")

        self.radio_selection_mode_rect.toggled.connect(self.selction_mode_change)
        self.radio_selection_mode_rect.setChecked(True)

        layout_001.insertStretch(-1)
        layout_001.addWidget(QLabel("selection:"))
        layout_001.addWidget(self.radio_selection_mode_rect)
        layout_001.addWidget(self.radio_selection_mode_poly)
        layout_000.addLayout(layout_001)

        layout_002 = QHBoxLayout()
        self.spinbox_brightness = QDoubleSpinBox()
        self.spinbox_brightness.setToolTip("when greater than zero, the image display intensity is brightened")
        self.spinbox_brightness.valueChanged[float].connect(self.eq_change)
        self.spinbox_brightness.setRange(0.0, 1.0)
        self.spinbox_brightness.setValue(0.0)
        self.spinbox_brightness.setSingleStep(0.01)
        layout_002.addWidget(QLabel("brightness:"))
        layout_002.addWidget(self.spinbox_brightness)

        self.spinbox_line_width = QDoubleSpinBox()
        self.spinbox_line_width.setToolTip("Increase line thickness")
        self.spinbox_line_width.valueChanged[float].connect(self.eq_change_line_width)
        self.spinbox_line_width.setRange(1.0, 10.0)
        self.spinbox_line_width.setValue(0.0)
        self.spinbox_line_width.setSingleStep(0.5)
        layout_002.addWidget(QLabel("line width:"))
        layout_002.addWidget(self.spinbox_line_width)

        self.slider_scale = QSlider(Qt.Orientation.Horizontal)
        self.slider_scale.setMinimum(0)
        self.slider_scale.setMaximum(1000)
        self.slider_scale.valueChanged[int].connect(self.scale_slider_change)
        self.spinbox_scale = QDoubleSpinBox()
        self.spinbox_scale.setToolTip("sets the magnification of the image")
        self.spinbox_scale.valueChanged[float].connect(self.scale_spinbox_change)
        self.spinbox_scale.setRange(0.1, 5.0)
        self.spinbox_scale.setValue(1.0)
        self.spinbox_scale.setSingleStep(0.1)
        layout_002.addWidget(QLabel("scale:"))
        layout_002.addWidget(self.spinbox_scale)
        layout_002.addWidget(self.slider_scale)
        layout_002.insertStretch(-1)
        layout_000.addLayout(layout_002)

    def selction_mode_change(self):
        '''
        This function is called when the selection mode radio buttons change state.
        '''
        self.view.selction_mode_change(self.radio_selection_mode_poly.isChecked())

    def scale_slider_change(self, value):
        min_val = self.spinbox_scale.minimum()
        max_val = self.spinbox_scale.maximum()
        fval = ((value/1000.0) * (max_val-min_val)) + min_val
        self.spinbox_scale.setValue(fval)

    def scale_spinbox_change(self, value):
        min_val = self.spinbox_scale.minimum()
        max_val = self.spinbox_scale.maximum()
        int_val = int(((value - min_val)/(max_val-min_val)*1000.0))
        self.slider_scale.setValue(int_val)
        self.view.set_scale(value)

    def eq_change(self, value):
        """ Called when the user changes the image brightness/contrast. """
        self.view.set_brightness(float(self.spinbox_brightness.value()))

    def eq_change_line_width(self, value):
        """ Called when the user changes the segmentation line width. """
        self.view.set_line_width(float(self.spinbox_line_width.value()))

    def checkbox_state_change_paper(self, value):
        """ Called when the user toggles the display of the paper mask. """
        self.view.set_display_paper_polygons(value)

    def checkbox_state_change_spots(self, value):
        """ Called when the user toggles the display of the voids mask. """
        self.view.set_display_spot_polygons(value)

    def set_image(self, img):
        self.view.set_image(img)
        self.set_min_scale()

    def set_title(self, title):
        self.setTitle(title)

    def clear_selection_annotation(self):
        self.view.clear_selection_annotation()

    def get_selection(self):
        '''
        This function returns the current selection polygon.
        If there is no current selection an empty list is returned.
        If the current selection is a polygon, it is return as a list
        of points.  If the current selection is a rectangle, then that
        rectangle is returned as a polygon.
        '''
        if len(self.view.selection_poly_points):
            return self.view.selection_poly_points
        poly = []
        selection = self.view.selection
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

    def get_selection_rect(self):
        return self.view.selection

    def get_selection_poly(self):
        return self.view.selection_poly_points

    def get_view_size(self):
        return self.view.size().width(), self.view.size().height()

    def get_scale(self):
        return(self.view.view_scale)

    def set_scale(self, scale):
        self.scale_spinbox_change(scale)

    def set_min_scale(self):
        if self.view.image is None:
            return
        img_height, img_width = self.view.image.shape
        view_width, view_height = self.get_view_size()
        w_scale = view_width/img_width
        h_scale = view_height/img_height
        min_scale = min(w_scale, h_scale)
        self.spinbox_scale.setRange(min_scale, 5.0)

    def set_paper_annotation(self, paper_polygons):
        self.view.set_paper_annotation(paper_polygons)

    def set_spot_annotation(self, spot_polygons):
        self.view.set_spot_annotation(spot_polygons)

    def set_candidate_annotation(self, candidate_polygons):
        self.view.set_candidate_annotation(candidate_polygons)


class VsaView(QGraphicsView):
 
    def __init__(self):
        super().__init__()
        self.viewport().setAttribute(QtCore.Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
        self.scene = None

        self.selection_color = QColor(0, 255, 255)
        self.paper_annotation_color = QColor(240, 240, 0)
        self.spot_annotation_color = QColor(0, 255, 0)
        self.micro_spot_annotation_color = QColor(198, 132, 227)
        self.nano_spot_annotation_color = QColor(235, 146, 77)
        self.junk_spot_annotation_color = QColor(235, 0, 235)
        self.candidate_annotation_color = QColor(0, 200, 200)

        self.brightness = 0.0

        self.view_scale = 1.0
        self.scale_previous = 1.0

        # NOTE: the way this code handles line width changing with view scale is
        # not ideal.
        self.normalize_line_width_by_scale = True

        self.line_width = 1.0
        self.selection_line_width = 1.0
        self.paper_line_width = 1.0

        self.selection_anchor = [-1, -1]
        self.selection = [-1, -1, 0, 0]
        self.selection_rect = None
        self.selection_poly_points = []
        self.selection_poly = None
        self.polygon_selection_mode = False

        self.img_item = None
        self.image = None
        self.paper_polygon_items = []
        self.display_paper_polygons = True
        self.spot_polygon_items = []
        self.micro_spot_polygon_items = []
        self.nano_spot_polygon_items = []
        self.junk_spot_polygon_items = []
        self.display_spot_polygons = False
        self.candidate_polygon_items = []
        return


    def mouseMoveEvent(self, event):
        if self.image is None:
            return
        if self.polygon_selection_mode == False:
            if self.selection_rect is None:
                return
            if self.selection_anchor[0] == -1:
                return

            x_final, y_final = self._event_to_scene_point(event)
            if x_final < 0:
                x_final = 0
            if y_final < 0:
                y_final = 0
            img_h, img_w = self.image.shape
            if x_final > (img_w-1):
                x_final = img_w-1
            if y_final > (img_h-1):
                y_final = img_h-1

            if x_final < self.selection_anchor[0]:
                x = x_final
                w = self.selection_anchor[0] - x_final
            else:
                x = self.selection_anchor[0]
                w = x_final - self.selection_anchor[0]
            if y_final < self.selection_anchor[1]:
                y = y_final
                h = self.selection_anchor[1] - y_final
            else:
                y = self.selection_anchor[1]
                h = y_final - self.selection_anchor[1]

            self.selection_rect.setRect(x, y, w, h)
            return

        if self.polygon_selection_mode == True:
            x, y = self._event_to_scene_point(event)
            h, w = self.image.shape
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            if x >= w:
                x = w-1
            if y >= h:
                y = h-1
            if self.selection_poly_points[-1] == [x,y]:
                return
            self.selection_poly_points.append([x,y])
            qpoly = QPolygonF()
            for point in self.selection_poly_points:
                qpoly.append(QPointF(point[0], point[1]))
            self.selection_poly.setPolygon(qpoly)

            return

    def mousePressEvent(self, event):
        if self.image is None:
            return
        x, y = self._event_to_scene_point(event)
        h, w = self.image.shape
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x >= w:
            x = w-1
        if y >= h:
            y = h-1
        self.clear_selection_annotation()
        if self.polygon_selection_mode == False:
            self.selection_anchor = [x, y]
            self._clear_candidate_polygons()
            return
        if self.polygon_selection_mode == True:
            self.selection_poly_points = [[x,y]]
            qpoly = QPolygonF()
            qpoly.append(QPointF(x, y))
            self.selection_poly.setPolygon(qpoly)
            return

    def mouseReleaseEvent(self, event):
        if self.image is None:
            return
        if self.polygon_selection_mode == False:
            if self.selection_rect is None:
                return
            self.selection = [-1, -1, 0, 0]
            self.selection_rect.setRect(0, 0, 0, 0)
            self.candidate_polygon_items = []

            x_final, y_final = self._event_to_scene_point(event)
            if x_final < 0:
                x_final = 0
            if y_final < 0:
                y_final = 0
            img_h, img_w = self.image.shape
            if x_final > (img_w-1):
                x_final = img_w-1
            if y_final > (img_h-1):
                y_final = img_h-1
            if (self.selection_anchor[0] == -1) or (self.selection_anchor[1] == -1) or (x_final == self.selection_anchor[0]) or (y_final == self.selection_anchor[1]):
                self.selection = [-1, -1, 0, 0]
                return

            if x_final < self.selection_anchor[0]:
                x = x_final
                w = self.selection_anchor[0] - x_final
            else:
                x = self.selection_anchor[0]
                w = x_final - self.selection_anchor[0]
            if y_final < self.selection_anchor[1]:
                y = y_final
                h = self.selection_anchor[1] - y_final
            else:
                y = self.selection_anchor[1]
                h = y_final - self.selection_anchor[1]

            self.selection = [int(x), int(y), int(w), int(h)]
            self.selection_anchor = [-1, -1]
            self.selection_rect.setRect(x, y, w, h)
            return
        if self.polygon_selection_mode == True:
            pt_list_length = len(self.selection_poly_points)
            if pt_list_length < 5:
                return
            pt.smooth_polygon(self.selection_poly_points)
            qpoly = QPolygonF()
            for point in self.selection_poly_points:
                qpoly.append(QPointF(point[0], point[1]))
            self.selection_poly.setPolygon(qpoly)
            return

    def selction_mode_change(self, polygon_selection_mode):
        self.polygon_selection_mode = polygon_selection_mode
        self.clear_selection_annotation()
        return

    def _clear_paper_polygons(self):
        for item in self.paper_polygon_items:
            self.scene.removeItem(item)
        self.paper_polygon_items = []

    def _clear_candidate_polygons(self):
        for item in self.candidate_polygon_items:
            self.scene.removeItem(item)
        self.candidate_polygon_items = []

    def _clear_spot_polygons(self):
        for item in self.spot_polygon_items+self.micro_spot_polygon_items+self.nano_spot_polygon_items+self.junk_spot_polygon_items:
            self.scene.removeItem(item)
        self.spot_polygon_items = []
        self.micro_spot_polygon_items = []
        self.nano_spot_polygon_items = []
        self.junk_spot_polygon_items = []

    def clear_selection_annotation(self):
        self.selection = [-1, -1, 0, 0]
        if self.selection_rect is not None:
            self.selection_rect.setRect(0, 0, 0, 0)
        self.selection_poly_points = []
        if self.selection_poly is not None:
            qpoly = QPolygonF()
            self.selection_poly.setPolygon(qpoly)
        return


    def _add_image_to_scene(self):
        if self.image is None:
            return
        img_h, img_w = self.image.shape
        tmp_image = self.image.copy()
        eq_factor = 1.0 + 10.0*float(self.brightness)
        tmp_image = tmp_image * eq_factor
        tmp_image = np.minimum(tmp_image, 255.0)
        tmp_image = tmp_image.astype('uint8')

        q_img = QImage(tmp_image.data, img_w, img_h, img_w, QImage.Format.Format_Grayscale8)
        self.img_item = QGraphicsPixmapItem()
        self.img_item.setPixmap(QPixmap.fromImage(q_img))
        self.img_item.setZValue(0)
        self.scene.addItem(self.img_item)
        return

    def _event_to_scene_point(self, event):
        fpoint = self.mapToScene(int(event.position().x()), int(event.position().y()))
        x = int(fpoint.x()+0.5)
        y = int(fpoint.y()+0.5)
        return x, y

    def set_image(self, image):
        if not self.img_item is None:
            self.scene.removeItem(self.img_item)
        self.image = image.copy()
        img_h, img_w = image.shape
        self.scene = QGraphicsScene(0, 0, img_w, img_h)
        self.setScene(self.scene)
        self._add_image_to_scene()

        self.selection = [-1, -1, 0, 0]
        self.selection_rect = QGraphicsRectItem(-1, -1, 0, 0)
        self.selection_rect.setPen(
            QPen(self.selection_color, self.selection_line_width/self.view_scale)
        )
        self.selection_rect.setZValue(4)
        self.scene.addItem(self.selection_rect)

        self.selection_poly_points = []
        qpoly = QPolygonF()
        self.selection_poly = self.scene.addPolygon(qpoly)
        self.selection_poly.setPen(
            QPen(self.selection_color, self.selection_line_width/self.view_scale)
        )
        self.selection_poly.setZValue(4)

        self.paper_polygon_items = []
        self.spot_polygon_items = []
        self.micro_spot_polygon_items = []
        self.nano_spot_polygon_items = []
        self.junk_spot_polygon_items = []
        self.candidate_polygon_items = []

        self.centerOn(int(img_w/2), int(img_h/2))
        return


    def set_paper_annotation(self, paper_polygons):
        if self.scene is None:
            return
        self._clear_paper_polygons()

        # Thickness of paper outline
        pen = QPen(self.paper_annotation_color, self.paper_line_width/self.view_scale)
        for poly in paper_polygons:
            qpoly = QPolygonF()
            for point in poly:
                qpoly.append(QPointF(point[0], point[1]))
            item = self.scene.addPolygon(qpoly, pen)
            item.setZValue(1)
            self.paper_polygon_items.append(item)
        self._update_paper_annotation_view()
        return


    def _update_paper_annotation_view(self):
        for item in self.paper_polygon_items:
            item.setVisible(self.display_paper_polygons)
        return


    def set_spot_annotation(self, spot_polygons):
        if self.scene is None:
            return
        self._clear_spot_polygons()
        self._clear_candidate_polygons()
        pen_primary = QPen(self.spot_annotation_color, self.line_width)
        pen_micro = QPen(self.micro_spot_annotation_color, self.line_width)
        pen_nano = QPen(self.nano_spot_annotation_color, self.line_width)
        pen_junk = QPen(self.junk_spot_annotation_color, self.line_width)
        for props in spot_polygons:
            poly = props['points']
            if props['class'] == 'junk':
                pen = pen_junk
            elif props['class'] == 'nano':
                pen = pen_nano
            elif props['class'] == 'micro':
                pen = pen_micro
            else:
                pen = pen_primary

            qpoly = QPolygonF()
            for point in poly:
                qpoly.append(QPointF(point[0], point[1]))
            item = self.scene.addPolygon(qpoly, pen)
            item.setZValue(2)
            if props['class'] == 'junk':
                self.junk_spot_polygon_items.append(item)
            elif props['class'] == 'nano':
                self.nano_spot_polygon_items.append(item)
            elif props['class'] == 'micro':
                self.micro_spot_polygon_items.append(item)
            else:
                self.spot_polygon_items.append(item)
        self._update_spot_annotation_view()
        return


    def _update_spot_annotation_view(self):
        for item in self.spot_polygon_items+self.micro_spot_polygon_items+self.nano_spot_polygon_items+self.junk_spot_polygon_items:
            item.setVisible(self.display_spot_polygons)
        return


    def set_candidate_annotation(self, candidate_polygons):
        if self.scene is None:
            return
        self._clear_candidate_polygons()
        pen = QPen(self.candidate_annotation_color, self.line_width)
        for poly in candidate_polygons:
            qpoly = QPolygonF()
            for point in poly:
                qpoly.append(QPointF(point[0], point[1]))
            item = self.scene.addPolygon(qpoly, pen)
            item.setZValue(3)
            self.candidate_polygon_items.append(item)
        return


    def set_scale(self, view_scale):
        self.scale((1/self.view_scale), (1/self.view_scale))
        self.view_scale = view_scale
        self.scale(self.view_scale, self.view_scale)
        pen = QPen(self.paper_annotation_color, self.paper_line_width/view_scale)
        for item in self.paper_polygon_items:
            item.setPen(pen)
        pen = QPen(self.candidate_annotation_color, self.line_width)
        for item in self.candidate_polygon_items:
            item.setPen(pen)
        pen1 = QPen(self.spot_annotation_color, self.line_width)
        for item in self.spot_polygon_items:
            item.setPen(pen1)
        pen2 = QPen(self.micro_spot_annotation_color, self.line_width)
        for item in self.micro_spot_polygon_items:
            item.setPen(pen2)
        pen3 = QPen(self.nano_spot_annotation_color, self.line_width)
        for item in self.nano_spot_polygon_items:
            item.setPen(pen3)
        pen4 = QPen(self.junk_spot_annotation_color, self.line_width)
        for item in self.junk_spot_polygon_items:
            item.setPen(pen4)
        pen5 = QPen(self.selection_color, self.selection_line_width/self.view_scale)
        if self.selection_poly is not None:
            self.selection_poly.setPen(pen5)
        if self.selection_rect is not None:
            self.selection_rect.setPen(pen5)

    def set_display_paper_polygons(self, state):
        self.display_paper_polygons = state
        self._update_paper_annotation_view()

    def set_display_spot_polygons(self, state):
        self.display_spot_polygons = state
        self._update_spot_annotation_view()

    def set_brightness(self, val):
        self.brightness = val
        if self.image is None:
            return
        if self.img_item is None:
            return
        self._add_image_to_scene()
        return
    
    def set_line_width(self, val):
        if self.normalize_line_width_by_scale:
            self.line_width = val / self.view_scale
        else:
            self.line_width = val
        if self.image is None or self.img_item is None:
            return
        self._add_image_to_scene()
        return


