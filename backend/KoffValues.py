import numpy as np


class KoffValues:
    
    def __init__(self, breakPoints, koff = np.array([])):
        if not koff.size:
            koff = [0]*len(breakPoints)
        self.arrKoff = koff
        self.prGroup = 0
        self.prPeriod = 0
        
    def getKoff(self):
        return self.arrKoff
        
    def setPeriod(self, p):
        self.prPeriod = p
        
    def setIncompleteKoff(self, koff, missing):
        tmp = []
        j = 0
        for i in range(0, len(self.arrKoff)):
            if i in missing:
                tmp.append(0)
            else:
                tmp.append(koff[j])
                j += 1
        return tmp
