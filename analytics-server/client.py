#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
client.py
websocket client for calculating analytics data

Receives logging data by listening to logging websockets. Processes user data into graphs and calculated analytics.
Sends requests for data with a UUID to the connected logging websocket.

Message structure: {user: uuid, t: Date.now(), type: message_type, exp: exp_type, payload: payload}

TESTING by setting up local server and broadcasting
websocat -t ws-l:127.0.0.1:8000 broadcast:mirror:


@author: dprydereid@gmail.com
"""



import analytics
import json
import os
import pandas as pd
import process
import rel
import response
import _thread
import time
from time import sleep
import traceback
import websocket

def on_message(ws, message):
    try:
        print(message)
        mes = json.loads(message)
        
        ## if the message is a logging message from the UI then process this new log
        ## No response sent from client
        if(mes["type"] == "log"):

            process.AddUserLog(mes)


        ## else if the message is a request to return the analytics for a specific user then do..
        ## user adjacency matrix as a dataframe is generated here and passed to analysis methods
        elif(mes["type"] == "request"):
            user = mes['user']
            exp = mes['exp']
            course = mes['course']
            payload = mes['payload']
            ##update this to reflect use of a single method to generate analytics
            A = process.GenerateAdjacencyMatrix(user, exp, course)

            ## if requesting a graph do something
            if(payload['content'] == 'student_graph'):
                res = response.StudentGraphResponse(user, exp, course)
                ws.send(json.dumps(res))
            elif(payload['content'] == 'comparison_graph'):
                res = response.ComparisonGraphResponse(payload['graph'], user, exp)
                ws.send(json.dumps(res))

            ## if requesting task identification do something
            elif(payload['content'] == 'task_identification'):
                res = response.TaskCompletionResponse(A, user, exp, course)
                ws.send(json.dumps(res))
            ##if requesting indicator (e.g. exploration) data do something
            elif(payload['content'] == 'indicators'):
                res = response.IndicatorResponse(A, user, exp, course)
                ws.send(json.dumps(res))

            elif(payload['content'] == 'centroids'):
                res = response.CentroidResponse(A, user, exp, course)
                ws.send(json.dumps(res))
            
            
        ## else if the message is feedback from the user, including tags on the dashboard
        elif(mes["type"] == "feedback"):
            print('logging feedback')
            process.AddUserFeedback(mes)

        else:
            print("log message not recognised")    
        
    except Exception as e:
        print(e)
        traceback.print_stack()

def connect(addresses):
    
    for address in addresses:
        print(address)
        ws = websocket.WebSocketApp(address, on_message=on_message, on_error=on_error, on_close=on_close)
        ws.run_forever(dispatcher=rel, reconnect=3) 
    rel.signal(2, rel.abort) 
    rel.dispatch()  
    
# >>> addr = "wss://api.gemini.com/v1/marketdata/%s"
# >>> for symbol in ["BTCUSD", "ETHUSD", "ETHBTC"]:
# ...     ws = websocket.WebSocketApp(addr % (symbol,), on_message=lambda w, m : print(m))
# ...     ws.run_forever(dispatcher=rel, reconnect=3)  
# >>> rel.signal(2, rel.abort)  # Keyboard Interrupt  
# >>> rel.dispatch()  

def on_error(ws, error):
    print(error)

def on_close(ws, close_status_code, close_msg):
    print(close_msg)
    print( "connection lost, exiting" )  


def on_open(ws):
    print('opened')
    def run(*args):
        for i in range(3):
            time.sleep(1)
            ws.send("Hello %d" % i)
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    _thread.start_new_thread(run, ())
    

if __name__ == "__main__":
    
    addresses = [
        "ws://localhost:8888/ws/spin30",
        "ws://localhost:8888/ws/spin31",
        "ws://localhost:8888/ws/spin32"
        ]
    connect(addresses)
