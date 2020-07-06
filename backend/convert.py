import logging
from backend.Point import Point
import iso8601
from datetime import datetime, timezone, timedelta
from swagger_server.models import Regression
from backend.Matrix import Matrix
from backend.Group import Group
from swagger_server.models.coefficients_values import CoefficientsValues
from swagger_server.models.coefficient import Coefficient
from swagger_server.models.meter_reading_w_regression import MeterReadingWRegression

log = logging.getLogger(__name__)


def convert_from_consumption_date_to_timestamp(_datetime):
    """Will convert from consumption.from to timestamp

    Arguments:
        _datetime (datetime) : the consumption.from value

    Returns:
        (datetime) : the day before
    """
    if isinstance(_datetime, str):
        dt = iso8601.parse_date(_datetime)
        tomorrow = dt + timedelta(days=1)
        return tomorrow.isoformat('T')
    return _datetime + timedelta(days=1)


def convert_from_timestamp_to_consumption_date(_datetime):
    """Will convert from timestamp to consumption.from

    Arguments:
        _datetime (datetime) : the timestamp

    Returns:
        (datetime) : the day after

    """
    if isinstance(_datetime, str):
        dt = iso8601.parse_date(_datetime)
        yesterday = dt - timedelta(days=1)
        return yesterday.isoformat('T')
    return _datetime - timedelta(days=1)


def fill_points_with_data(meter_readings, weather_readings, property_of_data, breakpoints):
    points = []
    for meter_reading in meter_readings:
        try:
            if meter_reading['property'] == property_of_data and meter_reading['status']:
                if {'key': 'calculate_consuming_values', 'val': 'calculate_consuming_values_ok'} not in meter_reading['status'] and \
                        {'key': 'calculate_consuming_values', 'val': 'pre-calculated'} not in meter_reading['status']:
                    continue
                if {'key': 'validate_simple_status', 'val': 'validate_simple_ok'} not in meter_reading['status']:
                    continue
                point = Point()
                if 'consumption' in meter_reading and ('status' not in meter_reading or
                                                       {'key': 'calculate_consuming_values',
                                                        'val': 'calculate_consuming_values_error'}
                                                       not in meter_reading['status']):
                    point.reading = meter_reading['consumption']['value']
                else:
                    point.reading = 0
                point.timestamp = meter_reading['timestamp']
                point.consumption_timestamp = meter_reading['consumption']['from']
                point.breakpoints = breakpoints
                point.temp = float(
                    weather_readings[meter_reading['timestamp']]['value'])
                points.append(point)
        except Exception:
            continue
    return points


def fill_points_with_data(meter_readings, property_of_data, breakpoints):
    """Fill points from meter_readings when temperature is includede in meter_reading

    Arguments:
        meter_readings {array} -- from meter_readings endpoint
        property_of_data {str} -- Flow or Energy
        breakpoints {array} -- Temperature breakpoints

    Returns:
        Array of Points -- Points is a class from the old java code
    """
    points = []
    for meter_reading in meter_readings:
        try:
            if meter_reading['property'] == property_of_data and meter_reading['status']:
                if {'key': 'calculate_consuming_values', 'val': 'calculate_consuming_values_ok'} not in meter_reading['status'] and \
                        {'key': 'calculate_consuming_values', 'val': 'pre-calculated'} not in meter_reading['status']:
                    continue
                if {'key': 'validate_simple_status', 'val': 'validate_simple_ok'} not in meter_reading['status']:
                    continue
                point = Point()
                if 'consumption' in meter_reading and ('status' not in meter_reading or
                                                       {'key': 'calculate_consuming_values',
                                                        'val': 'calculate_consuming_values_error'}
                                                       not in meter_reading['status']):
                    point.reading = meter_reading['consumption']['value']
                else:
                    point.reading = 0
                point.timestamp = meter_reading['timestamp']
                point.consumption_timestamp = meter_reading['consumption']['from']
                point.breakpoints = breakpoints
                point.temp = float(
                    meter_reading['calculated']['weather_data']['outdoor_temperature'])
                points.append(point)
        except Exception:
            continue
    return points


def fill_points_from_temperature(meter_readings, breakpoints):
    """Fill Points (class) with temperature """
    points = []
    for meter_reading in meter_readings:
        try:
            point = Point()
            point.reading = 0.0
            point.breakpoints = breakpoints
            point.temp = float(
                meter_reading['calculated']['weather_data']['outdoor_temperature'])
            point.timestamp = meter_reading['timestamp']
            point.consumption_timestamp = meter_reading['consumption']['from']
            points.append(point)
        except Exception:
            pass
    return points


""" def calc_regression_of_body(body, property_of_data, breakpoints, coff):
    for meter in body.meter_readings:
        if (meter._property == property_of_data):
            point = Point()
            point.reading = meter.consumption.value
            point.timestamp = meter.timestamp
            point.breakpoints = breakpoints
            for temp in body.temperatures_readings:
                if (point.timestamp == temp.timestamp):
                    point.temp = float(temp.value)
                    break
            regression = point.get_reg_value(coff)
            if hasattr(meter, 'calculated') == False:
                meter['calculated'] = {
                    'value': 0.0, 'normalized_value': 0.0, 'deviation_type': '', 'deviation_level': ''}
            meter.calculated.value = regression
    return body """


def _find_temp(weather_readings, timestamp):
    if timestamp in weather_readings:
        return weather_readings[timestamp]['value']
    else:
        return None


def _find_correct_coefficient(cofficient_list, _property, group=None, period=None):
    """Filter out the correct coefficients based on property, group and period


    Args:
        coefficient_list (list) : the coefficient_list from metering_point
        property (str): energy or flow
        group (str): group name
        period (str): period name

    Returns:
        A list of coefficients (list)
    """
    return_list = []
    for coefficient in cofficient_list:
        if coefficient['type_of_coefficient'] == _property:
            if group is None:
                return_list.append(coefficient)
                continue
            else:
                if period is None:
                    if group == coefficient['group']:
                        return_list.append(coefficient)
                        continue
                else:
                    if period == coefficient['period']:
                        return_list.append(coefficient)
    return return_list


def _find_coff(coff_list, _property, group, period):
    """ Find the right cofficient info based on group and period"""
    for c in coff_list:
        if c['period'] == period and c['group'] == group and c['type_of_coefficient'] == _property:
            return c
    log.debug('_find_coff: did not find the correct coefficient group, will choose the first')
    for c in coff_list:
        if c['type_of_coefficient'] == _property:
            return c
    raise Exception('_find_coff: no coefficient was found')


def _find_optimal_regression_value(point, coefficients, _property):
    """Will find the group/coefficient thats nearest reality

    This is a copy of the same method in validate

    Args:
        point (Point)): a meter_reading class 
        coefficients([coefficients]) : array of coefficients  

    Returns:
        regression_value (float): The regressionvalue with the smallest diff between regression and measured
        """
    correct_coefficients = _find_correct_coefficient(coefficients, _property)
    optimal_regression = None
    for coefficient in correct_coefficients:
        regression = point.get_reg_value(_convert_coff(coefficient))
        if optimal_regression is None:
            optimal_regression = regression
        if (abs(optimal_regression-point.reading)) > (abs(regression-point.reading)):
            optimal_regression = regression
    return optimal_regression


def _convert_coff(coff):
    ret = []
    ret.append(coff['values']['c1'])
    ret.append(coff['values']['c2'])
    ret.append(coff['values']['c3'])
    ret.append(coff['values']['c4'])
    ret.append(coff['values']['c5'])
    return ret


def convert_points_to_meter_readings(points, _property):
    """Convert from Point() to meter_readings"""
    meter_readings = []
    for point in points:
        meter_reading = {}
        meter_reading['timestamp'] = point.timestamp.replace(
            tzinfo=timezone.utc).isoformat('T').replace('+00:00', 'Z')
        meter_reading['property'] = _property
        meter_reading['consumption'] = {'from': point.consumption_timestamp.replace(
            tzinfo=timezone.utc).isoformat('T').replace('+00:00', 'Z'),
            'to': point.timestamp.replace(
                tzinfo=timezone.utc).isoformat('T').replace('+00:00', 'Z'),
            'value': point.reading}
        meter_reading['calculated'] = {
            'weather_data': {'outdoor_temperature': point.temp}}
        meter_readings.append(meter_reading)
    return meter_readings


def calc_regression_from_temp(meter_readings, breakpoints, coff_reference, coff_period=None):
    """Will calculate regressions based on cofficient 

    This function is group aware and will choose the right one if provided, or it will use the existing one

    Arguments:
        meter_readings (dict) : meter_readings 
        weather_readings (dict) : weather_readings
        group (int) : the group number, zero based
        breakpoints (dict) : the breakpoints used to split temperatures
        coff_reference (dict) : the cofficients from the reference period
        coff_period (dict) : the cofficients from the current period

    Returns:
        Regression (dict) : A regression list of Regression object
    """

    regressions = []
    existing_meter_readings = {}
    for meter_reading in meter_readings:
        try:
            temp = float(meter_reading['calculated']['weather_data']['outdoor_temperature'])
        except Exception as e:
            log.warning(f'Unable to get outdoor temperature from meter reading object. ({e}),'
                        f"(datetime: {meter_reading.get('timestamp', '[UNKNOWN]')}). Skipping...")
            continue
        point = Point()
        point.temp = float(temp)
        if 'consumption' in meter_reading and 'status' in meter_reading:
            if (
                ( ({'key': 'calculate_consuming_values', 'val': 'calculate_consuming_values_ok'} not in meter_reading['status']) and
                ({'key': 'calculate_consuming_values', 'val': 'pre-calculated'} not in meter_reading['status']) )
                or ({'key': 'validate_simple_status', 'val': 'validate_simple_ok'} not in meter_reading['status'])
            ):
                log.warning(f'Meter reading not (simple) validated.'
                            f"(datetime: {meter_reading.get('timestamp', '[UNKNOWN]')}). Skipping...")
                continue
            consumption_value = meter_reading['consumption']['value']
            point.reading = consumption_value
            point.breakpoints = breakpoints
            regression = Regression()
            if coff_period is not None:
                regression.calculated_period = _find_optimal_regression_value(
                    point, coff_period, meter_reading['property'])
            regression.calculated_reference = _find_optimal_regression_value(
                point, coff_reference, meter_reading['property'])
            regression.timestamp = meter_reading['consumption']['from']
            regression.consumption = consumption_value
            regression._property = meter_reading['property']
            regression.temperature = float(temp)
            regressions.append(regression)
            existing_meter_readings[meter_reading['timestamp']] = True
    return regressions


def calc_regression_from_temp_using_group(meter_readings, group, breakpoints, coefficient):
    """Will calculate regressions based on coefficient 

    This function is group aware and will choose the right one if provided, or it will use the existing one

    Arguments:
        meter_readings (dict) : meter_readings 
        group (int) : the group number, zero based
        breakpoints (dict) : the breakpoints used to split temperatures
        coff_reference (dict) : the cofficients from the reference period
        coff_period (dict) : the cofficients from the current period

    Returns:
        MeterReadingsWRegression (dict) : A regression list of MeterReadingsWRegression object
    """

    regressions = []

    for m in meter_readings:
        point = Point()
        if 'weather_data' in m['calculated']:
            point.temp = float(
                m['calculated']['weather_data']['outdoor_temperature'])
        else:
            continue
        if 'consumption' in m and ('status' not in m or
                                   {'key': 'calculate_consuming_values',
                                    'val': 'calculate_consuming_values_error'}
                                   not in m['status']):
            consumption_value = m['consumption']['value']
        else:
            consumption_value = 0
        point.reading = consumption_value
        point.breakpoints = breakpoints
        coff_4_property = _find_correct_coefficient(
            coefficient, m['property'], group)
        if len(coff_4_property) < 1:
            continue
        point.regression = point.get_reg_value(
            _convert_coff(coff_4_property[0]))
        regression = MeterReadingWRegression()
        regression._calculated_value = point.regression
        regression.timestamp = m['consumption']['from']
        regression.consumption = consumption_value
        regression._property = m['property']
        regression.temperature = float(point.temp)
        regressions.append(regression)
    return regressions


def calc_groups(meter_readings, breakpoints, max_groups, kvot_splittring, calc_times, tolerance, _property):
    """Split values into groups """

    points = fill_points_with_data(
        meter_readings, _property, breakpoints)

    # Create group
    group = Group()
    group.set_breakpoints(breakpoints)
    group.set_points(points)

    # Matrix
    matrix = Matrix(breakpoints)
    matrix.addGroup(group)
    matrix.split(max_groups, kvot_splittring)
    matrix.base(calc_times, tolerance)
    return matrix


def fill_group_for_return(org_groups: Matrix, _property, breakpoints, coff_reference, coff_period):
    """Calculate and creates a group used as return object

    The structure is {group-info , fixed: [], regressions: []}. 

    Args:
        groups (Matrix) : the matrix object filled with data
        _property (str) : What kind of data is it, energy, flow?
        breakpoints ([]): list of breakpoints
        coff_reference ([]): list of coefficients for the reference period
        coff_period([]): list of coefficients for the viewed period

    Returns:
        [obj] : an object build around how the return information should look
    """
    return_obj = {'view_groups': [], 'reference_groups': []}

    # Get referens values for temp as meter_readings
    meter_readings_ref = get_ref_metering_readings(_property)

    # Fill view_groups
    for group_id, group in enumerate(org_groups.groups):
        group_meter_readings = convert_points_to_meter_readings(
            group.points, _property)
        regressions = calc_regression_from_temp_using_group(
            group_meter_readings, group_id, breakpoints, coff_period)

        referens_values = calc_regression_from_temp_using_group(
            meter_readings_ref, group_id, breakpoints, coff_period)

        # Add group object to response
        return_group = {}
        return_group['group_id'] = str(group_id+1)
        return_group['property'] = _property
        return_group['regressions'] = regressions
        return_group['fixed'] = referens_values
        return_obj['view_groups'].append(return_group)

    # Fill reference_groups
    coefficient_groups = _find_correct_coefficient(coff_reference, _property)

    # We need all points together in order to use their temperature
    points = []
    for group in org_groups.groups:
        for point in group.points:
            points.append(point)
    # points = fill_points_from_temperature(
    #    meter_readings_ref, breakpoints)
    log.debug('We have {} number of points, and the first one looks like this {}'.format(
        len(points), points[0]))
    for coefficient_id, coefficient_group in enumerate(coefficient_groups):
        referens_values = calc_regression_from_temp_using_group(
            meter_readings_ref, coefficient_id, breakpoints, [coefficient_group])
        group_meter_readings = convert_points_to_meter_readings(
            points, _property)
        regressions = calc_regression_from_temp_using_group(
            group_meter_readings, coefficient_id, breakpoints, [coefficient_group])
        return_group = {}
        return_group['group_id'] = str(coefficient_id+1)
        return_group['property'] = _property
        return_group['fixed'] = referens_values
        return_group['regressions'] = regressions
        return_obj['reference_groups'].append(return_group)
    return return_obj


def get_ref_metering_readings(_property):
    moc = [
        {
            "calculated": {
                "deviation_level": "",
                "deviation_type": "",
                "normalized_value": 0,
                "value": 1.0,
                "weather_data": {
                    "outdoor_temperature": -5
                }
            },
            "consumption": {
                "from": "2018-01-01T00:00:00Z",
                "to": "2018-01-02T00:00:00Z",
                "value": 1.0
            },
            "metering_point_id": "DEMO234",
            "property": _property,
            "reading_status": "measured",
            "status": [
                {
                    "key": "calulate_consuming_values",
                    "val": "calculate_consuming_values_ok"
                },
                {
                    "key": "validate_simple_status",
                    "val": "validate_simple_ok"
                },
                {
                    "key": "validate_advanced_status",
                    "val": "validate_advanced_ok"
                }
            ],
            "timestamp": "2018-01-02T00:00:00Z",
            "unit_of_measure": "MWh",
            "value": 1.0
        },
        {
            "calculated": {
                "deviation_level": "",
                "deviation_type": "",
                "normalized_value": 0,
                "value": 1.0,
                "weather_data": {
                    "outdoor_temperature": 2
                }
            },
            "consumption": {
                "from": "2018-01-02T00:00:00Z",
                "to": "2018-01-03T00:00:00Z",
                "value": 1.0
            },
            "metering_point_id": "DEMO234",
            "property": _property,
            "reading_status": "measured",
            "status": [
                {
                    "key": "calulate_consuming_values",
                    "val": "calculate_consuming_values_ok"
                },
                {
                    "key": "validate_simple_status",
                    "val": "validate_simple_ok"
                },
                {
                    "key": "validate_advanced_status",
                    "val": "validate_advanced_ok"
                }
            ],
            "timestamp": "2018-01-03T00:00:00Z",
            "unit_of_measure": "MWh",
            "value": 1.0
        },
        {
            "calculated": {
                "deviation_level": "",
                "deviation_type": "",
                "normalized_value": 0,
                "value": 1.0,
                "weather_data": {
                    "outdoor_temperature": 9
                }
            },
            "consumption": {
                "from": "2018-01-03T00:00:00Z",
                "to": "2018-01-04T00:00:00Z",
                "value": 1.0
            },
            "metering_point_id": "DEMO234",
            "property": _property,
            "reading_status": "measured",
            "status": [
                {
                    "key": "calulate_consuming_values",
                    "val": "calculate_consuming_values_ok"
                },
                {
                    "key": "validate_simple_status",
                    "val": "validate_simple_ok"
                },
                {
                    "key": "validate_advanced_status",
                    "val": "validate_advanced_ok"
                }
            ],
            "timestamp": "2018-01-04T00:00:00Z",
            "unit_of_measure": "MWh",
            "value": 1.0
        },
        {
            "calculated": {
                "deviation_level": "",
                "deviation_type": "",
                "normalized_value": 0,
                "value": 1.0,
                "weather_data": {
                    "outdoor_temperature": 15
                }
            },
            "consumption": {
                "from": "2018-01-04T00:00:00Z",
                "to": "2018-01-05T00:00:00Z",
                "value": 1.0
            },
            "metering_point_id": "DEMO234",
            "property": _property,
            "reading_status": "measured",
            "status": [
                {
                    "key": "calulate_consuming_values",
                    "val": "calculate_consuming_values_ok"
                },
                {
                    "key": "validate_simple_status",
                    "val": "validate_simple_ok"
                },
                {
                    "key": "validate_advanced_status",
                    "val": "validate_advanced_ok"
                }
            ],
            "timestamp": "2018-01-05T00:00:00Z",
            "unit_of_measure": "MWh",
            "value": 1.0
        },
        {
            "calculated": {
                "deviation_level": "",
                "deviation_type": "",
                "normalized_value": 0,
                "value": 1.0,
                "weather_data": {
                    "outdoor_temperature": 20
                }
            },
            "consumption": {
                "from": "2018-01-05T00:00:00Z",
                "to": "2018-01-06T00:00:00Z",
                "value": 1.0
            },
            "metering_point_id": "DEMO234",
            "property": _property,
            "reading_status": "measured",
            "status": [
                {
                    "key": "calulate_consuming_values",
                    "val": "calculate_consuming_values_ok"
                },
                {
                    "key": "validate_simple_status",
                    "val": "validate_simple_ok"
                },
                {
                    "key": "validate_advanced_status",
                    "val": "validate_advanced_ok"
                }
            ],
            "timestamp": "2018-01-06T00:00:00Z",
            "unit_of_measure": "MWh",
            "value": 1.0
        }
    ]
    return moc


def get_ref_weather_readings():
    moc = {
        '2018-01-02T00:00:00Z':
        {
            "property": "outdoor_temperature",
            "timestamp": "2018-01-02T00:00:00Z",
            "unit_of_measure": "C",
            "value": "-5.0",
            "weather_station_agency": "local",
            "weather_station_id": "1"
        }, '2018-01-03T00:00:00Z':
        {
            "property": "outdoor_temperature",
            "timestamp": "2018-01-03T00:00:00Z",
            "unit_of_measure": "C",
            "value": "2.0",
            "weather_station_agency": "local",
            "weather_station_id": "1"
        }, '2018-01-04T00:00:00Z':
        {
            "property": "outdoor_temperature",
            "timestamp": "2018-01-04T00:00:00Z",
            "unit_of_measure": "C",
            "value": "9.0",
            "weather_station_agency": "local",
            "weather_station_id": "1"
        }, '2018-01-05T00:00:00Z':
        {
            "property": "outdoor_temperature",
            "timestamp": "2018-01-05T00:00:00Z",
            "unit_of_measure": "C",
            "value": "15.000",
            "weather_station_agency": "local",
            "weather_station_id": "1"
        }, '2018-01-06T00:00:00Z':
        {
            "property": "outdoor_temperature",
            "timestamp": "2018-01-06T00:00:00Z",
            "unit_of_measure": "C",
            "value": "20",
            "weather_station_agency": "local",
            "weather_station_id": "1"
        }
    }
    return moc
