from __future__ import print_function
import sys
import cv2


def main(argv):
    # capture from camera at location 0
    cap = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier("cat_cascade.xml")
    H = []
    delta = 0
    while True:
        ret, img = cap.read()
        height, width = img.shape[:2]
        size_max = 1000
        if (height and width) > size_max:
            ratio = width / height
            if ratio > 1:
                f = size_max / width
            else:
                f = size_max / height
            img = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        ret, thresh = cv2.threshold(gray, 127, 255, 0)
        try:
            rects = detector.detectMultiScale(gray, scaleFactor=1.25, minNeighbors=10, minSize=(75, 75))
            # loop over the cat faces and draw a rectangle surrounding each
            delta = 0
            if len(rects) > 0:
                for (i, (x, y, w, h)) in enumerate(rects):
                    # cv2.circle(image,(int(x+w/2),int(y+h/2)),1,(255,255,0))
                    cropped_cat = img[y - delta:y + h - delta, x:x + w]
                    hsvc = cv2.cvtColor(cropped_cat, cv2.COLOR_BGR2HSV)
                    hist = cv2.calcHist([cropped_cat], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
                    # normalize histogram and apply backprojection
                    # cv2.normalize(hist,hist,0,255,cv2.NORM_MINMAX)
                    # dst = cv2.calcBackProject([hsv],[0,1],hist,[0,180,0,256],1)
                    # disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(10,10))
                    # cv2.filter2D(dst,-1,disc,dst)
                # if len(H)==1:
                # try:
                # print('Cat ref: ' + imagefile)
                # H=hist
                # except:
                # None
                # else:
                # print(imagefile)
                # compH = cv2.compareHist(H,hist,cv2.HISTCMP_CORREL)
                # print(compH)
                # threshold and binary AND
                # ret,thresh = cv2.threshold(dst,50,255,0)
                # thresh = cv2.merge((thresh,thresh,thresh))
                # res = cv2.bitwise_and(image,thresh)
                # res = np.vstack((image,thresh,res))

                # show the detected cat faces
                # cv2.imshow("Cat Faces", image)
                # cv2.imshow('res',res)
                # cv2.imshow('Cat contour', im2)
                # cv2.imshow('Cat edge', edges)
                # cv2.imshow('Cat laplacian', laplacian)
                # cv2.imshow('Cat sobelx',sobelx)
                # cv2.imshow('Cat sobely', sobely)
                # cv2.imshow('Cat sobelabs', sobel_8u)
                # cv2.imshow('cropped cat'+str(iloop),cropped_cat)
                cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
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
