import numpy as np
import cv2
from matplotlib import pyplot as plt
import matplotlib.animation as animation

cap = cv2.VideoCapture(0)
# cap.set(3, 1280)
# cap.set(4, 720)
# cap.open("http://192.168.0.100/videostream.asf?user=A1-wearable&pwd=a1234567")
ret, img = cap.read()
# mask_old = np.zeros_like(old_frame)
f = plt.figure()
# graph1 = f.add_subplot(121)
# graph2 = f.add_subplot(122)
i = 0
while (1):
    # Take each frame
    ret, img = cap.read()
    # img = cv2.imread('messi5.jpg',0)

    # Histogram equalization
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(4, 4))
    l = clahe.apply(l)
    lab = cv2.merge((l, a, b))
    lab = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    img = lab

    height, width, channels = img.shape
    height_b = height / 2
    width_b = height_b
    # print(width)
    # print(height)
    h_in = height / 2 - height_b / 2
    h_out = height / 2 + height_b / 2
    w_in = width / 2 - width_b / 2
    w_out = width / 2 + width_b / 2
    img = img[h_in: h_out, w_in: w_out]
    if i == 0:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        dft = cv2.dft(np.float32(img), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        laplacian = cv2.Laplacian(img, cv2.CV_64F)
        magnitude_spectrum = 20 * np.log(cv2.magnitude(dft_shift[:, :, 0], dft_shift[:, :, 1]))
        # kernel = np.ones((5,5),np.float32)/25
        # magnitude_spectrum = cv2.filter2D(magnitude_spectrum,-1,kernel)

        magnitude_spectrum = cv2.bilateralFilter(magnitude_spectrum, 9, 75, 75)

        rows, cols = img.shape
        crow, ccol = rows / 2, cols / 2

        # create a mask first, center square is 1, remaining all zeros
        mask = np.zeros((rows, cols, 2), np.uint8)
        mask[crow - 10:crow + 10, ccol - 10:ccol + 10] = 1

        # apply mask and inverse DFT
        fshift = dft_shift * mask
        f_ishift = np.fft.ifftshift(fshift)
        img_back = cv2.idft(f_ishift)
        img_back = cv2.magnitude(img_back[:, :, 0], img_back[:, :, 1])
        # im = plt.imshow(magnitude_spectrum, cmap = 'gray')
        # ani = animation.FuncAnimation(f, img, interval=50, blit=True)
        # plt.show()
        # graph1.clear()
        # graph2.clear()
        # graph1.imshow(img, cmap = 'gray')
        # graph1.show()
        # plt.title('Input Image'), plt.xticks([]), plt.yticks([])
        # graph2.imshow(magnitude_spectrum, cmap = 'gray')
        # plt.title('Magnitude Spectrum'), plt.xticks([]), plt.yticks([])
        # graph2.show()
        # ani = animation.FuncAnimation(f, img, interval=50, blit=True)
        # ani2 = animation.FuncAnimation(graph2, magnitude_spectrum, interval=50, blit=True)
        # f.show()

        cv2.imshow('img', img)
        cv2.imshow('fft', magnitude_spectrum.astype(np.uint8))
        cv2.imshow('laplacian', laplacian)
        cv2.imshow('img_back', img_back.astype(np.uint8))
        aaa = cv2.sumElems(magnitude_spectrum.astype(np.uint8))
        print(aaa)
    i = i + 1
    if i == 1:
        i = 0

    # print(i)
    # wait(100)
    k = cv2.waitKey(30) & 0xFF
    # Esc. pressed, quit app
    if k == 27:
        break
        # "p" pressed, save image
    if k == ord('p'):
        cv2.imwrite("saved_current" + ".jpg", frame)
        cv2.imwrite("saved_current_data" + ".jpg", img)

# Destroy windows, close the app
cv2.destroyAllWindows()
cap.release()
