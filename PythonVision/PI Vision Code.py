#!/usr/bin/env python3
#----------------------------------------------------------------------------
# Copyright (c) 2018 FIRST. All Rights Reserved.
# Open Source Software - may be modified and shared by FRC teams. The code
# must be accompanied by the FIRST BSD license file in the root directory of
# the project.
#----------------------------------------------------------------------------

import json
import time
import sys

from cscore import CameraServer, VideoSource, UsbCamera, MjpegServer
from networktables import NetworkTablesInstance
from networktables import NetworkTables
import ntcore
import math
#   JSON format:
#   {
#       "team": <team number>,
#       "ntmode": <"client" or "server", "client" if unspecified>
#       "cameras": [
#           {
#               "name": <camera name>
#               "path": <path, e.g. "/dev/video0">
#               "pixel format": <"MJPEG", "YUYV", etc>   // optional
#               "width": <video mode width>              // optional
#               "height": <video mode height>            // optional
#               "fps": <video mode fps>                  // optional
#               "brightness": <percentage brightness>    // optional
#               "white balance": <"auto", "hold", value> // optional
#               "exposure": <"auto", "hold", value>      // optional
#               "properties": [                          // optional
#                   {
#                       "name": <property name>
#                       "value": <property value>
#                   }
#               ],
#               "stream": {                              // optional
#                   "properties": [
#                       {
#                           "name": <stream property name>
#                           "value": <stream property value>
#                       }
#                   ]
#               }
#           }
#       ]
#       "switched cameras": [
#           {
#               "name": <virtual camera name>
#               "key": <network table key used for selection>
#               // if NT value is a string, it's treated as a name
#               // if NT value is a double, it's treated as an integer index
#           }
#       ]
#   }

configFile = "/boot/frc.json"

class CameraConfig: pass

team = None
server = False
cameraConfigs = []
switchedCameraConfigs = []
cameras = []

def parseError(str):
    """Report parse error."""
    print("config error in '" + configFile + "': " + str, file=sys.stderr)

def readCameraConfig(config):
    """Read single camera configuration."""
    cam = CameraConfig()

    # name
    try:
        cam.name = config["name"]
    except KeyError:
        parseError("could not read camera name")
        return False

    # path
    try:
        cam.path = config["path"]
    except KeyError:
        parseError("camera '{}': could not read path".format(cam.name))
        return False

    # stream properties
    cam.streamConfig = config.get("stream")

    cam.config = config

    cameraConfigs.append(cam)
    return True

def readSwitchedCameraConfig(config):
    """Read single switched camera configuration."""
    cam = CameraConfig()

    # name
    try:
        cam.name = config["name"]
    except KeyError:
        parseError("could not read switched camera name")
        return False

    # path
    try:
        cam.key = config["key"]
    except KeyError:
        parseError("switched camera '{}': could not read key".format(cam.name))
        return False

    switchedCameraConfigs.append(cam)
    return True

def readConfig():
    """Read configuration file."""
    global team
    global server

    # parse file
    try:
        with open(configFile, "rt", encoding="utf-8") as f:
            j = json.load(f)
    except OSError as err:
        print("could not open '{}': {}".format(configFile, err), file=sys.stderr)
        return False

    # top level must be an object
    if not isinstance(j, dict):
        parseError("must be JSON object")
        return False

    # team number
    try:
        team = j["team"]
    except KeyError:
        parseError("could not read team number")
        return False

    # ntmode (optional)
    if "ntmode" in j:
        str = j["ntmode"]
        if str.lower() == "client":
            server = False
        elif str.lower() == "server":
            server = True
        else:
            parseError("could not understand ntmode value '{}'".format(str))

    # cameras
    try:
        cameras = j["cameras"]
    except KeyError:
        parseError("could not read cameras")
        return False
    for camera in cameras:
        if not readCameraConfig(camera):
            return False

    # switched cameras
    if "switched cameras" in j:
        for camera in j["switched cameras"]:
            if not readSwitchedCameraConfig(camera):
                return False

    return True

def startCamera(config):
    """Start running the camera."""
    print("Starting camera '{}' on {}".format(config.name, config.path))
    inst = CameraServer.getInstance()
    camera = UsbCamera(config.name, config.path)
    server = inst.startAutomaticCapture(camera=camera, return_server=True)
    camera.setConfigJson(json.dumps(config.config))
    camera.setConnectionStrategy(VideoSource.ConnectionStrategy.kKeepOpen)

    if config.streamConfig is not None:
        server.setConfigJson(json.dumps(config.streamConfig))

    return camera

def startSwitchedCamera(config):
    """Start running the switched camera."""
    print("Starting switched camera '{}' on {}".format(config.name, config.key))
    server = CameraServer.getInstance().addSwitchedCamera(config.name)

    def listener(fromobj, key, value, isNew):
        if isinstance(value, float):
            i = int(value)
            if i >= 0 and i < len(cameras):
              server.setSource(cameras[i])
        elif isinstance(value, str):
            for i in range(len(cameraConfigs)):
                if value == cameraConfigs[i].name:
                    server.setSource(cameras[i])
                    break

    NetworkTablesInstance.getDefault().getEntry(config.key).addListener(
        listener,
        ntcore.constants.NT_NOTIFY_IMMEDIATE |
        ntcore.constants.NT_NOTIFY_NEW |
        ntcore.constants.NT_NOTIFY_UPDATE)

    return server

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        configFile = sys.argv[1]
    
    # read configuration
    if not readConfig():
        sys.exit(1)

    # start NetworkTables
    ntinst = NetworkTablesInstance.getDefault()
    if server:
        print("Setting up NetworkTables server")
        ntinst.startServer()
    else:
        print("Setting up NetworkTables client for team {}".format(team))
        ntinst.startClientTeam(team)

    # start cameras
    #for config in cameraConfigs:
    #    cameras.append(startCamera(config))

    # start switched cameras
    #for config in switchedCameraConfigs:
    #    startSwitchedCamera(config)

    # loop forever
    from cscore import CameraServer

    # Import OpenCV and NumPy
    import cv2
    import numpy as np
    cs = CameraServer.getInstance()
    cs.enableLogging()

    # Capture from the first USB Camera on the system
    camera = cs.startAutomaticCapture()
    amt = 2
    camera.setResolution(160*amt, 120*amt)

    # Get a CvSink. This will capture images from the camera
    cvSink = cs.getVideo()

    # (optional) Setup a CvSource. This will send images back to the Dashboard
    outputStream = cs.putVideo("Name", 160*amt, 120*amt)

    # Allocating new images is very expensive, always try to preallocate
    img = np.zeros(shape=(120*amt, 160*amt, 3), dtype=np.uint8)
    table = NetworkTables.getTable("SmartDashboard")
    table.putNumber("lower-h", 77)
    table.putNumber("upper-h", 85)
    table.putNumber("lower-s", 110)
    table.putNumber("upper-s", 255)
    table.putNumber("lower-v", 100)
    table.putNumber("upper-v", 250)
    while True:
        # Tell the CvSink to grab a frame from the camera and put it
        # in the source image.  If there is an error notify the output.
        time, img = cvSink.grabFrame(img)
        if time == 0:
            # Send the output the error.
            outputStream.notifyError(cvSink.getError());
            # skip the rest of the current iteration
            continue

        #
        # Insert your image processing logic here!
        #
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower = np.array([table.getNumber("lower-h",0),table.getNumber("lower-s",0),table.getNumber("lower-v",0)])
        upper = np.array([table.getNumber("upper-h",255),table.getNumber("upper-s",255),table.getNumber("upper-v",255)])
        #upper = np.array([90,255,255])
        # Threshold the HSV image to get only blue colors
        mask = cv2.inRange(hsv, lower, upper)
        totX = 0
        totY = 0
        amt = 0
        minX = hsv.shape[1]
        minXY = 0
        maxX = 0
        maxXY = 0
        minY = hsv.shape[0]
        maxY = 0
        for y in range(len(mask)):
            for x in range(len(mask[y])):
                if(mask[y][x]):
                    totX += x
                    totY += y
                    amt += 1
                    if(x < minX):
                        minX = x
                        minXY = y
                    if(x > maxX):
                        maxX = x
                        maxXY = y
                    if(y > maxY):
                        maxY = y
                    if(y < minY):
                        minY = y
                        
                    '''
                    if(x < minX):
                        try:
                            if(mask[y][x+1] == 255):
                                minX = x
                                minXY = [y]
                        except:
                            pass
                    elif(x == minX):
                        minXY.append(y)
                    if(x > maxX):
                        try:
                            if(mask[y][x-1] == 255):
                                maxX = x
                                maxXY = [y]
                        except:
                            pass
                    elif(x == maxX):
                        maxXY.append(y)
                        
                    if(y < minY):
                        try:
                            if(mask[y+1][x] == 255):
                                minY = y
                                minYX = [x]
                        except:
                            pass
                    elif(y == minY):
                        minYX.append(x)
                    if(y > maxY):
                        try:
                            if(mask[y-1][x] == 255):
                                maxY = y
                                maxYX = [x]
                        except:
                            pass
                    elif(y == maxY):
                        maxYX.append(x)
                    '''
        if(amt > 0): #  and len(maxYX) > 0 and len(maxXY) > 0 and len(minYX) > 0 and len(maxYX) > 0
            mask[int(totY/amt)][int(totX/amt)] = 0
            table.putNumber("tape-x", totX/amt)
            table.putNumber("tape-y", totY/amt)
            amt1 = 0
            avgX = int(totX/amt)
            avgY = int(totY/amt)
            
            A = minXY-maxXY
            B = maxX-minX
            C = -minXY*maxX+minX*maxXY-minXY*maxX+maxX*minXY
            denom = math.sqrt(A**2+B**2)
            leftRightDist = math.sqrt((minX-maxX)**2+(minXY-maxXY)**2)
            maxD = 0.4325*leftRightDist
            minD = 0.3816*leftRightDist
            #print(maxD, minD)
            bottomSeen = False
            bottomLeftX = 0
            bottomLeftY = 0
            bottomRightX = 0
            bottomRightY = 0
            topSeen = False
            topLeftX = 0
            topLeftY = 0
            topRightX = 0
            topRightY = 0
            for x in range(minX, maxX+1): #len(mask.shape[1])):
                maskAmtBottom = 0
                maskAmtTop = 0
                lastSeenYBot = 0
                lastSeenYTop = 0
                for y in range(minY, maxY+1):
                    if(mask[y][x]):
                        # y = (y2-y1)/(x2-x1)*(x-x1)+y1
                        # (y-y1)*(x2-x1)=(y2-y1)*(x-x1)
                        # y*x2-y1*x2+x1*y1-x1*y=y2*x-y1*x+y1*x2-x1*y2
                        # y*(x2-x1) x*(-y2+y1)  -y1*x2+x1*y2-y1*x2+x2*y1=0
                        d = (A*x+B*y+C)/denom
                        #mask[y][x] = int(d*255/30.0)
                        if(d >= minD and d <= maxD):
                            mask[y][x] = 0
                            maskAmtBottom += 1
                            if(maskAmtBottom > 3 and not bottomSeen):
                                bottomSeen = True
                                bottomLeftX = x
                                bottomLeftY = y
                                break
                            lastSeenYBot = y
                        else:
                            mask[y][x] = 0
                if(bottomSeen and maskAmtBottom < 3):
                    bottomRightX = x
                    bottomRightY = lastSeenYBot
                    bottomSeen = False
                    
                            # 39.3in
                            # 17 in
                        # 
                        # 
            
            '''
            stdDevX = 0
            stdDevY = 0
            for y in range(len(mask)):
                for x in range(len(mask[y])):
                    if(mask[y][x]):
                        amt1 += 1
                        stdDevX += (avgX-x)**2
                        stdDevY += (avgY-y)**2
                        if(amt1 >= amt):
                            break
            stdDevX = int(stdDevX / amt)
            stdDevX = int(stdDevY / amt)
            cv2.rectangle(mask, (avgX-stdDevX*2, avgY-stdDevY*2), (avgX+stdDevX*2, avgY+stdDevY*4), 255, 3)
            '''
            #cv2.rectangle(mask, (0,0), (mask.shape[0], mask.shape[1]), 0, 10000)
            mask[maxXY][maxX] = 255
            mask[minXY][minX] = 255
            mask[bottomLeftY][bottomLeftX] = 255
            mask[bottomRightY][bottomRightX] = 255
            cv2.line(mask, (bottomLeftX, bottomLeftY), (minX, minXY), 255, 3)
            cv2.line(mask, (bottomLeftX, bottomLeftY), (bottomRightX, bottomRightY), 255, 3)
            cv2.line(mask, (bottomRightX, bottomRightY), (maxX, maxXY), 255, 3)
            '''
            minXY1 = minXY[0]
            minXY2 = minXY[-1]
            maxXY1 = maxXY[0]
            maxXY2 = maxXY[-1]
            if(len(minXY) > 1):
                cv2.line(mask, (minX, minXY1), (minX, minXY2), 255, 3)
            if(len(maxXY) > 1):
                cv2.line(mask, (maxX, maxXY1), (maxX, maxXY2), 255, 3)
            minYX1 = minYX[0]
            minYX2 = minYX[-1]
            maxYX1 = maxYX[0]
            maxYX2 = maxYX[-1]
            if(len(minYX) > 1):
                cv2.line(mask, (minYX1, minY), (minYX2, minY), 255, 10)
            if(len(maxYX) > 1):
                cv2.line(mask, (maxYX1, maxY), (maxYX2, maxY), 255, 10)
            cv2.line(mask, (minX, minXY1), (minYX1, minY), 255, 10)
            cv2.line(mask, (minX, minXY2), (maxYX1, maxY), 255, 10)
            cv2.line(mask, (maxX, maxXY1), (minYX2, minY), 255, 10)
            cv2.line(mask, (maxX, maxXY2), (maxYX2, maxY), 255, 10)
            '''
        else:
            table.putNumber("tape-x", -1)
            table.putNumber("tape-y", -1)
        #print(mask.dtype, hsv.dtype)
        # (optional) send some image back to the dashboard
        #print(img)
        outputStream.putFrame(mask)
