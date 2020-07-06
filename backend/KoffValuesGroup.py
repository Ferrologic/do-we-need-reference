class KoffValuesGroup:
    
    def __init__(self):
        self.group = []
        
    def addRegValue(self, regvalues, group):
        self.group.append([group, regvalues])
    
    def getRegValues(self, g):
        return self.group[g]