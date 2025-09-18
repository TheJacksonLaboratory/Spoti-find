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


import sys
import inspect
import polygon_tools as pt

class TestPolygonTools:
    def __init__(self):
        self.test_list = {
            'circularity_001':self.circularity_001,
            'circularity_002':self.circularity_002
        }
        self.epsilon = 0.0001

    def run_all(self):
        for key in self.test_list:
            print(f"{key}: ", end=" ")
            self.test_list[key]()
        return

    def run_test(self, test_name):
        print(f"{test_name}: ", end=" ")

        if test_name not in self.test_list:
            print("TEST NO FOUND")
            return False
        self.test_list[test_name]()
        return True

    def circularity_001(self):
        frame = inspect.currentframe()
        function_name = inspect.getframeinfo(frame).function
        print(f"{function_name}:", end=" ")

        polygon = [(0, 0), (100, 0), (100, 100), (0, 100)]
        circularity = pt.circularity(polygon)
        if abs(circularity - 0.7853981633974483) < self.epsilon:
            print("Pass")
        else:
            print("FAIL")
            print(f"    expected 0.7853981633974483, saw {circularity}")


    def circularity_002(self):
        frame = inspect.currentframe()
        function_name = inspect.getframeinfo(frame).function
        print(f"{function_name}:", end=" ")

        polygon = [(0, 0), (100, 0), (100, 100), (100, 0), (0, 0)]
        circularity = pt.circularity(polygon)
        if abs(circularity) < self.epsilon:
            print("Pass")
        else:
            print("FAIL")
            print(f"    expected 0.0, saw {circularity}")



def main():
    test_class = TestPolygonTools()
    if len(sys.argv) <= 1:
        test_class.run_all()
    else:
        for test_name in sys.argv[1:]:
            test_class.run_test(test_name)
    return

if __name__ == '__main__':
    main()

