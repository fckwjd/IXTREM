import cv2
import numpy as np


def nothing(x):
    pass


# Create a black image, a window
img = np.zeros((300, 512, 3), np.uint8)
img2 = np.zeros((300, 512, 3), np.uint8)
cv2.namedWindow('Bars')
cv2.namedWindow('Image 1')
cv2.namedWindow('Image 2')
# create trackbars for color change
# cv2.createTrackbar('R','image',0,255,nothing)
# cv2.createTrackbar('G','image',0,255,nothing)
# cv2.createTrackbar('B','image',0,255,nothing)

cv2.createTrackbar('H1', 'Bars', 0, 179, nothing)
cv2.createTrackbar('S1', 'Bars', 0, 255, nothing)
cv2.createTrackbar('V1', 'Bars', 0, 255, nothing)
cv2.createTrackbar('H2', 'Bars', 0, 179, nothing)
cv2.createTrackbar('S2', 'Bars', 0, 255, nothing)
cv2.createTrackbar('V2', 'Bars', 0, 255, nothing)

# create switch for ON/OFF functionality
switch = '0 : OFF \n1 : ON'
cv2.createTrackbar(switch, 'Bars', 0, 1, nothing)

while (1):
    cv2.imshow('Image 1', img)
    cv2.imshow('Image 2', img2)
    k = cv2.waitKey(1) & 0xFF
    if k == 27:
        break

    # get current positions of four trackbars
    # r = cv2.getTrackbarPos('R','image')
    # g = cv2.getTrackbarPos('G','image')
    # b = cv2.getTrackbarPos('B','image')
    h1 = cv2.getTrackbarPos('H1', 'Bars')
    s1 = cv2.getTrackbarPos('S1', 'Bars')
    v1 = cv2.getTrackbarPos('V1', 'Bars')
    h2 = cv2.getTrackbarPos('H2', 'Bars')
    s2 = cv2.getTrackbarPos('S2', 'Bars')
    v2 = cv2.getTrackbarPos('V2', 'Bars')
    sw = cv2.getTrackbarPos(switch, 'Bars')

    if sw == 0:
        img[:] = 0
    else:
        # img[:] = [b,g,r]
        img[:] = [h1, s1, v1]
        img = cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
        img2[:] = [h2, s2, v2]
        img2 = cv2.cvtColor(img2, cv2.COLOR_HSV2BGR)
cv2.destroyAllWindows()
