# encoding: utf-8
#
# """"
################################################################
#
#  How to store Samsung Smartthings Data in a Google Spreadsheet
#
################################################################
__author__ = "Oliver Schlueter"
__copyright__ = "Copyright 2020"
__license__ = "GPL"
__version__ = "1.0.0"
__email__ = "oliver.schlueter@dell.com"
__status__ = "Production"

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import argparse
import sys
import json
import requests
import urllib3
import datetime

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
         "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

###########################################
#        VARIABLE
###########################################
DEBUG = True


###########################################
#    Methods
###########################################

def get_argument():
    global apiEndpoint, smartdeviceID, token, sheetName

    try:
        # Setup argument parser
        parser = argparse.ArgumentParser()
        parser.add_argument('-a', '--address',
                            type=str,
                            help='API Endpoint',
                            required=True)
        parser.add_argument('-d', '--deviceid',
                            type=str,
                            help='Device ID',
                            required=True)
        parser.add_argument('-t', '--token',
                            type=str,
                            help='SmartThings API Bearer Token',
                            required=True)
        parser.add_argument('-s', '--sheet',
                            type=str,
                            help='Google Sheet Name',
                            required=True)

        args = parser.parse_args()

    except KeyboardInterrupt:
        # handle keyboard interrupt #
        return 0

    apiEndpoint = args.address
    smartdeviceID = args.deviceid
    token = args.token
    sheetName = args.sheet


###########################################
#    Classes
###########################################
class ST2GSheet:
    # This class permit to connect to Samsung SmartThings

    def __init__(self):
        self.apiEndpoint = apiEndpoint
        self.deviceID = smartdeviceID
        self.token = token
        self.ST_all_Temp_Devices = []
        self.ST_results01 = []
        self.ST_results02 = []
        self.TempDevices = []
        self.valueSet = []

    def send_request_allTempDevices(self):
        # send a request and get the result as dict

        try:
            # try to get all temperature sensors
            url = apiEndpoint + "/v1/devices?capability=temperatureMeasurement"
            headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
            r = requests.get(url, verify=False, headers=headers)
            self.ST_all_Temp_Devices = json.loads(r.content)

        except Exception as err:
            print(timestamp + ": Not able to get temperature devices: " + str(err))
            exit(1)

    def send_request_deviceName(self, deviceID):
        # send a request and get the result as dict

        try:
            # try to get device name from device ID
            url = apiEndpoint + "/v1/devices/" + deviceID
            headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
            r = requests.get(url, verify=False, headers=headers)
            self.ST_results01 = json.loads(r.content)

        except Exception as err:
            print(timestamp + ": Not able to get device name: " + str(err))
            exit(1)

    def send_request_deviceStatus(self, deviceID):
        # send a request and get the result as dict

        try:
            # try to get device status and values
            url = apiEndpoint + "/v1/devices/" + deviceID + "/status"
            headers = {"Authorization": "Bearer " + token, "Accept": "application/json"}
            r = requests.get(url, verify=False, headers=headers)
            self.ST_results02 = json.loads(r.content)

        except Exception as err:
            print(timestamp + ": Not able to get device status: " + str(err))
            exit(1)

    def getAllTempDevices(self):
        self.send_request_allTempDevices()

        try:
            # get name and device value
            for TempDevice in self.ST_all_Temp_Devices['items']:
                self.TempDevices.append(TempDevice['deviceId'])

        except Exception as err:
            print(timestamp + ": Error while generating device list: " + str(err))
            exit(1)

    def getDeviceValues(self, deviceID):
        self.send_request_deviceStatus(deviceID)
        self.send_request_deviceName(deviceID)

        try:
            # get name and device value

            DeviceName = self.ST_results01['name']
            DeviceLabel = self.ST_results01['label']

            # get humidity value
            HumidityTimestamp = self.ST_results02['components']['main']['relativeHumidityMeasurement']['humidity'][
                'timestamp']
            Tempvalue = self.ST_results02['components']['main']['relativeHumidityMeasurement']['humidity']['value']

            # get temperature value
            TempTimestamp = self.ST_results02['components']['main']['temperatureMeasurement']['temperature'][
                'timestamp']
            TempValue = self.ST_results02['components']['main']['temperatureMeasurement']['temperature']['value']

            valueSet = [DeviceName, DeviceLabel, HumidityTimestamp, Tempvalue, TempTimestamp, TempValue]
            self.uploadVales(valueSet)

        except Exception as err:
            print(timestamp + ": Error while process device values: " + str(err))
            exit(1)

    def uploadVales(self, valueSet):
        # initiating upload into google sheet
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
            client = gspread.authorize(creds)
            sheet = client.open("PoolTemp").sheet1  # Open the spreadhseet
            sheet.insert_row(valueSet, 1)

        except Exception as err:
            print(timestamp + ": Error while uploading data into Google Sheet: " + str(err))
            exit(1)


def main():
    # get and test arguments
    get_argument()

    # store timestamp
    global timestamp
    timestamp = datetime.datetime.now().strftime("%d-%b-%Y (%H:%M:%S)")

    # display arguments if DEBUG enabled
    if DEBUG:
        print("API Endpoint: " + apiEndpoint)
        print("Smartdevice ID: " + smartdeviceID)
        print("SmartThings API Token: " + token)
        print("Google Sheet Name: " + sheetName)
    else:
        sys.tracebacklimit = 0

    myST2GSheet = ST2GSheet()

    if smartdeviceID == "all":
        myST2GSheet.getAllTempDevices()
        for deviceID in myST2GSheet.TempDevices:
            myST2GSheet.getDeviceValues(deviceID)
    else:
        myST2GSheet.getDeviceValues(smartdeviceID)


if __name__ == '__main__':
    main()
