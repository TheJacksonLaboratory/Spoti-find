# Spoti-find - Copyright (C) 2025 The Jackson Laboratory, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


"""
Copyright The Jackson Laboratory, 2023
authors: Jim Peterson
"""
import math
import numpy as np


def contour_to_polygon(contour):
    """
    Converts a contour (numpy array), as would be produced by OpenCVs findContours function, to
    a simple list of points.
    """
    polygon = []
    for obj in contour.tolist():
        polygon.append(obj[0])
    return polygon

def polygon_to_contour(polygon):
    """
    Computes a simple list of points to a contour (numpy array) as would be returned from
    OpenCV's findContours function.
    """
    contour = np.array([[p] for p in polygon]).astype(np.int32)
    return contour

def polygon_perimeter(pt_list):
    """
    Compute the polygon perimeter length.
    """
    sum = 0.0
    for idx in range(len(pt_list)-1):
        dx = pt_list[idx+1][0] - pt_list[idx][0]
        dy = pt_list[idx+1][1] - pt_list[idx][1]
        sum += math.sqrt(dx*dx + dy*dy)

    dx = pt_list[0][0] - pt_list[-1][0]
    dy = pt_list[0][1] - pt_list[-1][1]
    sum += math.sqrt(dx*dx + dy*dy)
    return sum

def polygon_center(pt_list):
    """
    This computes the weighted average of the vertices.
    Note: This is NOT the center of weight of the polygon, but does
    a good job of approximating it for polygons with many short sides.
    """
    if not pt_list:
        return None
    x = sum([p[0] for p in pt_list])/len(pt_list)
    y = sum([p[1] for p in pt_list])/len(pt_list)
    return (x, y)

def polygon_signed_area(pt_list) -> float:
    """
    Compute signed polygon area.  Clockwise - positive.
    Note: self-intersections create holes.
    """
    if (pt_list is None) or (len(pt_list) < 3):
        return 0.0
    sum = 0.0
    vertex_count = len(pt_list) - 1
    for idx in range(len(pt_list)-1):
        sum += (pt_list[idx][1]*pt_list[idx+1][0] - pt_list[idx][0]*pt_list[idx+1][1]);

    if (pt_list[0][0] != pt_list[-1][0]) or (pt_list[0][1] != pt_list[-1][1]):
        sum += (pt_list[-1][1]*pt_list[0][0] - pt_list[-1][0]*pt_list[0][1]);

    sum /= 2.0;
    return sum


def polygon_area(pt_list):
    """
    Computes the unsigned area of a polygon
    """
    area = polygon_signed_area(pt_list)
    if area < 0.0:
        area *= -1.0
    return area

def point_in_polygon_mbr(pt, polygon):
    mbr = polygon_mbr(polygon)
    x = mbr[0]
    y = mbr[1]
    w = mbr[2]
    h = mbr[3]
    if pt[0] < x or pt[0] > (x+w):
        return False
    if pt[1] < y or pt[1] > (y+h):
        return False
    return True

def polygon_mbr(polygon):
    x_coords = [pt[0] for pt in polygon]
    y_coords = [pt[1] for pt in polygon]
    x = min(x_coords)
    w = max(x_coords) - x + 1
    y = min(y_coords)
    h = max(y_coords) - y +1
    return (x, y, w, h)

def largest_contour(contours):
    '''
    Finds the polygon of largest area from a list of polygons.
    The input list is a list of contours as created by OpenCV.
    '''
    if contours is None:
        return -1

    polygons = []
    for contour in contours:
        polygon = contour_to_polygon(contour)
        polygons.append(polygon)
    return largest_polygon(polygons)



def largest_polygon(polygons):
    '''
    Finds the polygon of largest area from a list of polygons.
    '''
    if (polygons is None) or (len(polygons) <= 0):
        return -1
    max_area = 0.0
    max_idx = 0
    for idx in range(len(polygons)):
        area = polygon_area(polygons[idx])
        if area > max_area:
            max_area = area
            max_idx = idx
    return max_idx


def circularity(polygon):
    '''
    Computes the circularity of a given polygon
    '''
    L = polygon_perimeter(polygon)
    if L <= 0.0:
        return 0.0
    A = polygon_area(polygon)
    C = (4.0*math.pi*A)/(L*L)
    return C


def smooth_polygon(polygon):
    '''
    This is a simple smoothing algorithm.  It assumes that there are no long
    edges, so it is not suitable for all polygons.  This algorithm simply
    performs a running average of the points.
    '''
    if len(polygon) < 5:
        return
    for idx in range(len(polygon)-1):
        x = (polygon[idx-1][0] + polygon[idx][0] + polygon[idx+1][0])/3
        y = (polygon[idx-1][1] + polygon[idx][1] + polygon[idx+1][1])/3
        polygon[idx][0] = int(x)
        polygon[idx][1] = int(y)

