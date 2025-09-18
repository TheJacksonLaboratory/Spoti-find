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


class AreaVolumeMap():
    '''
    This class for mapping area of spot to volume.
    The mapping uses a 2nd order poly of the form V(x) = c2*x^2 + c1*x
    '''
    def __init__(self):
        self.c1 = 0.0  # coeficient on the linear term
        self.c2 = 0.0  # coeficient on the squared term
        return

    def map_area(self, area_cm2):
        '''
        '''
        volume_uL = self.c2*area_cm2*area_cm2 + self.c1*area_cm2
        return volume_uL

    def compute_model(self, points):
        self.c1 = 0.0
        self.c2 = 0.0

        if len(points) <= 0:
            return False

        if len(points) <= 3:
            self._compute_linear_model(points)
        else:
            self._compute_second_order_model(points)

        return True

    def _compute_second_order_model(self, points):
        a1 = b1 = c1 = 0.0
        a2 = b2 = c2 = 0.0
        for p in points:
            x = p[0]
            y = p[1]
            a1 += x**3
            b1 += x**2
            c1 += x*y
            a2 += x**4
            b2 += x**3
            c2 += x*x*y
        self.c2 = (b2*c1 - b1*c2)/(a1*b2 - a2*b1)
        self.c1 = (a1*c2 - a2*c1)/(a1*b2 - a2*b1)
        return

    def _compute_linear_model(self, points):
        sum_xx = 0.0
        sum_xy = 0.0
        for point in points:
            sum_xx += point[0]**2
            sum_xy += point[0]*point[1]
        self.c1 = sum_xy/sum_xx
        self.c2 = 0.0


