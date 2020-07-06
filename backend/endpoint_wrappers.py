import requests
import logging
import os
import iso8601
from datetime import datetime
import asyncio
import aiohttp
from collections import defaultdict
# from functools import lru_cache

log = logging.getLogger(__name__)
API_TOKEN = os.getenv("API_TOKEN", None)


def _fix_datetime(meter_readings):
    for meter_reading in meter_readings:
        meter_reading['timestamp'] = iso8601.parse_date(
            meter_reading['timestamp'])
        if 'consumption' in meter_reading:
            meter_reading['consumption']['from'] = iso8601.parse_date(
                meter_reading['consumption']['from'])
            meter_reading['consumption']['to'] = iso8601.parse_date(
                meter_reading['consumption']['to'])


# @lru_cache(maxsize=32)
def get_meter_readings(metering_point_id, _from, to):
    """Returns meter_readings object

    You need to set the environment variable uri_meter_readings

    Args:
        metering_point_id (str) : the metering_point
        _from (datetime) : included from date
        to (datetime) : included to date

    Returns:
        metering_points (str) : in json format
    """

    uri_meter_readings = os.getenv(
        'METER_READINGS_HOST', 'http://localhost:8082')
    uri_meter_readings = '{}/validated'.format(uri_meter_readings)
    query_params = {
        'metering_point_id': metering_point_id,
        'include_from': _from,
        'include_to': to,
        'interval': 'daily',
        'limit': 9999999,
        'offset': 0,
        'property': 'energy,flow'
    }

    response = requests.get(uri_meter_readings, params=query_params, headers={
                            'Authorization': 'Token ' + API_TOKEN})
    response.raise_for_status()
    meter_readings = response.json()
    _fix_datetime(meter_readings)

    return meter_readings


# # @lru_cache(maxsize=32)
def get_metering_points(metering_point_id):
    """Returns metering_points object

    You need to set the environment variable uri_meteringpoint

    Args:
        metering_point_id (str) : metering_point_id

    Returns:
        dict = the result in form of a python obj

    """

    uri_meteringpoints = os.getenv(
        'METERING_POINTS_HOST', 'http://localhost:8083')
    uri_meteringpoints = '{}/{}'.format(
        uri_meteringpoints, metering_point_id)
    response = requests.get(uri_meteringpoints, headers={
                            'Authorization': 'Token ' + API_TOKEN})
    response.raise_for_status()

    return response.json()


# @lru_cache(maxsize=32)
def get_weather_readings(weather_station_id, weather_stations_agency, _from, to):
    """Will ask weather api about temperature values

    You need to set the environment variable uri_wather


    Args:
        weather_station_id (string) : weather_station_id
        timestamp (datetime) : the date

    Returns:
        dict - the result in form of a dict where the kwy is the timestamp
    """

    uri_weather = os.getenv(
        'WEATHER_HOST', 'http://localhost:8084')
    uri_weather = '{}/readings'.format(uri_weather)
    query = {
        'weather_station_id': weather_station_id,
        'weather_station_agency': weather_stations_agency,
        'include_from': _from,
        'include_to': to,
        'limit': 9999
    }

    response = requests.get(uri_weather, params=query, headers={
                            'Authorization': 'Token ' + API_TOKEN})
    response.raise_for_status()
    response_as_json = response.json()
    return_list = {}
    for r in response_as_json:
        r['timestamp'] = iso8601.parse_date(r['timestamp'])
        return_list[r['timestamp']] = r
    return return_list


async def request_meter_readings(session, metering_point_id, _from, to, response_data):
    uri_meter_readings = os.getenv(
        'METER_READINGS_HOST', 'http://localhost:8082')
    uri_meter_readings = '{}/validated'.format(uri_meter_readings)
    if isinstance(_from, datetime):
        _from = _from.strftime('%Y-%m-%dT%H:%M:%SZ')
    if isinstance(to, datetime):
        to = to.strftime('%Y-%m-%dT%H:%M:%SZ')

    query_params_meter_readings = {
        'metering_point_id': metering_point_id,
        'include_from': _from,
        'include_to': to,
        'interval': 'daily',
        'limit': '9999999',
        'offset': '0'
    }
    async with session.get(uri_meter_readings, params=query_params_meter_readings) as resp:
        response_data['meter_readings'] = await resp.json()
        _fix_datetime(response_data['meter_readings'])


async def request_weather(session, metering_point_id, _from, to, response_data):

    uri_meteringpoints = os.getenv(
        'METERING_POINTS_HOST', 'http://localhost:8083')
    uri_meteringpoints = '{}/{}'.format(
        uri_meteringpoints, metering_point_id)
    query_params_meteringpoints = {}

    metering_point = None
    async with session.get(uri_meteringpoints, params=query_params_meteringpoints) as resp:
        metering_point = await resp.json()
    weather_station_id = metering_point['weather_station_id']
    weather_station_agency = metering_point['weather_station_agency']
    response_data['metering_points'] = metering_point
    uri_weather = os.getenv(
        'WEATHER_HOST', 'http://localhost:9999')
    uri_weather = '{}/readings'.format(uri_weather)

    if isinstance(_from, datetime):
        _from = _from.strftime('%Y-%m-%dT%H:%M:%SZ')
    if isinstance(to, datetime):
        to = to.strftime('%Y-%m-%dT%H:%M:%SZ')

    query_params_weather = {
        'weather_station_id': weather_station_id,
        'weather_station_agency': weather_station_agency,
        'include_from': _from,
        'include_to': to,
        'limit': 9999
    }
    async with session.get(uri_weather, params=query_params_weather) as weather_resp:
        return_list = defaultdict()
        response_as_json = await weather_resp.json()
        for r in response_as_json:
            #r['timestamp'] = iso8601.parse_date(r['timestamp'])
            return_list[r['timestamp']] = r
        response_data['weather_readings'] = return_list


async def request_metering_point(session, metering_point_id, response_data):
    uri_meteringpoints = os.getenv(
        'METERING_POINTS_HOST', 'http://localhost:8083')
    uri_meteringpoints = '{}/{}'.format(
        uri_meteringpoints, metering_point_id)
    query_params_meteringpoints = {}

    async with session.get(uri_meteringpoints, params=query_params_meteringpoints) as resp:
        response_data['metering_points'] = await resp.json()


async def add_requestes(metering_point_id, _from, to, result_data):
    auth = {'Authorization': 'Token ' + API_TOKEN}
    async with aiohttp.ClientSession(headers=auth) as session:
        return await asyncio.gather(*[request_metering_point(session, metering_point_id, result_data), request_meter_readings(session, metering_point_id, _from, to, result_data)])


def get_data_async(metering_point_id, _from, to):
    """ This code will use asyncio and aiohttp to async external calls

    The awswers will be in a key/value list, where the answers are saved as keys:
     - weather_readings
     - metering_points
     - meter_readings

     Args:
        metering_point_id (string) : metering_point_id to search for
        _from (datetime) : datetime with utc information.
        to (datetime) : datetime with utc information

    Returns:
        dict['type_of_answer_as_key']
        """
    result_data = {}
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(add_requestes(
        metering_point_id, _from, to, result_data))
    return result_data
