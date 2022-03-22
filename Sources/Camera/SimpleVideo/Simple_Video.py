# -*- coding: utf-8 -*-
import cv2
import numpy as np
import cameraundistort as undis
import colordetection as coldet
import rangefinder as rgfd
# import urllib.request
import time

# import cgitb
# cgitb.enable()

# response = urllib.request.urlopen('http://192.168.0.1/cam.cgi?mode=startstream&value=49152')
# html = response.read()
# print(html)
# time.sleep(1)

# response = urllib.request.urlopen('http://192.168.0.1/cam.cgi?mode=camcmd&value=capture')
# html = response.read()
# print(html)
# time.sleep(1)
# stream = 'http://192.168.0.100:7000'
cap = cv2.VideoCapture(0)
_, frame = cap.read()
width = cap.get(3)
height = cap.get(4)
if width > 0 and height > 0:
    print(height, width)
    # cv2.imshow('img', frame)
    # Create CameraUndistort object
    camcorr = undis.CameraUndistort()
    mtx, dist = camcorr.calibrate()

    # Create ColorDetection object
    colordetec = coldet.ColorDetection('green', 2, 1000, 5000, (0, 255, 255), 1, [1000, 50000], 200)

    # Create RangeFinder object
    rangefinder = rgfd.RangeFinder((0, 0), (width, height))

    # Correct distortion
    frame = camcorr.undistortImage(frame, mtx, dist)

    # Store frame in object
    colordetec.setFrame(frame)

    # Create empty mask
    colordetec.createEmptyMask()

    # Initialize file number
    idx_file = 0

    # Acquire image continuously
    while (1):
        try:
            # Grab frame
            _, frame = cap.read()

            # Correct distortion
            # frame = camcorr.undistortImage(frame, mtx, dist)

            # Store frame in object
            colordetec.setFrame(frame)

            # Detect contours
            colordetec.CannyDetec()

            # Draw contours
            # colordetec.drawContourCircle()
            mask, center = colordetec.drawContour()
            rangefinder.pixelsFromCenter(center)
            distance = rangefinder.calcDistance()
            print(distance * 1e2)
            # print(center)
            # colordetec.findMaxSatContour(frame,)

            # Display images
            img = cv2.add(frame, mask)
            cv2.imshow('img', img)
        except:
            None
        # Wait for a key pressed
        k = cv2.waitKey(30) & 0xFF
        # Esc. pressed, quit app
        if k == 27:
            break
        # "p" pressed, save image
        if k == ord('p'):
            cv2.imwrite("chess_" + str(idx_file) + ".jpg", frame)
            idx_file = idx_file + 1

    # Destroy windows, close the app
cv2.destroyAllWindows()
cap.release()

# response = urllib.request.urlopen('http://192.168.0.1/cam.cgi?mode=stopstream')
# html = response.read()
# print(html)
# time.sleep(1)
