#!/usr/bin/env python3
import numpy as np
import cv2, os, psycopg, multiprocessing, time, os.path, re, queue, json, subprocess

cv2.setLogLevel(0)

def detect_motion(frame):
    contours, hierarchy = cv2.findContours(frame, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    motion_threshold = int((frame.shape[0] * 0.05) * (frame.shape[1] * 0.05))
    for contour in contours:
        contour_area = cv2.contourArea(contour)
        if contour_area > motion_threshold:
            x,y,w,h = cv2.boundingRect(contour)
            boxed_frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            boxed_frame = cv2.rectangle(boxed_frame,(x,y),(x+w,y+h),(0,255,0),10)
            return True, boxed_frame
    return False, None

def monitor_camera(camera_id, camera_url):
    background_subtractor = cv2.cuda.createBackgroundSubtractorMOG2(history=500, varThreshold = 16, detectShadows = True)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5,5))
    open_filter = cv2.cuda.createMorphologyFilter(cv2.MORPH_OPEN, cv2.CV_8UC1, kernel)
    close_filter = cv2.cuda.createMorphologyFilter(cv2.MORPH_CLOSE, cv2.CV_8UC1, kernel)
    
    capture = cv2.cudacodec.createVideoReader(camera_url)
    capture.set(cv2.cudacodec.ColorFormat_BGR)
    
    start_time = time.time()
    frame_counter = 0
    while True:
        ret, frame_gpu = capture.nextFrame()
        if frame_gpu is None:
            break
        
        frame_gpu = cv2.cuda.resize(frame_gpu, (1920, 1080))
        original_frame = frame_gpu.download()
        
        frame_gpu = background_subtractor.apply(frame_gpu, -1, None)
        fgmask = frame_gpu.download()
        
        retval, frame_gpu = cv2.cuda.threshold(frame_gpu, 128, 255, cv2.THRESH_BINARY)
        
        if frame_counter <= 10:
            frame_counter += 1
            continue
        
        open_filter.apply(frame_gpu, frame_gpu)
        close_filter.apply(frame_gpu, frame_gpu)
        
        despeckled = frame_gpu.download()
        
        motion, boxed_frame = detect_motion(frame_gpu.download())
        if motion:
            cv2.imwrite(F"{camera_id}_{frame_counter}.jpg", np.hstack([original_frame, cv2.cvtColor(fgmask, cv2.COLOR_GRAY2BGR), cv2.cvtColor(despeckled, cv2.COLOR_GRAY2BGR), boxed_frame]))
        
        frame_counter += 1

config = json.load(open("/etc/juniorgopher/config.json"))
db = psycopg.connect(config['db'])
c = db.cursor()
c.execute("SELECT id, url FROM cameras")
cameras = c.fetchall()
c.close()
db.close()

for camera_id, camera_url in cameras:
    print(camera_id, camera_url)
    p = multiprocessing.Process(target=monitor_camera, args=(camera_id, camera_url))
    p.start()
    
