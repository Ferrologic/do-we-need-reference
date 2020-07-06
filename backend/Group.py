# coding: utf-8

import numpy as np
from backend.Point import Point
from backend.KoffValues import KoffValues
import logging
import copy


log = logging.getLogger(__name__)


class Group:

    def __init__(self):
        self.points = []
        self.arrKoff = None
        self.breakpoints = []
        self._kvot = None

    def __str__(self):
        return_str = ''
        for p in self.points:
            if isinstance(p, Point):
                return_str += str(p)
        return return_str

    def set_breakpoints(self, breakpoints):
        self.breakpoints = breakpoints

    def set_points(self, points):
        self.points = points

    def addPoint(self, point):
        self.points.append(point)

    def getSize(self):
        return len(self.points)

    def split(self):
        """
        Will split the group in two and copy every value below its regressionvalue in one group above in the second

        :return:
        """
        # self.calcRegValues()
        arr_list = []
        arr_above = Group()
        arr_above.set_breakpoints(self.breakpoints)
        arr_below = Group()
        arr_below.set_breakpoints(self.breakpoints)
        for p in self.points:
            if(p.reading <= p.regression):
                arr_above.addPoint(copy.copy(p))
            else:
                arr_below.addPoint(copy.copy(p))
        arr_list.append(arr_above)
        arr_list.append(arr_below)
        return arr_list

    def kvot(self):
        """
        Calculate the sum of the each diff between value and reg
        :return:
        """
        if self._kvot is None:
            # self.calcRegValues(self.arrKoff)
            self.calcRegValues()
            self._kvot = sum((p.reading - p.regression)**2 for p in self.points)
        return self._kvot

    def calcRegValues(self, koff=None):
        if self.getSize() < len(self.breakpoints):
            return
        if koff is None:
            koff = self.calcKoff()
        self.updatePointRegression(koff)

    def updatePointRegression(self, koff):
        if self.getSize() < len(self.breakpoints):
            return
        for i in range(0, self.getSize()):
            p = self.getPoint(i)
            p.get_reg_value(koff)

    def calcKoff(self):
        tmpM = self.asMatrix()
        rm = self.checkGroup()
        if len(rm) > 2:
            log.debug("för få punkter")
        tmpM = np.delete(tmpM, rm, 1)
        tmpE = self.get_readings()
        tmpE1 = np.linalg.inv(np.matmul(tmpM.transpose(), tmpM))
        tmpE2 = tmpM.transpose().dot(tmpE)
        tmpKoff = tmpE1.dot(tmpE2)
        #log.debug('tmpKoff is {}'.format(tmpKoff))
        rv = KoffValues(self.breakpoints)
        tmpKoff = rv.setIncompleteKoff(tmpKoff, rm)
        #log.debug('tmpKoff after incompleteKoff is {}'.format(tmpKoff))
        self.setCalcKoff(tmpKoff)
        return tmpKoff

    def setCalcKoff(self, arr):
        self.arrKoff = arr

    def asMatrix(self):
        tmp_matrix = np.zeros((self.getSize(), len(self.breakpoints)))
        for k in range(0, self.getSize()):
            p = self.getPoint(k)
            a = p.getArrTemp()
            for j in range(0, len(self.breakpoints)):
                d = a[j]
                tmp_matrix[k, j] = d
        return tmp_matrix

    def getPoint(self, i):
        return self.points[i]

    def get_readings(self):
        """
        Gets an array of the values in the group
        :return:
        """
        tmp_array = np.zeros(self.getSize())
        for i in range(0, self.getSize()):
            e = self.getPoint(i).reading
            tmp_array[i] = e
        return tmp_array

    def checkGroup(self):
        """
        Check if there is to few values in a temperature area
        :return:

        """
        # log.debug('entering checkGroup')
        tmp = []
        temp = [0] * len(self.breakpoints)
        min = [1000] * len(self.breakpoints)
        max = [-1000] * len(self.breakpoints)
        for i in range(0, len(self.points)):
            p = self.getPoint(i)
            prev_bp = -1000
            for j in range(1, len(self.breakpoints)):
                if j != len(self.breakpoints)-1:
                    cur_bp = 1000
                cur_bp = self.breakpoints[j]
                if prev_bp <= p.temp < cur_bp:
                    temp[j] += 1
                    if p.temp < min[j]:
                        min[j] = p.temp
                    if p.temp > max[j]:
                        max[j] = p.temp
                prev_bp = cur_bp
        # log.debug('temp= {}'.format(temp))
        for i in range(1, len(temp)):
            # if not enough points in temp[i], discard breakpoint i
            # print(f'Checking temp[{i}] = {temp[i]}')
            if temp[i] < 5:
                tmp.append(i)
        # log.debug('tmp= {}'.format(tmp))
        for i in range(1, len(temp)):
            # print(f'Checking temp[{i}] = {temp[i]}')
            if max[i] - min[i] < 2 and i not in tmp:
                tmp.append(i)
        # log.debug('returns {}'.format(tmp))
        # log.debug('temp is {}'.format(temp))
        # log.debug('min is {}'.format(min))
        # log.debug('max is {}'.format(max))
        # log.debug('returns {}'.format(tmp))
        return tmp
