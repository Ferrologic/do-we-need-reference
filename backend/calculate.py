import logging

log = logging.getLogger(__name__)


def _coff_to_array(coff):
    """converts coff to array

    Args:
        coff: str

    Returns:
        an array of coff values

    """
    arr = []
    try:
        arr.append(coff['values']['c1'])
        arr.append(coff['values']['c2'])
        arr.append(coff['values']['c3'])
        arr.append(coff['values']['c4'])
        arr.append(coff['values']['c5'])

    except:
        log.error('error in _coff_to_array')
    finally:
        return arr


def _temp_to_array(temp):
    """converts temperture to an array

    The temp need to be splittet in parts, this as an part of the kasper math

    Example:
    |     | (1)| (2) | (9) | (15)|>(15)|
    |Temp | 1  |  2  |  3  |  4  |  5  |
    | 3   | 1  |  1  | -6  | -6  |  0  |
    | 10  | 1  |  0  |  0  | -5  |  0  |
    | 15  | 1  |  0  |  0  |  0  |  1  |

    Args:
        temp (float): the temp value

    Returns:
        an array where temp have been splittet up in an array

    """
    arr = []
    try:
        arr.append(1)
        res = temp - 2
        if (res < 0):
            arr.append(res)
        else:
            arr.append(0)

        res = temp-9
        if (res < (2-9)):
            res = 2-9
        if (res < 0):
            arr.append(res)
        else:
            arr.append(0)

        res = temp - 15
        if (res < (9-15)):
            res = 9-15
        if (res < 0):
            arr.append(res)
        else:
            arr.append(0)

        res = temp - 15
        if (res > 0):
            arr.append(res)
        else:
            arr.append(0)

    except:
        log.error('Error in _temp_to_array')
    finally:
        return arr


def _calculate_value(arr_coff, arr_temp):
    """calculate a energy/flow value based on coff

    This part is copied from the java version

    Args:
        arr_coff (array of numbers) : An array of coff values
        arr_temp (array of numbers) : An array of the temp splitted

    Returns:
        the calculated value as a number
    """
    try:
        sum = 0.0
        for c, t in zip(arr_coff, arr_temp):
            sum = sum + (c*t)
        return sum
    except Exception as e:
        log.error(e)


def calculate_consumption(coff, temperature_value):

    _arr_coff = _coff_to_array(coff)
    _arr_temp = _temp_to_array(float(temperature_value))
    _energy_calculated = _calculate_value(_arr_coff, _arr_temp)
    return _energy_calculated
