#!/usr/bin/env python3
import psycopg, os, os.path, jinja2, re, datetime, json

segment_pattern = re.compile('^(\d+).mp4$')
day_pattern = re.compile('^(\d+)$')

config = json.load(open("/etc/juniorgopher/config.json"))
db = psycopg.connect(config['db'])

c = db.cursor()
c.execute("SELECT id, url FROM cameras")
cameras = c.fetchall()

# insert into database
for camera_id, camera_url in cameras:
    camera_segment_path = os.path.join(config['cameras_segment_directory'], str(camera_id))
    #ensure the directories exist
    os.makedirs(camera_segment_path, exist_ok=True)
    for day_entry in os.scandir(camera_segment_path):
        day_match = day_pattern.match(day_entry.name)
        if day_entry.is_dir() and day_match:
            for segment_entry in os.scandir(os.path.join(camera_segment_path, day_entry.name)):
                segment_match = segment_pattern.match(segment_entry.name)
                if segment_entry.is_file() and segment_match:
                    relative_path = os.path.join(day_entry.name, segment_entry.name)
                    c.execute("INSERT INTO segments(id, camera_id, start, relative_path, day_start) VALUES (gen_random_uuid(), %s, %s, %s, %s) ON CONFLICT (camera_id, relative_path) DO UPDATE SET relative_path=EXCLUDED.relative_path, day_start=EXCLUDED.day_start", (camera_id, datetime.datetime.utcfromtimestamp(int(segment_match.group(1))), relative_path, datetime.datetime.utcfromtimestamp(int(day_match.group(1)))))
                    db.commit()

