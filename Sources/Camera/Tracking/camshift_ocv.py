import numpy as np
import cv2

cap = cv2.VideoCapture(0)

# take first frame of the video
ret, frame = cap.read()

# setup initial location of window
r, h, c, w = 250, 90, 400, 125  # simply hardcoded the values
track_window = (c, r, w, h)

# Create a mask image for drawing purposes
maskz = np.zeros_like(frame)

rh = r + w
cw = c + w
# set up the ROI for tracking
roi = frame[r:rh, c:cw]
hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv_roi, np.array((0., 60., 32.)), np.array((180., 255., 255.)))
roi_hist = cv2.calcHist([hsv_roi], [0], mask, [180], [0, 180])
cv2.normalize(roi_hist, roi_hist, 0, 255, cv2.NORM_MINMAX)

# Setup the termination criteria, either 10 iteration or move by atleast 1 pt
term_crit = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 1)

while True:
    ret, frame = cap.read()

    if ret == True:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        dst = cv2.calcBackProject([hsv], [0], roi_hist, [0, 180], 1)
        maskz = np.zeros_like(frame)
        # apply meanshift to get the new location
        ret, track_window = cv2.CamShift(dst, track_window, term_crit)

        # Draw it on image
        pts = cv2.boxPoints(ret)
        pts = np.int0(pts)
        maskz = cv2.polylines(maskz, [pts], True, 255, 2)

        k = cv2.waitKey(60) & 0xff
        if k == 27:
            break
        if k == ord('p'):
            img = frame
            cv2.imshow('img', img)
            cv2.imwrite("saved_current" + ".jpg", img)
        else:
            img = cv2.add(frame, maskz)
            cv2.imshow('img', img)

    else:
        break

cv2.destroyAllWindows()
cap.release()
