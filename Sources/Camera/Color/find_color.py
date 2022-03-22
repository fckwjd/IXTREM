import cv2
import numpy as np

cap = cv2.VideoCapture(1)
# cap.set(3, 1280)
# cap.set(4, 720)
# cap.set(14, 100)
# cap.open("http://192.168.0.100/videostream.asf?user=A1-wearable&pwd=a1234567")
ret, old_frame = cap.read()
mask_old = np.zeros_like(old_frame)
color_chc = 'green'


def CannyDetec(img, color_chc, ths, minEdge, maxEdge):
    # Convert BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # define range of colors in HSV   
    if color_chc == 'blue':
        lower = np.array([85, 50, 50])
        upper = np.array([145, 255, 255])
    if color_chc == 'red':
        lower1 = np.array([130, 50, 50])
        upper1 = np.array([179, 255, 255])
        lower2 = np.array([0, 50, 50])
        upper2 = np.array([10, 255, 255])
        # lower = np.array([170,50,140])
        # upper = np.array([179,140,140])        
    if color_chc == 'green':
        lower = np.array([45, 50, 50])
        upper = np.array([85, 255, 255])
    if color_chc == 'white':
        lower = np.array([0, 0, 255])
        upper = np.array([179, 0, 255])
    if color_chc == 'yellow':
        lower = np.array([30, 50, 255])
        upper = np.array([35, 255, 255])

    # Threshold the HSV image to get only chosen colors
    if color_chc == 'red':
        mask = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)
        mask = cv2.add(mask, mask2)
    else:
        mask = cv2.inRange(hsv, lower, upper)

    kernel = np.ones((ths, ths), np.uint8)
    # mask = cv2.erode(mask,kernel,iterations = 5)
    # mask = cv2.dilate(mask,kernel,iterations = 5)

    # Bitwise-AND mask and original image: the pixels different from mask color set to 0 (black)
    res = cv2.bitwise_and(img, img, mask=mask)

    # Threshold the image to get black and white image
    res = np.uint8(res / 2.)
    res = cv2.cvtColor(res, cv2.COLOR_HSV2BGR)
    res = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
    rest, res = cv2.threshold(res, 1, 255, 0)

    # Erode and dilate to remove the noise
    # res = cv2.erode(res,kernel,iterations = 5)
    # res = cv2.dilate(res,kernel,iterations = 5)

    # Find the edges on the binary image
    edge = cv2.Canny(res, minEdge, maxEdge, apertureSize=5)

    # Find the contours on the binary image
    image, contours, hierarchy = cv2.findContours(res, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    return contours


def DetectColor(img, color):
    # Store BGR current frame to work on it without problems
    bgr = img

    # Split the frame in RGB Channels
    mask_blue, mask_green, mask_red = cv2.split(bgr)

    if color == 'red':
        # Remove blue and green color from red in order to get only red-ish object (yellow, red, purple,...)
        mask = cv2.subtract(mask_red, mask_green)
        mask_temp_b = cv2.addWeighted(mask_blue, 0.07, mask_blue, 0.07, 0)
        mask = cv2.subtract(mask, mask_temp_b)
    if color == 'blue':
        # Remove red and green color from blue in order to get only blue-ish object
        mask = cv2.subtract(mask_blue, mask_red)
        mask_temp_b = cv2.addWeighted(mask_green, 0.07, mask_green, 0.07, 0)
        mask = cv2.subtract(mask, mask_temp_b)
    if color == 'green':
        # Remove red and blue color from green in order to get only green-ish object
        mask = cv2.subtract(mask_green, mask_red)
        mask_temp_b = cv2.addWeighted(mask_blue, 0.07, mask_blue, 0.07, 0)
        mask = cv2.subtract(mask, mask_temp_b)
    else:
        # Remove blue and green color from red in order to get only red-ish object (yellow, red, purple,...), by default
        mask = ((1 * mask_red - 1 / 2 * mask_blue - 1 / 2 * mask_green))

    # Set to 0 negativ values (due to substraction)
    mask.clip(0)

    # kernel = np.ones((3,3),np.uint8)
    # mask_composition = cv2.erode(mask_composition,kernel,iterations = 1)
    # mask_composition = cv2.dilate(mask_composition,kernel,iterations = 1)

    # Normalize the mask to binary image
    mask = (mask) / 255.
    mask[mask > 0] = 1

    # Apply the binary mask to the RGB Channels
    mask_blue[mask <= 0] = 0
    mask_green[mask <= 0] = 0
    mask_red[mask <= 0] = 0

    # Merge the Channels to a color image diplaying only red-ish objects
    img_recompo = cv2.merge((mask_blue, mask_green, mask_red))
    if color == 'red':
        mask_b = mask_red
    if color == 'green':
        mask_b = mask_green
    if color == 'blue':
        mask_b = mask_blue

    mask_b[mask > 0] = 255.

    # Merge the Channels to a masked color image diplaying only red-ish objects
    img_mask = cv2.merge((mask_b, mask_b, mask_b))
    return img_recompo, img_mask


while (1):
    print('ok')
    # Recalculate an empty mask
    mask_old = np.zeros_like(old_frame)

    # Take each frame
    _, frame = cap.read()

    # Create a gray image
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Convert BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Histogram equalization
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(4, 4))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    lab = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    # frame = lab

    # Display the recomposed image
    contours_r = CannyDetec(frame, color_chc, 2, 1000, 5000)

    # img_green, mask_green = DetectColor(frame, 'green')

    # Display the recomposed image
    contours_b = CannyDetec(frame, 'green', 5, 1000, 5000)

    # ------------------------------------------------------------------
    # Edge detection using hsv collor and Canny detection method
    # contours_b = CannyDetec(frame, color_chc, 2, 100, 1000)        

    # Calculate the distance between the camera en the plan, based on area and intensity of the spot
    idx_txt = 0
    if len(contours_b) > 0:
        area_t = 0
        sum_t = 0
        idx_t = 0
        for idx in range(len(contours_b)):
            cnt = contours_b[idx]
            area = cv2.contourArea(cnt)
            if area > area_t:
                area_t = area
                idx_t = idx
        idx = idx_t
        area_t = 0
        # for idx in range(len(contours_b)):
        cnt = contours_b[idx]
        area = cv2.contourArea(cnt)
        M = cv2.moments(cnt)
        if area > 20:
            cimg = np.zeros_like(mask_old)
            cv2.drawContours(cimg, contours_b, idx, (255, 255, 255), -1, maxLevel=0)
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
            cimg = cv2.cvtColor(cimg, cv2.COLOR_BGR2GRAY)
            sum_img = cv2.sumElems(cimg * frame_gray)
            area_t = area_t + area
            sum_t = sum_t + max(sum_img)
            # cv2.drawContours(mask_old, contours_b, idx, (0,255,255), 1)                
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])

        if (area_t > 0 and sum_t > 0):
            text = 'Distance  = ' + str(1 * (area_t / 1000) - 0)
            cv2.putText(mask_old, text, (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0))

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
            if area > 1:
                cv2.drawContours(mask_old, contours_r, idx, (0, 255, 255), 1, maxLevel=0)
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                cv2.circle(mask_old, (cx, cy), 1, (0, 255, 0), 1)
                idx_txt = idx_txt + 1
                text = 'Defect ' + str(idx_txt)
                cv2.putText(mask_old, text, (cx + 20, cy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))

    img = cv2.add(frame, mask_old)

    cv2.imshow('img', img)
    # cv2.imshow('green',mask_green)
    # cv2.imshow('red',mask_red)
    # cv2.imshow('blue',mask_blue)
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
