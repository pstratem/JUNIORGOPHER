#!/usr/bin/env python3
import psycopg2, os, os.path, stat, sys, subprocess, shlex

db = psycopg2.connect(dbname="juniorgopher")

c = db.cursor()
c.execute("SELECT id, url FROM cameras")
cameras = c.fetchall()

os.makedirs("/tmp/juniorgopher", exist_ok=True)
for camera_id, camera_url in cameras:
    pipe_path = F"/tmp/juniorgopher/{camera_id}"
    if not os.path.exists(pipe_path):
        os.mkfifo(pipe_path)
    elif not stat.S_ISFIFO(os.stat(pipe_path).st_mode):
        print(F"expected fifo at {pipe_path}, didn't get, continuing")
        continue
    os.makedirs(F"/var/lib/juniorgopher/{camera_id}", exist_ok=True)
    print(F'/usr/bin/ffmpeg -i {camera_url} -use_wallclock_as_timestamps 1 -c:v copy -an -f segment -strftime 1 -segment_time 60 -segment_format mp4 "/var/lib/juniorgopher/{camera_id}/%s.mp4" -c:v copy -an -f mpegts pipe:/tmp/juniorgopher/{camera_id}')
#    ffmpeg_subprocess = subprocess.Popen(shlex.split(F'/usr/bin/ffmpeg -i {camera_url} -use_wallclock_as_timestamps 1 -c:v copy -an -f segment -strftime 1 -segment_time 60 -segment_format mp4 "/var/lib/juniorgopher/{camera_id}/%s.mp4" -c:v copy -an -f mpegts pipe:/tmp/juniorgopher/{camera_id}.pipe'))
