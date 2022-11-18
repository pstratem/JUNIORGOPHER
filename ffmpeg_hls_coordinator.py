#!/usr/bin/env python3
import psycopg, os, os.path, stat, sys, subprocess, shlex

db = psycopg.connect(dbname="juniorgopher")

c = db.cursor()
c.execute("SELECT id, url FROM cameras")
cameras = c.fetchall()

for camera_id, camera_url in cameras:
    camera_segment_path = F"/var/www/cameras/htdocs/"
    os.makedirs(camera_segment_path, exist_ok=True)
    pid_path = F"/run/juniorgopher"
    os.makedirs(pid_path, exist_ok=True)
    start_stop_daemon = F'/sbin/start-stop-daemon --start --background --make-pidfile --pidfile {pid_path}/{camera_id}.ffmpeg-hls.pid --exec /usr/bin/ffmpeg -- -i {camera_url} -c:v h264 -vf scale=1920:1080 -preset ultrafast -flags +cgop -g 30 -an -hls_time 1000ms -hls_list_size 10 -hls_delete_threshold 100 -hls_flags delete_segments {camera_segment_path}/{camera_id}.m3u8'
    subprocess.run(shlex.split(start_stop_daemon))

