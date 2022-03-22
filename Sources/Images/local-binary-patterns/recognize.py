# USAGE
# python recognize.py --training images/training --testing images/testing

# import the necessary packages
from pyimagesearch.localbinarypatterns import LocalBinaryPatterns
from sklearn.svm import LinearSVC
from sklearn.svm import SVC
from imutils import paths
import argparse
import cv2
import os

# construct the argument parse and parse the arguments
# ap = argparse.ArgumentParser()
# ap.add_argument("-t", "--training", required=True,
# help="path to the training images")
# ap.add_argument("-e", "--testing", required=True, 
# help="path to the testing images")
# args = vars(ap.parse_args())

# initialize the local binary patterns descriptor along with
# the data and label lists
desc = LocalBinaryPatterns(24, 8)
data = []
labels = []
path = "D:\\Programmation\\Python36\\Sources\\Images\\local-binary-patterns\\images\\training\\jack2\\"
pathlist = os.listdir(path)
# args["training"]
# loop over the training images
for imagePath in pathlist:
    # load the image, convert it to grayscale, and describe it
    image = cv2.imread(path + imagePath)
    height, width = image.shape[:2]
    print(imagePath)
    size_max = 1000
    if (height and width) > size_max:
        ratio = width / height
        if ratio > 1:
            f = size_max / width
        else:
            f = size_max / height
        image = cv2.resize(image, None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    hist = desc.describe(gray)

    # extract the label from the image path, then update the
    # label and data lists
    labels.append(imagePath.split("/")[-1])
    data.append(hist)

# train a Linear SVM on the data
# model = LinearSVC(C=100.0, random_state=42, max_iter =1000)
model = SVC(C=1, gamma=2)
model.fit(data, labels)
print(model)

print('Trained...')
# # loop over the testing images
# for imagePath in paths.list_images(args["testing"]):
# # load the image, convert it to grayscale, describe it,
# # and classify it
# image = cv2.imread(imagePath)
# height, width = image.shape[:2]
# size_max = 1000
# if (height and width)>size_max:
# ratio = width/height
# if ratio>1:
# f = size_max/width
# else:
# f = size_max/height
# image = cv2.resize(image,None,fx=f,fy=f,interpolation = cv2.INTER_CUBIC)
# gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# hist = desc.describe(gray)
# prediction = model.predict(hist)[0]

# # display the image and the prediction
# cv2.putText(image, prediction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
# 1.0, (0, 0, 255), 1)
# cv2.imshow("Image", image)
# cv2.waitKey(0)

# capture from camera at location 0
cap = cv2.VideoCapture(0)
while True:
    ret, img = cap.read()
    try:
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
        hist = desc.describe(gray)
        prediction = model.predict(hist.reshape(1, -1))[0]
        cv2.putText(img, prediction, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 1)
    except:
        None
    key = cv2.waitKey(10)
    if key == 27:
        break
    cv2.imshow("Image", img)
cv2.destroyAllWindows()
cv2.VideoCapture(0).release()
