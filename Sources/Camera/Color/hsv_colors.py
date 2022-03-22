import numpy as np
import cv2

green = np.uint8([[[60, 56, 131]]])
hsv_green = cv2.cvtColor(green, cv2.COLOR_BGR2HSV)
print(hsv_green)
