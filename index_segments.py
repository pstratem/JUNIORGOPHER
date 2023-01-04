#!/usr/bin/env python3
import psycopg, os, os.path, jinja2, re, datetime

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
    for entry in os.scandir(camera_segment_path):
        segment_match = segment_pattern.match(entry.name)
        if entry.is_file() and segment_match:
            timestamp = int(segment_match.group(1))
            timestamp_truncated_to_day = timestamp - (timestamp % (3600 * 24))
            daily_timestamp_dirname = os.path.join(camera_segment_path, str(timestamp_truncated_to_day))
            os.makedirs(daily_timestamp_dirname, exist_ok=True)
            segment_path = os.path.join(camera_segment_path, entry.name)
            new_segment_path = os.path.join(daily_timestamp_dirname, entry.name)
            os.rename(segment_path, new_segment_path)

# insert into database
for camera_id, camera_url in cameras:
    camera_segment_path = F"/var/lib/juniorgopher/segments/{camera_id}"
    for day_entry in os.scandir(camera_segment_path):
        day_match = day_pattern.match(day_entry.name)
        if day_entry.is_dir() and day_match:
            for segment_entry in os.scandir(os.path.join(camera_segment_path, day_entry.name)):
                segment_match = segment_pattern.match(segment_entry.name)
                if segment_entry.is_file() and segment_match:
                    relative_path = os.path.join(day_entry.name, segment_entry.name)
                    c.execute("INSERT INTO segments(id, camera_id, start, relative_path, day_start) VALUES (gen_random_uuid(), %s, %s, %s, %s) ON CONFLICT (camera_id, relative_path) DO UPDATE SET relative_path=EXCLUDED.relative_path, day_start=EXCLUDED.day_start", (camera_id, datetime.datetime.utcfromtimestamp(int(segment_match.group(1))), relative_path, datetime.datetime.utcfromtimestamp(int(day_match.group(1)))))
db.commit()
