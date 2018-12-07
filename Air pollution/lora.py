import requests
import pymongo
from pymongo import MongoClient
from flask import Flask, jsonify, request
from datetime import datetime
from datetime import timedelta
import uuid, json
import dateutil.parser as parser
import hashlib

MONGO_HOST = "mongodb://root:root@ds117848.mlab.com:17848/nodelogin"
MONGO_PORT = 23456
MONGO_DB = "nodelogin"
MONGO_USER = "root"
MONGO_PASS = "root"
connection = MongoClient(MONGO_HOST, MONGO_PORT)
mongo = connection[MONGO_DB]
currTime = datetime.today() + timedelta(hours=3)
token = ''

class DatabaseManager:
    def getToken(self):
        url = "http://130.240.134.128:9000/oauth2/token"
        payload = "grant_type=password&username=user01ssr%40ssr.se&password=password&client_id=8f2e5c99050b48348a5badfe68b55a67&client_secret=48f18ebe9120476a8e852f157dcf9ff5"
        headers = {
            'Authorization': "Basic OGYyZTVjOTkwNTBiNDgzNDhhNWJhZGZlNjhiNTVhNjc6NDhmMThlYmU5MTIwNDc2YThlODUyZjE1N2RjZjlmZjU=",
            'Content-Type': "application/x-www-form-urlencoded",
            'cache-control': "no-cache",
            'Postman-Token': "129ea1c9-ba6c-489f-b696-f5e3487d3b9e"
        }
        response = requests.request("POST", url, data=payload, headers=headers)
        data = response.json()
        global token
        token = data['access_token']
        print(token)
        return jsonify({"status":"success","token":data['access_token']})

    def getData(self):
        url = "https://130.240.134.128:3000/v1/queryContext"
        
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": token
        }
        #sensorInfo = {}
        sensor = mongo.entities
        sensorArr = []
        for q in sensor.find({}):
            print(q['name'])
            sensorInfo = {}
            sensorInfo['id'] = q['name']
            sensorInfo['type'] = 'LORA_Sensor'
            sensorInfo['isPattern'] = 'false'
            sensorArr.append(sensorInfo)
        mapData = {}
        mapData['entities'] = sensorArr
        data = json.dumps(mapData)
        currTime = datetime.today()
        print(mapData) 
        try:
            response = requests.post(url,data=data, headers=headers, verify=False)
           # response = requests.request("POST", url, data=jsonify(payload), headers=headers, verify=False)
        except Exception as e:
            print(e)
            return e
        responseData = response.json()
        print(responseData)
        connect = mongo.lora
        contextResp = (responseData['contextResponses'])
        mapForMongo = {}
        for element in contextResp:
            eachAttr = element['contextElement']
            idData = eachAttr['id']
            attr = eachAttr['attributes']
            localMap = {}
            for individualAttr in attr:
                name = individualAttr['name']
                value = individualAttr['value']
                localMap[name] = value
            localMap['recvTime'] = currTime
            if idData == '0004a30b00220604':
                localMap['LAT'] = '64.745692'
                localMap['LON'] = '20.958829'
            elif idData == '0004a30b00226cd6':
                localMap['LAT'] = '64.750784'
                localMap['LON'] = '20.960339'
            localMap['sensorId'] = idData
            connect.insert(localMap)
            #mapForMongo[idData] = localMap
        return jsonify({"status":"success"})

    def showData(self,time,sensor):
        connect = mongo.lora
        query = {}
        dateCheckEnd = parser.parse(time)
        print(dateCheckEnd)
        dateCheckStart = dateCheckEnd - timedelta(hours=10)
        print(sensor)
        if sensor != "all":
            query['sensorId'] = sensor
        query['recvTime'] = {"$gte": dateCheckStart, "$lte":dateCheckEnd}
        respMap = {}
        print(query)
        for q in connect.find(query):
            mapToRespond = {}
            mapToRespond['nitro'] = q['NO2']
            mapToRespond['pm1'] = q['PM1']
            mapToRespond['pm10'] = q['PM10']
            mapToRespond['pm25'] = q['PM25']
            mapToRespond['lat'] = q['LAT']
            mapToRespond['time'] = q['Timestamp']
            mapToRespond['lon'] = q['LON']
            mapToRespond['dateTime'] = q['recvTime']
            ts = str(q['_id'])
            respMap[ts] = mapToRespond
        return jsonify({"status":"success","data":respMap})

    def getEntities(self):
        connect = mongo.entities
        query = {}
        mapResp = []
        for q in connect.find(query):
            mapResp.append(q['name'])
        return jsonify({"status":"success",'data':mapResp})
