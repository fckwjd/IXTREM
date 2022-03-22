# -*- coding: utf-8 -*-

import cv2
import numpy as np
import cannydetec as cd

cap = cv2.VideoCapture(0)

ret, old_frame = cap.read()
mask_old = np.zeros_like(old_frame)
color_chc = 'dark_red'

while (1):
    # Recalculate an empty mask
    mask_old = np.zeros_like(old_frame)

    # Take each frame
    _, frame = cap.read()

    # Create a gray image
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Convert BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Histogram equalization
    # lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    # l, a, b = cv2.split(lab)
    # clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4,4))   
    # l = clahe.apply(l)
    # lab = cv2.merge((l, a, b))
    # lab = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    # frame = lab   

    contours_b = cd.CannyDetec(frame, color_chc, 2, 1000, 5000)

    # ------------------------------------------------------------------

    idx_txt = 0
    if len(contours_b) > 0:
        area_t = 0
        sum_t = 0
        idx_t = 0
        for idx in range(len(contours_b)):
            cnt = contours_b[idx]
            area_t = 0
            cnt = contours_b[idx]
            area = cv2.contourArea(cnt)
            M = cv2.moments(cnt)
            if area > 500 and area < 50000:
                try:
                    rect1 = cv2.minAreaRect(cnt)
                    box1 = cv2.boxPoints(rect1)
                    box1 = np.int0(box1)
                    cv2.drawContours(mask_old, [box1], -1, (0, 255, 255), -1, maxLevel=0)
                    # cv2.drawContours(mask_old, contours_b, idx, (0,255,255), 1)
                except:
                    None
                cv2.drawContours(mask_old, contours_b, idx, (0, 255, 255), 1)
                cx_dir = int(M['m10'] / M['m00'])
                cy_dir = int(M['m01'] / M['m00'])

    img = cv2.add(frame, mask_old)

    cv2.imshow('img', img)

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
