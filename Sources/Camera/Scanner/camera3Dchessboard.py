# -*- coding: utf-8 -*-
import cv2
import numpy as np
import chessboard3D as chess


# import numpy.zeros_like as zeros_like
# import numpy.array as array


class Cameractrl3D():
    '''Control the Camera, calculate the position, mouvement, angle and scaling'''

    def __init__(self, camcorr, video_ch=1, distance_marker=30, mtx=[], dist=[], undis=1,
                 board_h=8, board_w=7, size=25,
                 folder='C:\\Users\\Technicien\\Desktop\\Programmation\\Python34\\Sources\\Camera\\Scanner\\chessboard\\'):
        self.distance_marker = distance_marker
        self.isrunning = False
        self.video_ch = video_ch
        self.mtx = mtx
        self.dist = dist
        self.camcorr = camcorr
        self.undis = undis
        self.board_h = board_h
        self.board_w = board_w
        self.size = size
        self.folder = folder
        self.chess = chess.Chessboard3D(self.mtx, self.dist, self.board_h, self.board_w, self.size)

    def startCamera(self):
        '''Start the camera'''
        self.cap = cv2.VideoCapture(self.video_ch)
        self.ret, self.old_frame = self.cap.read()
        if self.undis == 1:
            if self.mtx != [] or self.dist != []:
                self.old_frame = self.camcorr.undistortImage(self.old_frame, self.mtx, self.dist)
        self.mask_old = np.zeros_like(self.old_frame)
        self.isrunning = True

    def stopCamera(self):
        '''Stop the camera'''
        # Destroy windows, close the app
        cv2.destroyAllWindows()
        self.cap.release()
        self.isrunning = False

    def grabFrame(self):
        '''Grab, correct and search for colored objects'''
        # Recalculate an empty mask
        self.mask_old = np.zeros_like(self.old_frame)

        # Take each frame
        self.ret, self.frame = self.cap.read()
        if self.undis == 1:
            if self.mtx != [] or self.dist != []:
                self.frame = self.camcorr.undistortImage(self.frame, self.mtx, self.dist)

        return self.frame

    def getPos3D(self, drawimg=False, keep=False):
        '''Get the position'''
        self.frame, self.ptzero, self.points3D = self.chess.chessboard3D(self.frame, drawimg, keep)
        return self.points3D

    def getScale(self):
        '''Get the scaling factor'''
        return self.scale

    def displayImage(self):
        '''Display the image'''
        # self.img = cv2.add(self.frame, self.mask_old)
        cv2.imshow('img', self.frame)
        # cv2.moveWindow('img', 100, 200)

    def setIsRunning(self, isrunning):
        '''Set setIsRunning to check if the app is running'''
        self.isrunning = isrunning

    def getIsRunning(self):
        '''Get getIsRunning to check if the app is running'''
        return self.isrunning

    def waitForEscape(self):
        '''Check if Esc. key has been pressed to escape the app'''
        # Wait for a key pressed
        self.k = cv2.waitKey(10) & 0xFF
        # Esc. pressed, quit app
        if self.k == 27:
            self.isrunning = False
        else:
            self.isrunning = True
        return self.isrunning


if __name__ == "__main__":
    import cameraundistort as undis

    from mpl_toolkits.mplot3d import axes3d
    import matplotlib.pyplot as plt
    import numpy as np

    points3D = []
    running = True
    camcorr = undis.CameraUndistort()
    camcorr.setFolder(
        'C:\\Users\\502750516\\Documents\\Programmation\\Python_3\\Sources\\Camera\\Scanner\\chessboard\\')
    mtx, dist = camcorr.calibrate()
    cam = Cameractrl3D(camcorr, 0, 25, mtx, dist, 1, 6, 5, 25)
    cam.startCamera()
    while (running):
        cam.grabFrame()
        points3D = cam.getPos3D(True, True)
        cam.displayImage()
        running = cam.waitForEscape()
    cam.stopCamera()
    points3D = np.array(points3D)
    X = points3D[:, :, 0].reshape(1, -1)
    X = X[0]
    Y = points3D[:, :, 1].reshape(1, -1)
    Y = Y[0]
    Z = points3D[:, :, 2].reshape(1, -1)
    Z = Z[0]
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    # ax.plot_wireframe(X, Y, Z, rstride=10, cstride=10)
    ax.scatter(X, Y, Z, c='r', marker='o')
    ax.set_xlabel('X axis')
    ax.set_ylabel('Y axis')
    ax.set_zlabel('Z axis')
    plt.show()
