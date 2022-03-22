from __future__ import print_function
import sys
import cv2


def nothing(x):
    pass


def main(argv):
    # capture from camera at location 0
    cap = cv2.VideoCapture(0)

    cv2.namedWindow('Bars')
    cv2.createTrackbar('Frame Rate', 'Bars', 0, 120, nothing)
    cv2.createTrackbar('Height', 'Bars', 0, 1024, nothing)
    cv2.createTrackbar('Width', 'Bars', 0, 1980, nothing)
    cv2.createTrackbar('Brightness', 'Bars', 0, 100, nothing)
    cv2.createTrackbar('Contrast', 'Bars', 0, 100, nothing)
    cv2.createTrackbar('Saturation', 'Bars', 0, 100, nothing)
    cv2.createTrackbar('Hue', 'Bars', 0, 255, nothing)
    cv2.createTrackbar('Gain', 'Bars', 0, 100, nothing)
    cv2.createTrackbar('Exposure', 'Bars', 0, 20, nothing)
    cv2.resizeWindow('Bars', (300, 200))

    frame_rate = cv2.setTrackbarPos('Frame Rate', 'Bars', 60)
    height = cv2.setTrackbarPos('Height', 'Bars', 480)
    width = cv2.setTrackbarPos('Width', 'Bars', 640)
    brightness = cv2.setTrackbarPos('Brightness', 'Bars', 20)
    contrast = cv2.setTrackbarPos('Contrast', 'Bars', 50)
    saturation = cv2.setTrackbarPos('Saturation', 'Bars', 50)
    hue = cv2.setTrackbarPos('Hue', 'Bars', 100)
    gain = cv2.setTrackbarPos('Gain', 'Bars', 10)
    exposure = cv2.setTrackbarPos('Exposure', 'Bars', 6)

    # Read the current setting from the camera
    test = cap.get(0)
    ratio = cap.get(2)
    frame_rate = cap.get(5)
    width = cap.get(3)
    height = cap.get(4)
    brightness = cap.get(10)
    contrast = cap.get(11)
    saturation = cap.get(12)
    hue = cap.get(13)
    gain = cap.get(14)
    exposure = cap.get(15)

    print("Test: ", test)
    print("Ratio: ", ratio)
    print("Frame Rate: ", frame_rate)
    print("Height: ", height)
    print("Width: ", width)
    print("Brightness: ", brightness)
    print("Contrast: ", contrast)
    print("Saturation: ", saturation)
    print("Hue: ", hue)
    print("Gain: ", gain)
    print("Exposure: ", exposure)

    while True:
        # frame_rate = cv2.getTrackbarPos('Frame Rate','Bars')
        height = cv2.getTrackbarPos('Height', 'Bars')
        width = cv2.getTrackbarPos('Width', 'Bars')
        brightness = cv2.getTrackbarPos('Brightness', 'Bars')
        contrast = cv2.getTrackbarPos('Contrast', 'Bars')
        saturation = cv2.getTrackbarPos('Saturation', 'Bars')
        hue = cv2.getTrackbarPos('Hue', 'Bars')
        gain = cv2.getTrackbarPos('Gain', 'Bars')
        exposure = cv2.getTrackbarPos('Exposure', 'Bars')

        # cap.set(5,frame_rate)
        cap.set(3, width)
        cap.set(4, height)
        cap.set(10, brightness)
        cap.set(11, contrast)
        cap.set(12, saturation)
        cap.set(13, hue)
        cap.set(14, -gain)
        cap.set(15, -exposure)

        ret, img = cap.read()
        cv2.imshow("input", img)

        key = cv2.waitKey(10)
        if key == 27:
            break

    # Read the current setting from the camera
    test = cap.get(0)
    ratio = cap.get(2)
    frame_rate = cap.get(5)
    width = cap.get(3)
    height = cap.get(4)
    brightness = cap.get(10)
    contrast = cap.get(11)
    saturation = cap.get(12)
    hue = cap.get(13)
    gain = cap.get(14)
    exposure = cap.get(15)

    print("Test: ", test)
    print("Ratio: ", ratio)
    print("Frame Rate: ", frame_rate)
    print("Height: ", height)
    print("Width: ", width)
    print("Brightness: ", brightness)
    print("Contrast: ", contrast)
    print("Saturation: ", saturation)
    print("Hue: ", hue)
    print("Gain: ", gain)
    print("Exposure: ", exposure)

    cv2.destroyAllWindows()
    cv2.VideoCapture(0).release()


#   0  CV_CAP_PROP_POS_MSEC Current position of the video file in milliseconds.
#   1  CV_CAP_PROP_POS_FRAMES 0-based index of the frame to be decoded/captured next.
#   2  CV_CAP_PROP_POS_AVI_RATIO Relative position of the video file
#   3  CV_CAP_PROP_FRAME_WIDTH Width of the frames in the video stream.
#   4  CV_CAP_PROP_FRAME_HEIGHT Height of the frames in the video stream.
#   5  CV_CAP_PROP_FPS Frame rate.
#   6  CV_CAP_PROP_FOURCC 4-character code of codec.
#   7  CV_CAP_PROP_FRAME_COUNT Number of frames in the video file.
#   8  CV_CAP_PROP_FORMAT Format of the Mat objects returned by retrieve() .
#   9 CV_CAP_PROP_MODE Backend-specific value indicating the current capture mode.
#   10 CV_CAP_PROP_BRIGHTNESS Brightness of the image (only for cameras).
#   11 CV_CAP_PROP_CONTRAST Contrast of the image (only for cameras).
#   12 CV_CAP_PROP_SATURATION Saturation of the image (only for cameras).
#   13 CV_CAP_PROP_HUE Hue of the image (only for cameras).
#   14 CV_CAP_PROP_GAIN Gain of the image (only for cameras).
#   15 CV_CAP_PROP_EXPOSURE Exposure (only for cameras).
#   16 CV_CAP_PROP_CONVERT_RGB Boolean flags indicating whether images should be converted to RGB.
#   17 CV_CAP_PROP_WHITE_BALANCE Currently unsupported
#   18 CV_CAP_PROP_RECTIFICATION Rectification flag for stereo cameras (note: only supported by DC1394 v 2.x backend currently)

if __name__ == '__main__':
    main(sys.argv)
