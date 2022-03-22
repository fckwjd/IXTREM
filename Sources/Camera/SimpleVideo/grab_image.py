import numpy as np
import cv2

cap = cv2.VideoCapture(0)

# take first frame of the video
ret, frame = cap.read()

# Create a mask image for drawing purposes
# ret, old_frame = cap.read()
# mask = np.zeros_like(old_frame)

# drawing = False # true if mouse is pressed
# mode = True # if True, draw rectangle. Press 'm' to toggle to curveqqqqqqqq
# ix,iy = -1,-1

# def draw_circle(event,x,y,flags,param):
# global ix,iy,drawing,mode

# if event == cv2.EVENT_LBUTTONDOWN:
# drawing = True
# ix,iy = x,y

# elif event == cv2.EVENT_MOUSEMOVE:
# if drawing == True:
# if mode == True:
# cv2.rectangle(mask,(ix,iy),(x,y),(0,255,0),-1)
# else:
# cv2.circle(mask,(x,y),5,(0,0,255),-1)

# elif event == cv2.EVENT_LBUTTONUP:
# drawing = False
# if mode == True:
# cv2.rectangle(mask,(ix,iy),(x,y),(0,255,0),-1)
# else:
# cv2.circle(mask,(x,y),5,(0,0,255),-1)


# cv2.namedWindow('image')
# cv2.setMouseCallback('image',draw_line)

while True:
    ret, frame = cap.read()
    print(ret)
    if ret == True:
        cv2.imshow('frame', frame)
        k = cv2.waitKey(30) & 0xff
        if (k == 27):
            break
    else:
        break
    # if k == ord('p'):
    # f = open("saved_image.jpg")
    # f.write(frame)
    # f.close()
    # dft = cv2.dft(np.float32(frame),flags = cv2.DFT_COMPLEX_OUTPUT)
    # dft_shift = np.fft.fftshift(dft)

    # magnitude_spectrum = 20*np.log(cv2.magnitude(dft_shift[:,:,0],dft_shift[:,:,1]))
    # cv2.imshow('mag',magnitude_spectrum)

cv2.destroyAllWindows()
cap.release()
