#!/usr/bin/env python3
import psycopg2, os, os.path, stat, sys, subprocess, shlex

db = psycopg2.connect(dbname="juniorgopher")

c = db.cursor()
c.execute("SELECT id, url FROM cameras")
cameras = c.fetchall()

for camera_id, camera_url in cameras:
    camera_segment_path = F"/var/lib/juniorgopher/segments/{camera_id}"
    os.makedirs(camera_segment_path, exist_ok=True)
    pid_path = F"/run/juniorgopher"
    os.makedirs(pid_path, exist_ok=True)
    start_stop_daemon = F'/sbin/start-stop-daemon --start --background --make-pidfile --pidfile {pid_path}/{camera_id}.ffmpeg.pid --exec /usr/bin/ffmpeg -- -i {camera_url} -use_wallclock_as_timestamps 1 -c:v copy -an -f segment -strftime 1 -segment_time 60 -segment_format mp4 {camera_segment_path}/%s.mp4'
    subprocess.run(shlex.split(start_stop_daemon))

