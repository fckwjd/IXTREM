import cv2
import numpy as np
import cannydetec as cd


def ColorBox(frame, color_chc):
    # Take each frame
    # _, frame = cap.read()

    # Recalculate an empty mask
    mask = np.zeros_like(frame)

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

    contours = cd.CannyDetec(frame, color_chc, 1000, 5000)

    if len(contours) > 0:
        for idx in range(len(contours)):
            cnt = contours[idx]
            area = cv2.contourArea(cnt)
            M = cv2.moments(cnt)
            if area > 500 and area < 50000:
                try:
                    rect = cv2.minAreaRect(cnt)
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    # cv2.drawContours(mask,[box],-1,(0,255,255),-1, maxLevel = 0)
                    cv2.drawContours(mask, contours, idx, (0, 255, 255), 1)
                except:
                    None
                cv2.drawContours(mask, contours, idx, (0, 255, 255), 1)
                cx_dir = int(M['m10'] / M['m00'])
                cy_dir = int(M['m01'] / M['m00'])

    img = cv2.add(frame, mask)
    # cv2.imshow('img', img)
    return (img)


if __name__ == '__main__':
    cap = cv2.VideoCapture(0)

    color_chc = 'dark_red'

    while (1):
        _, frame = cap.read()
        frame = ColorBox(frame, color_chc)
        cv2.imshow('img', frame)
        # Wait for a key pressed
        k = cv2.waitKey(30) & 0xFF
        # Esc. pressed, quit app
        if k == 27:
            break
        # "p" pressed, save image
        if k == ord('p'):
            cv2.imwrite("saved_current" + ".jpg", frame)

    # Destroy windows, close the app
    cv2.destroyAllWindows()
    cap.release()
