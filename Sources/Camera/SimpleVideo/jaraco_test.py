import jaraco.video.capture as Capture
import cv2

Cap = Capture.Device(1, show_video_window=True)

while (1):
    Cap.get_image()
    # cv2.imshow('frame', img)
    # print('ok')
    k = cv2.waitKey(30) & 0xFF
    # Esc. pressed, quit app
    if k == 27:
        break
