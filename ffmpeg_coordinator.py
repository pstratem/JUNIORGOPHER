#!/usr/bin/env python3
import psycopg, os, os.path, stat, sys, subprocess, shlex, json

config = json.load(open("/etc/juniorgopher/config.json"))
db = psycopg.connect(config['db'])

c = db.cursor()
c.execute("SELECT id, url FROM cameras")
cameras = c.fetchall()

for camera_id, camera_url in cameras:
    camera_segment_path = os.path.join(config['cameras_segment_directory'], str(camera_id))
    os.makedirs(camera_segment_path, exist_ok=True)
    pid_path = "/run/juniorgopher"
    os.makedirs(pid_path, exist_ok=True)
    start_stop_daemon = F'/sbin/start-stop-daemon --start --background --make-pidfile --pidfile {pid_path}/{camera_id}.ffmpeg.pid --exec /usr/bin/ffmpeg -- -i {camera_url} -c:v copy -an -f segment -strftime 1 -segment_time 60 -segment_format mp4 -movflags +faststart {camera_segment_path}/%s.mp4'
    subprocess.run(shlex.split(start_stop_daemon))

