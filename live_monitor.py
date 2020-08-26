#!/usr/bin/env python3
import cv2 as cv
import psycopg2, multiprocessing, time, os.path

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
            print(camera_id, capture.get(cv.CAP_PROP_POS_FRAMES))
            
            fgMask = background_subtractor.apply(frame)
            retval = cv.imwrite(os.path.join(camera_fgmasks_path, str(frame_time) + ".jpg"), fgMask)

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
    
