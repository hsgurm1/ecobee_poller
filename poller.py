#!/bin/python3.6
from influxdb import InfluxDBClient
import datetime
import requests
import json
import sys
from pathlib import Path
import logging
import logging.handlers
import os

#setup logging
log_file_path = os.environ['filepath']
days_of_logs_to_keep = 7
# set to DEBUG, INFO, ERROR, etc
logging_level = 'DEBUG'
#ecobee API Key
APIKey = os.environ['APIValue']
#influxDB info
influxdb_server = os.environ['influxdb_server_value']
influxdb_port = os.environ['influxdb_port_value']
influxdb_database = os.environ['influxdb_database_value']
#runtime report time since last report query
runtime_difference = 60
tnow = datetime.datetime.now()

#setup logger
logger = logging.getLogger('ecobee')
logger.setLevel(getattr(logging, logging_level))
handler = logging.handlers.TimedRotatingFileHandler(log_file_path, when="d", interval=1,  backupCount=days_of_logs_to_keep)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def to_bool(value):
    valid = {'true': True, 't': True, '1': True,
             'false': False, 'f': False, '0': False,
             }

    if isinstance(value, bool):
        return value

    lower_value = value.lower()
    if lower_value in valid:
        return valid[lower_value]
    else:
        raise ValueError('invalid literal for boolean: "%s"' % value)


def api_request(url, method, header=''):
    try:
        if method == 'post':
            #post to url
            return requests.post(url).json()
        if method == 'get':
            #get method
            return requests.get(url, headers=headers).json()
    except:
        logger.critical("error connecting to " + url)
        sys.exit()

token_file = str(Path.home()) + '/.ecobee_token'
with open(token_file) as f:
    refreshToken = f.readline().replace("\n","")

token_url = "https://api.ecobee.com/token?grant_type=refresh_token&code=" + refreshToken + "&client_id=" + APIKey
r = api_request(token_url, 'post')

access_token = r['access_token']
new_refresh_token = r['refresh_token']

with open(token_file, 'w') as f:
    f.write(new_refresh_token)

logger.debug("Initiated Ecobee poller at " + str(tnow))


def logPoint(sensorName=None, thermostatName=None, sensorValue=None, sensorType=None):
    return {
        "measurement": sensorType,
        "tags": {
            "thermostat_name": thermostatName,
            "sensor": sensorName
        },
        "fields": {
            "value": sensorValue
        }
    }

def logPoint_hvac(sensorName=None, thermostatName=None, sensorValue=None, sensorType=None, hvactype=None):
    return {
        "measurement": sensorType,
        "tags": {
            "thermostat_name": thermostatName,
            "sensor": sensorName,
            "working": hvactype
        },
        "fields": {
            "value": sensorValue
        }
    }

client = InfluxDBClient(host=influxdb_server,
                        port=influxdb_port,
                        database=influxdb_database,
                        verify_ssl=False)


points = []

payload = {
    "selection": {
        "selectionType": "registered",
        "selectionMatch": "",
        "includeRuntime": True,
        "includeEquipmentStatus": True,
        "includeWeather": True,
        "includeSensors": True,
        "includeExtendedRuntime": True,
        "includeDevice": True,
        "includeEvents": True,
        "includeProgram": True
    }
}

payload = json.dumps(payload)

url = 'https://api.ecobee.com/1/thermostat?format=json&body=' + payload
headers = {'content-type': 'text/json', 'Authorization': 'Bearer ' + access_token}
response = api_request(url, 'get', headers)

point_count = 0

for thermostat in response['thermostatList']:
    thermostatName = thermostat['name']
    sensors = thermostat['remoteSensors']
    current_weather = thermostat['weather']['forecasts'][0]
    current_program = thermostat['program']['currentClimateRef']
    if len(thermostat['events']) > 0:
        current_program = thermostat['events'][0]['name']
    hvacstatus_name = thermostat['equipmentStatus']
    if len(thermostat['equipmentStatus']) == 0:
        hvacstatus_name = "off"
    else:
        hvacstatus_name = thermostat['equipmentStatus']

    hvacstatus_code = thermostat['equipmentStatus']
    if len(thermostat['equipmentStatus']) == 0:
        hvacstatus_code = int(0)
    else:
        hvacstatus_code = int(1)


    for sensor in sensors:
        for capability in sensor['capability']:
            if capability['type'] == 'occupancy':
                value = bool(to_bool(capability['value']))
                points.append(logPoint(sensorName=sensor['name'], thermostatName=str(thermostatName), sensorValue=bool(value), sensorType="occupancy"))
            if capability['type'] == 'temperature':
                if str.isdigit(capability['value']) > 0:
                    temp = int(capability['value']) / 10
                else:
                    temp = 0
                points.append(logPoint(sensorName=sensor['name'], thermostatName=str(thermostatName), sensorValue=float(temp), sensorType="temp"))
            if capability['type'] == 'humidity':
                points.append(logPoint(sensorName=sensor['name'], thermostatName=str(thermostatName), sensorValue=float(capability['value']), sensorType="humidity"))


    runtime = thermostat['runtime']
    temp = int(runtime['actualTemperature']) / 10
    heatTemp = int(runtime['desiredHeat']) / 10
    coolTemp = int(runtime['desiredCool']) / 10
    outside_temp = current_weather['temperature'] / 10
    outside_wind = current_weather['windSpeed']
    outside_humidity = current_weather['relativeHumidity']
    points.append(logPoint(sensorName=thermostatName, thermostatName=str(thermostatName), sensorValue=float(temp), sensorType="actualTemperature"))
    points.append(logPoint(sensorName=thermostatName, thermostatName=str(thermostatName), sensorValue=float(runtime['actualHumidity']), sensorType="actualHumidity"))
    points.append(logPoint(sensorName=thermostatName, thermostatName=str(thermostatName), sensorValue=float(heatTemp), sensorType="insideHeat"))
    points.append(logPoint(sensorName=thermostatName, thermostatName=str(thermostatName), sensorValue=float(coolTemp), sensorType="insideCool"))
    points.append(logPoint(sensorName=thermostatName, thermostatName=str(thermostatName), sensorValue=float(outside_temp), sensorType="outsideTemp"))
    points.append(logPoint(sensorName=thermostatName, thermostatName=str(thermostatName), sensorValue=float(outside_wind), sensorType="outsideWind"))
    points.append(logPoint(sensorName=thermostatName, thermostatName=str(thermostatName), sensorValue=float(outside_humidity), sensorType="outsideHumidity"))
    points.append(logPoint(sensorName=thermostatName, thermostatName=str(thermostatName), sensorValue=str(current_program), sensorType="currentProgram"))
    points.append(logPoint_hvac(sensorName=thermostatName, thermostatName=str(thermostatName), hvactype=str(hvacstatus_name), sensorValue=float(hvacstatus_code), sensorType="hvacstatus"))

    point_count += 1

client.write_points(points)

logger.debug("sensor readings written: " + str(point_count))
logger.debug("-----------------------------------")
