#!/usr/bin/env python3
import psycopg, os, os.path, jinja2, json

config = json.load(open("/etc/juniorgopher/config.json"))
db = psycopg.connect(config['db'])

c = db.cursor()
c.execute("SELECT id, url FROM cameras")
camera_ids = [camera_id for camera_id, camera_url in c.fetchall()]

template = jinja2.Template(open('index.html.jinga').read())

print(template.render(camera_ids=camera_ids))
