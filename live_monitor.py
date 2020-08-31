#!/usr/bin/env python3
import cv2 as cv
import numpy as np
import psycopg2, multiprocessing, time, os.path

def despeckle(threshold_image):
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (int(threshold_image.shape[0] * 0.003), int(threshold_image.shape[1] * 0.003)))
    dilate_image = cv.dilate(threshold_image, kernel)
    erode_image = cv.erode(dilate_image, kernel)
    return erode_image

def monitor_camera(camera_id, camera_url):
    background_subtractor = cv.createBackgroundSubtractorMOG2()
    capture = cv.VideoCapture(camera_url)

    if not capture.isOpened:
        print('Unable to open capture')
        return

    start_time = time.time()
    frame_rate = capture.get(cv.CAP_PROP_FPS)
    camera_fgmasks_path = F"/var/lib/juniorgopher/fgmasks/{camera_id}"
    os.makedirs(camera_fgmasks_path, exist_ok=True)

    while True:
        ret, frame = capture.read()
        if frame is None:
            break

        frame_time = start_time + capture.get(cv.CAP_PROP_POS_MSEC) / 1000
        
        if (capture.get(cv.CAP_PROP_POS_FRAMES) % (frame_rate / 5)) == 0:
            foreground_mask = background_subtractor.apply(frame)
            ret, threshold_image = cv.threshold(foreground_mask, 250, 255, cv.THRESH_BINARY)
            despeckled_image = despeckle(threshold_image)

            if cv.countNonZero(despeckled_image) > int((frame.shape[0] * 0.005) * (frame.shape[1] * 0.005)):
                retval = cv.imwrite(os.path.join(camera_fgmasks_path, str(int(frame_time*1000)) + "a" + ".jpg"), frame)
                retval = cv.imwrite(os.path.join(camera_fgmasks_path, str(int(frame_time*1000)) + "b" + ".jpg"), foreground_mask)
                retval = cv.imwrite(os.path.join(camera_fgmasks_path, str(int(frame_time*1000)) + "c" + ".jpg"), threshold_image)
                retval = cv.imwrite(os.path.join(camera_fgmasks_path, str(int(frame_time*1000)) + "d" + ".jpg"), despeckled_image)
                

        if False:
            db = psycopg2.connect(dbname="juniorgopher")
            c = db.cursor()
            c.execute("SELECT id, url FROM cameras")
            cameras = c.fetchall()
            c.close()
            db.close()

db = psycopg2.connect(dbname="juniorgopher")
c = db.cursor()
c.execute("SELECT id, url FROM cameras")
cameras = c.fetchall()
c.close()
db.close()

for camera_id, camera_url in cameras:
    print(camera_id, camera_url)
    p = multiprocessing.Process(target=monitor_camera, args=(camera_id, camera_url))
    p.start()
    
