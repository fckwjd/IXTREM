from __future__ import print_function
import sys
import cv2


def main(argv):
    # capture from camera at location 0
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
    eye_cascade = cv2.CascadeClassifier('haarcascade_eye.xml')
    H = []
    delta = 0
    while True:
        ret, img = cap.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        try:
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                # xc = x+w/2
                # yc = y+h/2
                # w = int(w*0.85)
                # h = int(h*1.3)
                # x = int(xc-w/2)
                # y = int(yc-h/2)

                roi_color = img[y - delta:y + h - delta, x:x + w]
                roi_gray = gray[y:y + h, x:x + w]
                roi_hsv = img[y - delta:y + h - delta, x:x + w]

                hist = cv2.calcHist([roi_color], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
                histhsv = cv2.calcHist([roi_hsv], [0, 1], None, [180, 256], [0, 180, 0, 256])
                if len(H) == 0:
                    H = hist
                    Hhsv = histhsv
                else:
                    compH = cv2.compareHist(H, hist, cv2.HISTCMP_CORREL)
                    compHhsv = cv2.compareHist(Hhsv, histhsv, cv2.HISTCMP_CORREL)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(img, str(compH), (0, 30), font, 1, (0, 0, 255))
                    cv2.putText(img, str(compHhsv), (0, 80), font, 1, (0, 0, 255))

                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
                # eyes = eye_cascade.detectMultiScale(roi_gray,scaleFactor=1.25, minNeighbors=10)
                # for (ex,ey,ew,eh) in eyes:
                # cv2.rectangle(roi_color,(ex,ey),(ex+ew,ey+eh),(0,255,0),2)

            cv2.imshow('img', img)
        except:
            None
        key = cv2.waitKey(10)
        if key == 27:
            break

    cv2.destroyAllWindows()
    cv2.VideoCapture(0).release()


if __name__ == '__main__':
    main(sys.argv)
