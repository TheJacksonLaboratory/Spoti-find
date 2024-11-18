
"""
Copyright The Jackson Laboratory, 2023
authors: Jim Peterson

The VsaProcessor class implements the "voided spot analysys" on
images of mouse cage floor papers.

"""
import os
import math
import numpy as np
import cv2
import polygon_tools as pt

class VsaProcessor():

    def __init__(self):
        """
        class constructor
        These class variables should be accessed via the "get_" functions.
        """
        self.image_file = ""        # File name of currently open image
        self.img = None             # Grayscale image of cage floor paper
        self.img_extended = None
        self.paper_mask = None  # Binary mask of paper
        self.paper_polygon = []
        self.spot_mask = None
        self.spot_polygons = []
        self.spot_polygon_properties = []
        self.roi_polygons = []
        self.win_size = 100

    def open_image(self, filename: str) -> bool:
        """
        Opens image file.  The specified image file is opened as a grayscale image.
        both 8-bit and 16-bit images are supported in standard formats.
        After the successful call, the class variables "image_file" and "img" are set,
        and all others are reset.

        Parameters:
            filename (string) - image file to open and process
        returns:
            True if sucessful, False otherwise
        """
        # Reset all variables
        self.image_file = ""
        self.img = None
        self.paper_mask = None
        self.dist_map = None
        self.spot_mask = None

        self.paper_polygon = []
        self.spot_polygons = []
        self.spot_polygon_properties = []

        self.roi = [0, 0, 0, 0]
        self.roi_mask = None
        self.roi_polygons = []

        img = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
        if (img is None) or (not img.data):
            return False
        self.image_file = filename
        self.img = img
        h, w = self.img.shape
        self.spot_mask = np.zeros((h, w)).astype(np.uint8)
        return True

    def have_img(self) -> bool:
        """ Returns True if an image has been successfully loaded, False otherwise. """
        if (self.img is None) or (not self.img.data):
            return False
        return True

    def get_img(self):
        """ Returns currently opened image """
        if self.have_img:
            return self.img
        else:
            return None

    def get_img_dim(self) -> (int,int):
        """ Returns the dimensions (W, H) of the currently open image. """
        if self.have_img():
            return self.img.shape
        else:
            return 0,0


    def get_default_paper_threshold(self):
        '''
        The default threshold for segmentation of the paper from the background is a weighted
        average of thresholds computed from the triangle and Otsu methods, with the triangle
        threshold given a weight of 0.75.
        '''
        if not self.have_img():
            return -1
        triangle_weight = 0.75
        thresh, _ = cv2.threshold(self.img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_TRIANGLE)
        thresh_otsu, _ = cv2.threshold(self.img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        thresh_triangle, _ = cv2.threshold(self.img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_TRIANGLE)
        thresh = int((1.0-triangle_weight)*thresh_otsu+(triangle_weight)*thresh_triangle)

        thresh = int(thresh)
        thresh = max(thresh, 0)
        thresh = min(thresh, 255)
        return int(thresh)


    def segment_paper(self, threshold) -> bool:
        """
        Segmenting the paper from the background, this function computes the binary
        mask of the floor paper.  The resulting image has a value of 255 where the
        paper is identified, and 0 on the background.  This function processed the
        current image, self.img, and creates the mask, self.paper_mask.

        The mask is created with the fixed threshold.
        """
        if not self.have_img():
            return False
        _, paper_mask = cv2.threshold(self.img, threshold, 255, cv2.THRESH_BINARY)
        if (paper_mask is None) or (not np.any(paper_mask)):
            return False
        kernel = np.ones((3,3), np.uint8)
        paper_mask = cv2.erode(paper_mask, kernel, iterations=1)
        paper_mask = cv2.dilate(paper_mask, kernel, iterations=1)
        paper_contours, _ = cv2.findContours(image=paper_mask, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE)
        idx_of_largest_contour = pt.largest_contour(paper_contours)
        self.paper_mask = np.zeros(paper_mask.shape, dtype=np.uint8)
        cv2.drawContours(self.paper_mask, [paper_contours[idx_of_largest_contour]], -1, color=255, thickness=cv2.FILLED)
        self.paper_polygon = pt.contour_to_polygon(paper_contours[idx_of_largest_contour])
        self.extend_image()

        # Create distance map
        self.dist_map = cv2.distanceTransform(self.paper_mask, cv2.DIST_L2, 3)
        self.dist_map = self.dist_map.astype(np.uint16)
        papermask = self.paper_mask.astype(np.uint16)
        cv2.imwritemulti("dist_map.tif", [self.dist_map, papermask])
        return True


    def measure_spots(self, volume_mapper, pix_per_cm, size_thresh_list) -> float:
        """
        Measures the area of all the currently identified spots.
        """
        self.spot_polygon_properties = []
        for polygon in self.spot_polygons:
            poly_props = {}

            # img_x, img_y, img_w, img_h
            x, y, w, h = pt.polygon_mbr(polygon)
            poly_props['img_x'] = x
            poly_props['img_y'] = y
            poly_props['img_w'] = w
            poly_props['img_h'] = h

            # perimeter_pix
            poly_props['perimeter_pix'] = pt.polygon_perimeter(polygon)
            poly_props['perimeter_cm'] = poly_props['perimeter_pix'] / pix_per_cm

            # area_pix2
            poly_props['area_pix2'] = pt.polygon_area(polygon)
            poly_props['area_cm2'] = poly_props['area_pix2'] / (pix_per_cm**2)
            poly_props['volume_ul'] = volume_mapper.map_area(poly_props['area_cm2'])
            if len(size_thresh_list) == 3:
                if poly_props['volume_ul'] < size_thresh_list[0]:
                    poly_props['class'] = 'junk'
                elif poly_props['volume_ul'] < size_thresh_list[1]:
                    poly_props['class'] = 'nano'
                elif poly_props['volume_ul'] < size_thresh_list[2]:
                    poly_props['class'] = 'micro'
                else:
                    poly_props['class'] = 'primary'

            # eccentricity
            poly_props['eccentricity'] = pt.eccentricity(polygon)

            # dist_to_edge_pix
            spot_mask = np.zeros(self.paper_mask.shape, dtype=np.uint8)
            cv2.drawContours(spot_mask, [pt.polygon_to_contour(polygon)], -1, color=255, thickness=cv2.FILLED)
            count = np.sum(spot_mask == 255)
            masked_dist_map = np.where(spot_mask>0, self.dist_map, 0)
            sum = np.sum(masked_dist_map)
            poly_props['ave_dist_to_edge_pix'] = sum/count
            poly_props['ave_dist_to_edge_cm'] = poly_props['ave_dist_to_edge_pix'] / pix_per_cm
            poly_props['points'] = polygon

            self.spot_polygon_properties.append(poly_props)


        self.spot_polygon_properties = sorted(self.spot_polygon_properties, key=lambda d: d['volume_ul'], reverse=True)
        area_pix = 0.0
        for prop in self.spot_polygon_properties:
            if prop['class'] == 'junk':
                break
            area_pix += prop['area_pix2']
        return area_pix


    def _vectorize_spots(self):
        polygons = []
        spot_contours, _ = cv2.findContours(image=self.spot_mask, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE)
        for contour in spot_contours:
            polygon = pt.contour_to_polygon(contour)
            polygons.append(polygon)
        self.spot_polygons = polygons


    def save_roi_spots(self):
        if len(self.roi_polygons) == 0:
            return
        x = self.roi[0]
        y = self.roi[1]
        w = self.roi[2]
        h = self.roi[3]
        self.spot_mask[y:y+h, x:x+w] = np.bitwise_or(self.spot_mask[y:y+h, x:x+w], self.roi_mask)
        self._vectorize_spots()
        return


    def clear_poly_selection(self, polygon):
        if self.img is None:
            return
        contour = pt.polygon_to_contour(polygon)
        #mask = np.zeros(self.img.shape, dtype=np.uint8)
        cv2.drawContours(self.spot_mask, [contour], -1, color=0, thickness=cv2.FILLED)
        self._vectorize_spots()
        return


    def fill_poly_selection(self, polygon):
        if self.img is None:
            return
        contour = pt.polygon_to_contour(polygon)
        #mask = np.zeros(self.img.shape, dtype=np.uint8)
        cv2.drawContours(self.spot_mask, [contour], -1, color=255, thickness=cv2.FILLED)
        self._vectorize_spots()
        return


    def extend_image(self):
        '''
        This function computes the median value of the image in the paper mask area.  This value is then
        written to all pixels in the original image, outside the paper mask.

        Note: it may be better to set the value of the background pixels to the value closest in the mask.
        '''
        tmp_list = np.where(self.paper_mask>0, self.img, 0).flatten().tolist()
        tmp_list = [x for x in tmp_list if x > 0]
        self.img_median = np.median(tmp_list)
        img_type = type(self.img[0][0])
        self.img_extended = np.where(self.paper_mask>0, self.img, self.img_median).astype(img_type)

        dir_name = os.path.dirname(self.image_file)
        extended_img_path = os.path.join(dir_name, "extended_img.tif")
        cv2.imwrite(extended_img_path, self.img_extended)


    def _find_spots_in_rect(self, roi, threshold_adjustment=0, min_range=0, min_dist_from_median=10):
        self.roi = roi
        self.roi_mask = None
        self.roi_polygons = []
        contours = []
        x = roi[0]
        y = roi[1]
        w = roi[2]
        h = roi[3]
        roi_img = self.img_extended[y:y+h, x:x+w]
        tmp_list = roi_img.flatten().tolist()
        tmp_list = np.sort(tmp_list)
        min_val = tmp_list[0]
        max_val = tmp_list[-1]
        median_val = tmp_list[int(len(tmp_list)/2)]
        median_loc = int(100*(median_val-min_val)/(max_val-min_val+1))
        roi_range = max_val - min_val

        triangle_weight = 0.0
        thresh_otsu, _ = cv2.threshold(roi_img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)
        thresh_triangle, _ = cv2.threshold(roi_img, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_TRIANGLE)
        thresh = int((1.0-triangle_weight)*thresh_otsu+(triangle_weight)*thresh_triangle)
        thresh = thresh + threshold_adjustment
        thresh = max(1, min(thresh, 255))

        print(f"    ({x}, {y}, {w}x{h}) {self.img_median=} {median_val=} {roi_range=} {median_loc=} {thresh=} {min_range=} {min_dist_from_median=}")
        _, roi_mask = cv2.threshold(roi_img, thresh, 255, cv2.THRESH_BINARY)

        if (roi_mask is None) or (not np.any(roi_mask)):
            return contours, None

        if thresh < self.img_median:
            return contours, None
        if roi_range < min_range:
            return contours, None
        if (thresh - self.img_median) < min_dist_from_median:
            return contours, None

        # only include exterior contours
        self.roi_mask = roi_mask
        contours, _ = cv2.findContours(image=roi_mask, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_NONE)
        polygons = []
        for contour in contours:
            contour += (roi[0], roi[1])
            polygon = pt.contour_to_polygon(contour)
            polygons.append(polygon)

        return polygons, roi_mask


    def set_spot_polygons(self, polygons):
        if self.img is None:
            return False
        self.spot_polygons = polygons
        contours = []
        for polygon in polygons:
            contours.append(pt.polygon_to_contour(polygon))
        self.spot_mask = np.zeros(self.img.shape, dtype=np.uint8)
        cv2.drawContours(self.spot_mask, contours, -1, color=255, thickness=cv2.FILLED)


    def segment_spots_in_roi(self, roi, threshold_adjustment=0, min_range=0, min_dist_from_median=10):
        '''
        '''
        if not self.have_img():
            return
        self.roi_polygons, _ = self._find_spots_in_rect(roi, threshold_adjustment, min_range, min_dist_from_median)
        return


    def segment_spots(self, threshold_adjustment=0, min_range=40, min_dist_from_median=10):
        '''
        '''
        win_size = self.win_size
        self.roi_polygons = []
        self.spot_polygons = []
        if not self.have_img():
            return

        h, w = self.img.shape

        x_count = math.ceil(w / win_size)
        y_count = math.ceil(h / win_size)
        tiles = []
        for y_idx in range(y_count):
            for x_idx in range(x_count):
                x1 = x_idx * win_size
                y1 = y_idx * win_size
                x2 = min((x1+win_size), w)
                y2 = min((y1+win_size), h)
                tiles.append([x1, y1, x2, y2])

        self.spot_mask = np.zeros((h, w))
        idx = 1
        for tile in tiles:
            roi = [tile[0], tile[1], (tile[2]-tile[0]), (tile[3]-tile[1])]
            _, roi_mask = self._find_spots_in_rect(roi, threshold_adjustment, min_range, min_dist_from_median)

            x1 = tile[0]
            y1 = tile[1]
            x2 = tile[2]
            y2 = tile[3]
            self.spot_mask[y1:y2, x1:x2] = roi_mask

        self.spot_mask = self.spot_mask.astype(np.uint8)
        self.spot_mask = np.where(self.paper_mask==0, 0, self.spot_mask)
        cv2.imwritemulti("debug_stack.tif", [self.spot_mask, self.img])
        print("debug files: debug_stack.tif")

        self._vectorize_spots()
        return
