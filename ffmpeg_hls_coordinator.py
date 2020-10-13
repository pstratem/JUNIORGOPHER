#!/usr/bin/env python3
import psycopg2, os, os.path, stat, sys, subprocess, shlex

db = psycopg2.connect(dbname="juniorgopher")

c = db.cursor()
c.execute("SELECT id, url FROM cameras")
cameras = c.fetchall()

for camera_id, camera_url in cameras:
    camera_segment_path = F"/var/www/cameras/htdocs/"
    os.makedirs(camera_segment_path, exist_ok=True)
    pid_path = F"/run/juniorgopher"
    os.makedirs(pid_path, exist_ok=True)
    start_stop_daemon = F'/sbin/start-stop-daemon --start --background --make-pidfile --pidfile {pid_path}/{camera_id}.ffmpeg-hls.pid --exec /usr/bin/ffmpeg -- -i {camera_url} -c:v copy -an -max_muxing_queue_size 1024 -hls_time 1 -hls_list_size 5 -hls_delete_threshold 1 -hls_flags delete_segments {camera_segment_path}/{camera_id}.m3u8'
    subprocess.run(shlex.split(start_stop_daemon))

