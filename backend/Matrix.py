from backend.Group import Group
from backend.KoffValuesGroup import KoffValuesGroup
from backend.Point import Point
from backend.KoffValues import KoffValues
from datetime import datetime
import numpy as np
import logging

log = logging.getLogger(__name__)


class Matrix:

    def __init__(self, breakPoints=[]):
        self._groups = []
        self.refGroup = Group()
        self.regGroup = Group()
        self.refValuesGroup = KoffValuesGroup()
        self.regValuesGroup = None
        self.latest = None
        self.breakPoints = breakPoints
        # self.Group.breakPoints = breakPoints

    def addGroup(self, group):
        self._groups.append(group)

    def getSize(self):
        return len(self._groups)

    @property
    def groups(self):
        return self._groups

    @groups.setter
    def groups(self, g):
        self._groups = g

    def split(self, max_groups, kvot_splittring):
        if len(self._groups) >= max_groups:
            return
        arrTmp = self._groups
        while len(arrTmp) < max_groups:
            arrCheck = []
            splitMade = False
            for g in arrTmp:
                kvot_tot = g.kvot()
                arrKvot = g.split()
                upper = arrKvot[0]
                lower = arrKvot[1]
                kvot_a = upper.kvot()
                kvot_b = lower.kvot()
                kvot = (float(kvot_a) + float(kvot_b)) / float(kvot_tot)
                if kvot <= kvot_splittring:
                    arrCheck.append(upper)
                    arrCheck.append(lower)
                    splitMade = True
                    log.debug('split: will split')
                else:
                    arrCheck.append(g)
            arrTmp = arrCheck
            if not splitMade:
                break
        self._groups = arrTmp

    def calculate_total_kvot(self):
        sum = 0.0
        for group in self._groups:
            sum += group.kvot()
        return sum

    def base(self, int_number, tolerance):
        """ Used to check if invidual meter_readings are in the optimal group

        It will stop when no meter_readings moves

        Args:
            int_number (int) : Max times it will move around meter_readings values
            tolerance (float) : When the kvot is lower than this value, it will stop

        Returns: 
            None 
        """
        if len(self._groups) < 2:
            return
        for timescount in range(0, int_number):
            kvot_before = self.calculate_total_kvot()
            arrNew = self.base_one(self._groups)
            self._groups = arrNew
            kvot_after = self.calculate_total_kvot()
            if abs(kvot_after-kvot_before) < tolerance:
                break

    def base_one(self, original_groups):
        """ calculates the diff between from a point to each group and moves it

        Args:
            original_groups ([groups]): list of groups

        Return:
            [group] : new list where points have been moved to the optimal group

        """
        if len(original_groups) < 2:
            return original_groups
        arr_temp = []
        reg_groups_values = []

        # Copy the coffecients for each group and store them
        for group in original_groups:
            new_group = Group()
            new_group.set_breakpoints(self.breakPoints)
            arr_temp.append(new_group)
            reg_groups_values.append(group.calcKoff())

        for group_count, group in enumerate(original_groups):
            master_cofficient = reg_groups_values[group_count]
            for point_count, point in enumerate(group.points):
                bestgroup = group_count
                master_diff = abs(point.reading
                                  - point.get_reg_value(master_cofficient))
                for alternative_group_count, alternative_group in enumerate(original_groups):
                    if group_count == alternative_group_count:
                        continue
                    alternative_coffecient = reg_groups_values[alternative_group_count]
                    alternative_diff = abs(point.reading
                                           - point.get_reg_value(alternative_coffecient))
                    if master_diff > alternative_diff:
                        bestgroup = alternative_group_count
                g = arr_temp[bestgroup]
                g.addPoint(point)
        return arr_temp

    def calcKoff(self, g):
        group = self._groups[g]
        tmpKoff = group.calcKoff()
        self.convertToRegValuesGroup(tmpKoff, group)
        return tmpKoff

    def cleanMatrix(self, matrix, list):
        matrix = np.delete(matrix, list, 1)
        return matrix

    def convertToRegValuesGroup(self, koff, group):
        if self.regValuesGroup == None:
            self.regValuesGroup = KoffValuesGroup()
        regValues = KoffValues(self.breakPoints, np.array(koff))
        regValues.setPeriod(0)
        self.regValuesGroup.addRegValue(regValues, group)

    def setPlotGroup(self, tmpKoff):
        self.refGroup = self.plotGroup(tmpKoff)

    def plotGroup(self, koff):
        g = Group()
        for breakPoint in self.breakPoints:
            p = Point(0, breakPoint, datetime.now(), self.breakPoints)
            g.addPoint(p)
        for i in range(0, g.getSize()):
            tmpArr = g.getPoint(i).getArrTemp()
            d = tmpArr.dot(koff)
            g.getPoint(i).setMeasurement(d)
            g.getPoint(i).setRegression(d)
        return g

    def updateFromReg(self):
        for g in self._groups:
            # FIX Här blir det fel! Står det i Java-koden
            g.calcRegValues(self.regValuesGroup.getRegValues(0)[1].getKoff())

    def getRefGroup(self, group=None, period=None):
        if group == None and period == None:
            if self.refGroup == None:
                self.setPlotGroup(
                    self.refValuesGroup.getRegValues(0).getKoff())
            return self.refGroup
        else:
            refValues = self.refValuesGroup.getRegValues(group)
            returnGroup = self.plotGroup(refValues.getKoff())
            return returnGroup

    # Test function, for development only
    def testPlotSplit(self, upper, lower):
        x_upper = []
        y_upper = []
        x_lower = []
        y_lower = []
        for p in upper.points:
            x_upper.append(p.getTemp())
            y_upper.append(p.getEnergy())
        for p in lower.points:
            x_lower.append(p.getTemp())
            y_lower.append(p.getEnergy())
        # plt.plot(x_upper, y_upper, 'bo', markersize = 1.5)
        # plt.plot(x_lower, y_lower, 'ro', markersize = 1.5)
        # plt.grid(True)
        # plt.show()
