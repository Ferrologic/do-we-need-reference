import numpy as np
import logging

log = logging.getLogger(__name__)


class Point:

    def __init__(self, reading=0.0, temp=0.0, timestamp=None, breakpoints=[-5, 2, 9, 15, 20]):
        self.__arrTemp = None
        self.__reading = reading
        self.__temp = temp
        self.__timestamp = timestamp
        self.__regression = 0
        self.__breakpoints = breakpoints
        self.__consumtion_timestamp = None
        self.__reg_value = None

    def __str__(self):
        # print('temp: {}, time: {}, value: {}'.format(self.temp, self.timestamp, self.measurement))
        return 'p =  time : {}, temp: {}, value: {} '.format(
            self.timestamp, self.temp, self.reading)

    @property
    def reading(self):
        return self.__reading

    @reading.setter
    def reading(self, m):
        self.__reading = m

    @property
    def regression(self):
        return self.__regression

    @regression.setter
    def regression(self, r):
        self.__regression = r

    @property
    def temp(self):
        return self.__temp

    @temp.setter
    def temp(self, t):
        self.__temp = t
        self.fix_temp(self.temp, self.breakpoints)

    @property
    def timestamp(self):
        return self.__timestamp

    @timestamp.setter
    def timestamp(self, t):
        self.__timestamp = t

    @property
    def breakpoints(self):
        return self.__breakpoints

    @breakpoints.setter
    def breakpoints(self, bp):
        self.__breakpoints = bp
        self.fix_temp(self.temp, self.breakpoints)

    @property
    def consumption_timestamp(self):
        return self.__consumtion_timestamp

    @consumption_timestamp.setter
    def consumption_timestamp(self, _datetime):
        self.__consumtion_timestamp = _datetime

    def getArrTemp(self):
        if self.__arrTemp is None:
            self.fix_temp(self.temp, self.breakpoints)
        return np.array(self.__arrTemp)

    def get_reg_value(self, k):
        if self.__arrTemp is None:
            self.fix_temp(self.temp, self.breakpoints)
        summa = 0
        for i in range(0, len(k)):
            A = k[i]
            B = self.__arrTemp[i]
            summa += A * B
        self.regression = summa
        return summa

    def fix_temp(self, t, breakpoints):
        # log.debug(
        #    'entered fix_temp with t={} and breakpoint = {}'.format(t, breakpoints))
        self.__arrTemp = []
        self.__arrTemp.append(1)
        # Set to -1000 to skip 'if res < prevP - p' the first time
        prevP = -1000
        for p in breakpoints[1:-1]:
            res = t - p
            if res < prevP - p:
                res = prevP - p
            if res < 0:
                self.__arrTemp.append(res)
            else:
                self.__arrTemp.append(0)
            prevP = p

        res = t - breakpoints[-2]
        if res > 0:
            self.__arrTemp.append(res)
        else:
            self.__arrTemp.append(0)
