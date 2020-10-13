#!/usr/bin/env python3
import psycopg2, os, os.path, jinja2

db = psycopg2.connect(dbname="juniorgopher")

c = db.cursor()
c.execute("SELECT id FROM cameras")
camera_ids = c.fetchall()

template = jinja2.Template(open('index.html.jinga').read())

print(template.render(camera_ids=camera_ids))
