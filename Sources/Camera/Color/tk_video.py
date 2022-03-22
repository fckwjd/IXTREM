#!/usr/bin/python

import numpy as np
from multiprocessing import Process, Queue
from queue import Empty
import cv2
from PIL import Image, ImageTk
import time
import tkinter as tk


# tkinter GUI functions----------------------------------------------------------
def quit_(root, process):
    process.terminate()
    root.destroy()


def update_image(image_label, queue):
    frame = queue.get()
    mask_old = np.zeros_like(frame)
    img_red, mask_red = DetectColor(frame, 'red')
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # Display the recomposed image
    contours_r = CannyDetec(img_red, 'red', 1, 100, 5000)
    img_green, mask_green = DetectColor(frame, 'green')
    # Display the recomposed image
    contours_b = CannyDetec(img_green, 'green', 5, 1000, 1500)
    idx_txt = 0
    if len(contours_b) > 0:
        area_t = 0
        sum_t = 0
        for idx in range(len(contours_b)):
            cnt = contours_b[idx]
            area = cv2.contourArea(cnt)
            M = cv2.moments(cnt)
            if area > 50:
                cimg = np.zeros_like(mask_old)
                cv2.drawContours(cimg, contours_b, idx, (255, 255, 255), -1)
                cimg = cv2.cvtColor(cimg, cv2.COLOR_BGR2GRAY)
                sum_img = cv2.sumElems(cimg * frame_gray)
                area_t = area_t + area
                sum_t = sum_t + max(sum_img)
                cv2.drawContours(mask_old, contours_b, idx, (0, 255, 255), 1)
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
        # print('sum: '+str(sum_t))    
        # print('area: '+str(area_t))        
        if (area_t > 0 and sum_t > 0):
            text = 'Distance  = ' + str(sum_t / area_t)
            cv2.putText(mask_old, text, (20, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))

    # Draw contour around the contour_r objects
    idx_txt = 0
    if len(contours_r) > 0:
        area_t = 0
        sum_t = 0
        for idx in range(len(contours_r)):
            cnt = contours_r[idx]
            area = cv2.contourArea(cnt)
            M = cv2.moments(cnt)
            # print('area= '+str(area))
            if area > 1:
                cv2.drawContours(mask_old, contours_r, idx, (0, 255, 255), 1)
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                cv2.circle(mask_old, (cx, cy), 1, (0, 255, 0), 1)
                idx_txt = idx_txt + 1
                text = 'Defect ' + str(idx_txt)
                cv2.putText(mask_old, text, (cx + 20, cy + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255))

    im = cv2.add(frame, mask_old)
    im = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    a = Image.fromarray(im)
    b = ImageTk.PhotoImage(image=a)
    image_label.configure(image=b)
    image_label._image_cache = b  # avoid garbage collection


def update_all(root, image_label, queue):
    update_image(image_label, queue)
    root.after(0, func=lambda: update_all(root, image_label, queue))


def CannyDetec(img, color_chc, ths, minEdge, maxEdge):
    # Convert BGR to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # define range of colors in HSV   
    if color_chc == 'blue':
        lower = np.array([100, 50, 50])
        upper = np.array([120, 255, 255])
    if color_chc == 'red':
        lower = np.array([0, 50, 50])
        upper = np.array([30, 255, 255])
        # lower = np.array([170,50,140])
        # upper = np.array([179,140,140])        
    if color_chc == 'green':
        lower = np.array([30, 50, 50])
        upper = np.array([120, 255, 255])
    if color_chc == 'white':
        lower = np.array([0, 0, 255])
        upper = np.array([179, 0, 255])

        # Threshold the HSV image to get only chosen colors
    mask = cv2.inRange(hsv, lower, upper)
    kernel = np.ones((ths, ths), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Bitwise-AND mask and original image: the pixels different from mask color set to 0 (black)
    res = cv2.bitwise_and(img, img, mask=mask)

    # Threshold the image to get black and white image
    res = np.uint8(res / 2.)
    res = cv2.cvtColor(res, cv2.COLOR_HSV2BGR)
    res = cv2.cvtColor(res, cv2.COLOR_BGR2GRAY)
    rest, res = cv2.threshold(res, 1, 255, 0)

    # Erode and dilate to remove the noise
    res = cv2.erode(res, kernel, iterations=1)
    res = cv2.dilate(res, kernel, iterations=1)

    # Find the edges on the binary image
    edge = cv2.Canny(res, minEdge, maxEdge, apertureSize=5)

    # Find the contours on the binary image
    image, contours, hierarchy = cv2.findContours(res, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    return contours


def DetectColor(img, color):
    # Store BGR current frame to work on it without problems
    bgr = img

    # Split the frame in RGB Channels
    mask_blue, mask_green, mask_red = cv2.split(bgr)

    if color == 'red':
        # Remove blue and green color from red in order to get only red-ish object (yellow, red, purple,...)
        mask = ((1 * mask_red - 1 / 2 * mask_blue - 1 / 2 * mask_green))
    if color == 'blue':
        # Remove red and green color from blue in order to get only blue-ish object
        mask = ((1 * mask_blue - 1 / 2 * mask_red - 1 / 2 * mask_green))
    if color == 'green':
        # Remove red and blue color from green in order to get only green-ish object
        mask = ((1 * mask_green - 1 / 2 * mask_blue - 1 / 2 * mask_red))
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


# multiprocessing image processing functions-------------------------------------
def image_capture(queue):
    vidFile = cv2.VideoCapture(0)
    while True:
        try:
            flag, frame = vidFile.read()
            if flag == 0:
                break
                queue.put(frame)
                cv2.waitKey(20)
        except:
            continue
    vidFile.release()


if __name__ == '__main__':
    queue = Queue()
    print('queue initialized...')
    root = tk.Tk()
    print('GUI initialized...')
    image_label = tk.Label(master=root)  # label for the video frame
    image_label.pack()
    print('GUI image label initialized...')
    p = Process(target=image_capture, args=(queue,))
    p.start()
    print('image capture process has started...')
    # quit button
    quit_button = tk.Button(master=root, text='Quit', command=lambda: quit_(root, p))
    quit_button.pack()
    print('quit button initialized...')
    # setup the update callback
    root.after(0, func=lambda: update_all(root, image_label, queue))
    print('root.after was called...')
    root.mainloop()
    print('mainloop exit')
    p.join()
    print('image capture process exit')
