import cv2
import numpy as np
import glob

H = [[[]]]
for iloop, imagefile in zip(range(len(glob.glob("image/*.jpg"))), glob.glob("image/*.jpg")):
    # try:
    # load the input image and convert it to grayscale
    # image = cv2.imread("D:\Programmation\Python34\Sources\Images\image\cat_07.jpg")
    image = cv2.imread(imagefile)
    height, width = image.shape[:2]

    size_max = 1000
    if (height and width) > size_max:
        ratio = width / height
        if ratio > 1:
            f = size_max / width
        else:
            f = size_max / height
        image = cv2.resize(image, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    ret, thresh = cv2.threshold(gray, 127, 255, 0)
    # im2, contours, hierarchy = cv2.findContours(thresh,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    # edges = cv2.Canny(gray,50,100)
    # laplacian = cv2.Laplacian(gray,cv2.CV_64F)
    # sobelx = cv2.Sobel(gray,cv2.CV_64F,1,0,ksize=5)
    # sobely = cv2.Sobel(gray,cv2.CV_64F,0,1,ksize=5)

    # Output dtype = cv2.CV_64F. Then take its absolute and convert to cv2.CV_8U
    # sobelx64f = cv2.Sobel(gray,cv2.CV_64F,1,0,ksize=5)
    # abs_sobel64f = np.absolute(sobelx64f)
    # sobel_8u = np.uint8(abs_sobel64f)

    # load the cat detector Haar cascade, then detect cat faces
    # in the input image
    detector = cv2.CascadeClassifier("cat_cascade.xml")
    rects = detector.detectMultiScale(gray, scaleFactor=1.25, minNeighbors=10, minSize=(75, 75))

    # loop over the cat faces and draw a rectangle surrounding each
    delta = 0
    if len(rects) > 0:

        for (i, (x, y, w, h)) in enumerate(rects):
            # cv2.circle(image,(int(x+w/2),int(y+h/2)),1,(255,255,0))
            cropped_cat = image[y - delta:y + h - delta, x:x + w]
            hsvc = cv2.cvtColor(cropped_cat, cv2.COLOR_BGR2HSV)
            hist = cv2.calcHist([cropped_cat], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
            # normalize histogram and apply backprojection
            # cv2.normalize(hist,hist,0,255,cv2.NORM_MINMAX)
            # dst = cv2.calcBackProject([hsv],[0,1],hist,[0,180,0,256],1)
            # disc = cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(10,10))
            # cv2.filter2D(dst,-1,disc,dst)
        if len(H) == 1:
            try:
                print('Cat ref: ' + imagefile)
                H = hist
            except:
                None
        else:
            print(imagefile)
            compH = cv2.compareHist(H, hist, cv2.HISTCMP_CORREL)
            print(compH)
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
        cv2.imshow('cropped cat' + str(iloop), cropped_cat)
cv2.waitKey(0)
# except:
# None
