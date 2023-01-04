#!/usr/bin/env python3
import psycopg, os, os.path, jinja2, re

segment_pattern = re.compile('^(\d+).mp4$')
day_pattern = re.compile('^(\d+)$')

db = psycopg.connect(dbname="juniorgopher")

c = db.cursor()
c.execute("SELECT id, url FROM cameras")
cameras = c.fetchall()

#ensure the directories exist
for camera_id, camera_url in cameras:
    camera_segment_path = F"/var/lib/juniorgopher/segments/{camera_id}"
    os.makedirs(camera_segment_path, exist_ok=True)

# move segments into hierarchy to improve performance
for camera_id, camera_url in cameras:
    camera_segment_path = F"/var/lib/juniorgopher/segments/{camera_id}"
    for dirpath, dirnames, filenames in os.walk(camera_segment_path):
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

# insert into database
for camera_id, camera_url in cameras:
    camera_segment_path = F"/var/lib/juniorgopher/segments/{camera_id}"
    for day_entry in os.scandir(camera_segment_path):
        if day_entry.is_dir() and day_pattern.match(day_entry.name):
            for segment_entry in os.scandir(os.path.join(camera_segment_path, day_entry.name)):
                segment_match = segment_pattern.match(segment_entry.name)
                if segment_entry.is_file() and segment_match:
                    relative_path = os.path.join(day_entry.name, segment_entry.name)
                    c.execute("INSERT INTO segments(id, camera_id, start, relative_path) VALUES (gen_random_uuid(), %s, %s, %s) ON CONFLICT DO NOTHING",
                        (camera_id, datetime.datetime.utcfromtimestamp(int(segment_match.group(1))), relative_path))

db.commit()
