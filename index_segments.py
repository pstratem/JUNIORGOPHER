#!/usr/bin/env python3
import psycopg, os, os.path, jinja2, re

segment_pattern = re.compile('(\d+).mp4')

db = psycopg.connect(dbname="juniorgopher")

c = db.cursor()
c.execute("SELECT id, url FROM cameras")
cameras = c.fetchall()

for camera_id, camera_url in cameras:
    camera_segment_path = F"/var/lib/juniorgopher/segments/{camera_id}"
    os.makedirs(camera_segment_path, exist_ok=True)
    for dirpath, dirnames, filenames in os.walk(camera_segment_path):
        # move segments into hierarchy to improve performance
        if dirpath == camera_segment_path:
            for filename in filenames:
                match = segment_pattern.match(filename)
                if not match:
                    continue
                timestamp = int(match.group(1))
                timestamp_truncated_to_day = timestamp - (timestamp % (3600 * 24))
                daily_timestamp_dirname = os.path.join(camera_segment_path, str(timestamp_truncated_to_day))
                os.makedirs(daily_timestamp_dirname, exist_ok=True)
                segment_path = os.path.join(dirpath, filename)
                new_segment_path = os.path.join(daily_timestamp_dirname, filename)
                os.rename(segment_path, new_segment_path)
