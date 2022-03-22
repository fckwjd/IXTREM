import cv2
import numpy as np
import time

cap = cv2.VideoCapture()
cap.open(0)

# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
# cap.set(4, 720)

ret, old_frame = cap.read()
mask_old = np.zeros_like(old_frame)
color_chc = 'pink'

# Create a black image, a window
img1 = np.zeros((300, 512, 3), np.uint8)
img2 = np.zeros((300, 512, 3), np.uint8)
cv2.namedWindow('Bars')
cv2.namedWindow('Image 1')
cv2.namedWindow('Image 2')


def nothing(x):
    pass


cv2.createTrackbar('H1', 'Bars', 0, 179, nothing)
cv2.createTrackbar('S1', 'Bars', 0, 255, nothing)
cv2.createTrackbar('V1', 'Bars', 0, 255, nothing)
cv2.createTrackbar('H2', 'Bars', 0, 179, nothing)
cv2.createTrackbar('S2', 'Bars', 0, 255, nothing)
cv2.createTrackbar('V2', 'Bars', 0, 255, nothing)
# create switch for ON/OFF functionality
cv2.createTrackbar("Switch", 'Bars', 0, 1, nothing)


def CannyDetec(img, color_chc, color_val, ths, minEdge, maxEdge):
    # Convert BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    if color_val != []:
        lower = np.array([color_val[0], color_val[1], color_val[2]])
        upper = np.array([color_val[3], color_val[4], color_val[5]])
    else:
        # define range of colors in HSV   
        if color_chc == 'blue':
            lower = np.array([85, 50, 50])
            upper = np.array([145, 255, 255])
        if color_chc == 'red':
            lower1 = np.array([130, 50, 50])
            upper1 = np.array([179, 255, 255])
            lower2 = np.array([0, 50, 50])
            upper2 = np.array([10, 255, 255])
        if color_chc == 'green':
            lower = np.array([45, 50, 50])
            upper = np.array([85, 255, 255])
        if color_chc == 'white':
            lower = np.array([0, 0, 100])
            upper = np.array([179, 255, 255])
        if color_chc == 'yellow':
            lower = np.array([24, 120, 140])
            upper = np.array([36, 255, 255])
        if color_chc == 'pink':
            lower = np.array([130, 130, 130])
            upper = np.array([170, 255, 255])
        if color_chc == 'black':
            lower = np.array([0, 0, 0])
            upper = np.array([179, 255, 30])

            # Threshold the HSV image to get only chosen colors
    if color_chc == 'red':
        mask = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)
        mask = cv2.add(mask, mask2)
    else:
        mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((ths, ths), np.uint8)

    # Bitwise-AND mask and original image: the pixels different from mask color set to 0 (black)
    res = cv2.bitwise_and(img, img, mask=mask)

    # Threshold the image to get black and white image
    res = np.uint8(res / 2.)
    res = cv2.cvtColor(res, cv2.COLOR_HSV2BGR)
    res = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
    rest, res = cv2.threshold(res, 1, 255, 0)

    # Find the edges on the binary image
    edge = cv2.Canny(res, minEdge, maxEdge, apertureSize=5)

    # Find the contours on the binary image
    image, contours, hierarchy = cv2.findContours(res, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours


def chooseColor():
    h1 = cv2.getTrackbarPos('H1', 'Bars')
    s1 = cv2.getTrackbarPos('S1', 'Bars')
    v1 = cv2.getTrackbarPos('V1', 'Bars')
    h2 = cv2.getTrackbarPos('H2', 'Bars')
    s2 = cv2.getTrackbarPos('S2', 'Bars')
    v2 = cv2.getTrackbarPos('V2', 'Bars')
    switch = cv2.getTrackbarPos('Switch', 'Bars')

    if switch == 1:
        img1[:] = [h1, s1, v1]
        img2[:] = [h2, s2, v2]
        values = [h1, s1, v1, h2, s2, v2]
    else:
        img1[:] = 0
        img2[:] = 0
        values = []
    return values, img1, img2


while (1):
    # Recalculate an empty mask
    mask_old = np.zeros_like(old_frame)

    # Take each frame
    _, frame = cap.read()

    # Convert BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    cv2.imshow('Image 1', img1)
    cv2.imshow('Image 2', img2)
    colorvalue, img1, img2 = chooseColor()
    img1 = cv2.cvtColor(img1, cv2.COLOR_HSV2BGR)
    img2 = cv2.cvtColor(img2, cv2.COLOR_HSV2BGR)
    # Histogram equalization
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    lab = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    frame = lab

    # Display the recomposed image
    contours_r = CannyDetec(frame, color_chc, colorvalue, 2, 1000, 5000)

    # ------------------------------------------------------------------
    # Edge detection using hsv collor and Canny detection method

    # Draw contour around the contour_r objects
    idx_txt = 0

    if len(contours_r) > 0:
        area_t = 0
        sum_t = 0
        M = 0
        for idx in range(len(contours_r)):
            cnt = contours_r[idx]
            area = cv2.contourArea(cnt)
            M = cv2.moments(cnt)
            # print('area= '+str(area))
            if area > 10:
                cv2.drawContours(mask_old, contours_r, idx, (0, 255, 255), 1, maxLevel=0)
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                cv2.circle(mask_old, (cx, cy), 1, (0, 255, 0), 1)

    img = cv2.add(frame, mask_old)

    cv2.imshow('img', img)
    cv2.imshow('img clahe', lab)

    # Wait for a key pressed
    k = cv2.waitKey(30) & 0xFF
    # Esc. pressed, quit app
    if k == 27:
        break
    # "p" pressed, save image
    if k == ord('p'):
        cv2.imwrite("saved_current" + ".jpg", frame)
        cv2.imwrite("saved_current_data" + ".jpg", img)

# Destroy windows, close the app
cv2.destroyAllWindows()
cap.release()
