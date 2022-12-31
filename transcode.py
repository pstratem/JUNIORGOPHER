#!/usr/bin/env python3
import psycopg, os, os.path, re, queue, json, subprocess, heapq

transcoding_queue = queue.PriorityQueue()

segment_pattern = re.compile('^(\d+).mp4$')
day_start_pattern = re.compile('^(\d+)$')

config = json.load(open("/etc/juniorgopher/config.json"))
db = psycopg.connect(config['db'])

c = db.cursor()
c.execute("SELECT id, url FROM cameras")
cameras = c.fetchall()

def process_day_directory(day_start_path):
    transcoding_directory = os.path.join(day_start_path, "540p5")
    os.makedirs(transcoding_directory, exist_ok=True)

    transcoding_complete = set()
    for entry in os.scandir(transcoding_directory):
        if entry.is_file():
            if segment_pattern.match(entry.name):
                transcoding_complete.add(entry.name)

    for entry in os.scandir(day_start_path):
        match = segment_pattern.match(entry.name)
        if entry.is_file() and match:
            if not entry.name in transcoding_complete:
                priority_number = 1.0 / int(match.group(1))
                transcoding_queue.put((priority_number, day_start_path, entry.name, transcoding_directory))

for camera_id, camera_url in cameras:
    camera_segment_path = F"/var/lib/juniorgopher/segments/{camera_id}"
    os.makedirs(camera_segment_path, exist_ok=True)
    for entry in os.scandir(camera_segment_path):
        if entry.is_dir() and day_start_pattern.match(entry.name):
            process_day_directory(os.path.join(camera_segment_path, entry.name))

workers = dict()
worker_count = 8
for i in range(worker_count):
    workers[i] = None

while not transcoding_queue.empty():
    for i in range(worker_count):
        if transcoding_queue.empty():
            break
        if workers[i] is None or workers[i].poll() is not None:
            priority_number, day_start_path, segment_filename, transcoding_directory = transcoding_queue.get()
            workers[i] = subprocess.Popen(['/usr/bin/ffmpeg', '-y', '-vsync', '0', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda', '-i', os.path.join(day_start_path, segment_filename), '-vf', 'scale_cuda=960:540,fps=fps=5', '-an', '-c:v', 'hevc_nvenc', '-preset', 'p6', '-tune', 'hq', '-qmin', '0', '-g', '250', '-bf', '3', '-b_ref_mode', 'middle', '-temporal-aq', '1', '-rc-lookahead', '20', '-i_qfactor', '0.75', '-b_qfactor', '1.1', '-rc', 'vbr', '-cq', '23', os.path.join(transcoding_directory, segment_filename)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

