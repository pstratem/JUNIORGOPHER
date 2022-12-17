#!/usr/bin/env python3
import cv2
import numpy as np
import time, os.path

background_subtractor = cv2.cuda.createBackgroundSubtractorMOG2(history=500, varThreshold = 16, detectShadows = True)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10,10))
open_filter = cv2.cuda.createMorphologyFilter(cv2.MORPH_OPEN, cv2.CV_8UC1, kernel)
close_filter = cv2.cuda.createMorphologyFilter(cv2.MORPH_CLOSE, cv2.CV_8UC1, kernel)

stream = cv2.cuda_Stream()
frame_gpu = cv2.cuda_GpuMat()
capture = cv2.cudacodec.createVideoReader("1667624710.mp4")

frame_counter = -1
while True:
    frame_counter += 1

    ret, frame = capture.nextFrame()
    if not ret:
        break

    frame = cv2.cuda.resize(frame, (1920, 1080))
    frame_gpu = background_subtractor.apply(frame, -1, None)

    # cant detect motion in the first frame
    if frame_counter <= 0:
        continue

    # despeckle
    open_filter.apply(frame_gpu, frame_gpu)
    close_filter.apply(frame_gpu, frame_gpu)

    non_zero = cv2.cuda.countNonZero(frame_gpu)

    if non_zero < 2500:
        continue

    frame = frame_gpu.download()

    contours, hierarchy = cv2.findContours(frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    motion_threshold = int((frame.shape[0] * 0.05) * (frame.shape[1] * 0.05))
    motion = False
    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area > motion_threshold:
            motion = True

    if motion and frame_counter > 0:
        print("{} {}".format(frame_counter, motion))

print(frame_counter)

