# -*- coding: utf-8 -*-

import cv2
import numpy as np


def CannyDetec(img, color_chc, ths, minEdge, maxEdge):
    # Convert BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # define range of colors in HSV   
    if color_chc == 'blue':
        lower = np.array([100, 50, 50])
        upper = np.array([135, 255, 255])
    if color_chc == 'red':
        lower1 = np.array([135, 100, 100])
        upper1 = np.array([179, 255, 255])
        lower2 = np.array([0, 100, 100])
        upper2 = np.array([10, 255, 255])
    if color_chc == 'dark_red':
        lower1 = np.array([170, 100, 100])
        upper1 = np.array([179, 255, 255])
        lower2 = np.array([0, 100, 100])
        upper2 = np.array([10, 255, 255])
    if color_chc == 'green':
        lower = np.array([40, 40, 40])
        upper = np.array([85, 255, 255])
    if color_chc == 'white':
        lower = np.array([0, 0, 255])
        upper = np.array([179, 0, 255])
    if color_chc == 'yellow':
        lower = np.array([30, 50, 50])
        upper = np.array([40, 255, 255])
    if color_chc == 'pink':
        lower = np.array([130, 75, 75])
        upper = np.array([179, 255, 255])

        # Threshold the HSV image to get only chosen colors
    if color_chc == 'red' or color_chc == 'dark_red':
        mask = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)
        mask = cv2.add(mask, mask2)
    else:
        mask = cv2.inRange(hsv, lower, upper)

    # imgmask = cv2.add(frame,mask_old)

    # kernel = np.ones((ths,ths),np.uint8)

    # # Bitwise-AND mask and original image: the pixels different
    # from mask color set to 0 (black)
    # res = cv2.bitwise_and(img,img, mask= mask)

    # #Threshold the image to get black and white image
    # res = np.uint8(res/2.)
    # res = cv2.cvtColor(res,cv2.COLOR_HSV2BGR)
    # res = cv2.cvtColor(res,cv2.COLOR_BGR2GRAY)
    # rest, res= cv2.threshold(res, 1 , 255 , 0)

    # Find the edges on the binary image
    edge = cv2.Canny(mask, minEdge, maxEdge, apertureSize=3)

    # Find the contours on the binary image
    image, contours, hierarchy = cv2.findContours(mask,
                                                  cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours
