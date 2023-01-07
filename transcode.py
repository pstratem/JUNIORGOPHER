#!/usr/bin/env python3
import psycopg, os, os.path, re, queue, json, subprocess, heapq

config = json.load(open("/etc/juniorgopher/config.json"))
db = psycopg.connect(config['db'])

c = db.cursor()
c.execute("SELECT id, camera_id, day_start, relative_path FROM segments WHERE transcoded IS NULL ORDER BY start DESC LIMIT 1440")

for segment_id, camera_id, day_start, relative_path in c.fetchall():
    camera_segment_path = F"/var/lib/juniorgopher/segments/{camera_id}"
    day_start_path = os.path.join(camera_segment_path, str(int(day_start.timestamp())))
    transcoding_directory = os.path.join(day_start_path, "540p5")
    os.makedirs(transcoding_directory, exist_ok=True)
    segment_filename = os.path.basename(relative_path)
    priority_number = 1.0 / day_start.timestamp()
    result = subprocess.run(['/usr/bin/ffmpeg', '-y', '-vsync', '0', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda', '-i', os.path.join(day_start_path, segment_filename), '-vf', 'scale_cuda=960:540,fps=fps=5', '-an', '-c:v', 'hevc_nvenc', '-preset', 'p6', '-tune', 'hq', '-qmin', '0', '-g', '250', '-bf', '3', '-b_ref_mode', 'middle', '-temporal-aq', '1', '-rc-lookahead', '20', '-i_qfactor', '0.75', '-b_qfactor', '1.1', '-rc', 'vbr', '-cq', '23', os.path.join(transcoding_directory, segment_filename)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode == 0:
        c.execute("UPDATE segments SET transcoded=now() WHERE id=%s", (segment_id,))
        db.commit()

