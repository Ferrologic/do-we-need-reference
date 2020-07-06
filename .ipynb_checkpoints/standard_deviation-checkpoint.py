#kopierad klass från backend/standard_deviation, går ej att importera...
import pandas as pd
import logging
import copy
import math

log = logging.getLogger(__name__)


class StandardDeviation:

    def __init__(self, breakpoints=None):
        breakpoints = copy.deepcopy(breakpoints)
        if breakpoints != None:
            self._breakpoints = self.check_breakpoints(breakpoints)
        else:
            self._breakpoints = None
        self._dataframe = None
        self._dataframe_stdav = None

    def check_breakpoints(self, breakpoints):
        """We need to add max and min as -100 and 100 """
        if breakpoints[0] != -100:
            breakpoints[0] = -100
        if breakpoints[len(breakpoints)-1] != 100:
            breakpoints.append(100)
        return breakpoints

    def normalize_data(self, raw_data):
        """This will take the json values and flatten them.

        It can be done by som pandas functionality also

        Args:
            raw_data (Group) : The list with consumption_value and calculated_value

        Returns:
            None
            """
        norm_data_list = []
        for item in raw_data:
            norm_item = {}
            norm_item['consumption_value'] = item['consumption_value']
            norm_item['calculated_value'] = item['calculated_value']
            norm_item['temperature'] = item['temperature']
            norm_item['group'] = item['group']
            norm_item['property'] = item['property']
            norm_data_list.append(norm_item)
        self._dataframe = pd.DataFrame.from_dict(norm_data_list)

    def import_from_group(self, group):
        """Get values from Group class

        Since this is one group only, and there are no information about property, these values are 
        set to default values.

        Args:
            group (Group) : Group class 

        Returns: 
           None
        """
        norm_data_list = []
        for point in group.points:
            norm_item = {}
            norm_item['consumption_value'] = point.reading
            norm_item['calculated_value'] = point.regression
            norm_item['temperature'] = point.temp
            norm_item['group'] = 1
            norm_item['property'] = 'not-known'
            norm_data_list.append(norm_item)
        self._dataframe = pd.DataFrame.from_dict(norm_data_list)
        log.debug('import_from_group: first item is -> consumption={}, calculated={}, temp={}'.format(
            norm_data_list[0]['consumption_value'], norm_data_list[0]['calculated_value'], norm_data_list[0]['temperature']))

    def calc_standard_deviation(self, breakpoints=None):
        if breakpoints is None:
            breakpoints = self._breakpoints
        else:
            breakpoints = copy.deepcopy(breakpoints)
            breakpoints = self.check_breakpoints(breakpoints)
            self._breakpoints = breakpoints
        self._dataframe['consumption_norm'] = self._dataframe['consumption_value'] - \
            self._dataframe['calculated_value']
        self._dataframe['temp_intervall'] = pd.cut(
            self._dataframe['temperature'], breakpoints)
        self._dataframe_stdav = self._dataframe.groupby(['temp_intervall', 'group', 'property'])[
            'consumption_norm'].std().rename('stdav')
        return self._dataframe_stdav

    def export_data(self):
        std_list = {}
        for key, item in self._dataframe_stdav.iteritems():

            # Fills all intervall even if they are not in the dataframe
            for temp_interval in self._breakpoints:
                std_item = {}
                std_item['temp_interval'] = '{}'.format(temp_interval)
                std_item['group'] = key[1]
                std_item['property'] = key[2]
                std_item['stdav'] = -99999.0
                key_tuple = (
                    temp_interval, std_item['group'], std_item['property'])
                if key_tuple not in std_list.keys():
                    std_list[key_tuple] = std_item
            std_item = {}
            std_item['temp_interval'] = "{}->{}".format(
                key[0].left, key[0].right)
            std_item['group'] = key[1]
            std_item['property'] = key[2]
            if math.isnan(item):
                std_item['stdav'] = -99999.0
            else:
                std_item['stdav'] = item
            key_tuple = (key[0].left, key[1], key[2])
            std_list[key_tuple] = std_item
        return std_list

    def standard_deviation(self, raw_data, breakpoints):
        self.normalize_data(raw_data)
        self.calc_standard_deviation(breakpoints)
        return self.export_data()