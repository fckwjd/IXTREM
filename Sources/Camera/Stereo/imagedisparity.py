import numpy as np
import cv2
from matplotlib import pyplot as plt

imgL = cv2.imread('img1.jpg', 0)
imgR = cv2.imread('img0.jpg', 0)
window_size = 3
min_disp = 16
num_disp = 256 - min_disp
stereo = cv2.StereoSGBM_create(minDisparity=min_disp,
                               numDisparities=num_disp,
                               blockSize=2,
                               P1=8 * 3 * window_size ** 2,
                               P2=32 * 3 * window_size ** 2,
                               disp12MaxDiff=1,
                               uniquenessRatio=10,
                               speckleWindowSize=50,
                               speckleRange=64
                               )
# stereo = cv2.StereoSGBM_create(numDisparities=512, blockSize=2)
disparity = stereo.compute(imgL, imgR)
plt.imshow(disparity, 'gray')
plt.show()
