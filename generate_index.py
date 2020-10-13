#!/usr/bin/env python3
import psycopg2, os, os.path, jinja2

db = psycopg2.connect(dbname="juniorgopher")

c = db.cursor()
c.execute("SELECT id FROM cameras")
camera_ids = c.fetchall()

template = jinja2.Template("""<html>
    <head>
        <title>Cameras</title>
        <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    </head>
    <body>
      {% for camera_id in camera_ids %}
          <video name="camera_feed" controls autoplay muted id="{{ camera_id }}" src="{{ camera_id }}.m3u8" />
      {% endfor %}
<script>
  function fixCameraFeed(video) {
      if (Hls.isSupported()) {
        var hls = new Hls();
        hls.loadSource(video.src);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, function() {
          video.play();
        });
      }
      else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.addEventListener('loadedmetadata', function() {
          video.play();
        });
      }
  }
  var camera_feeds = document.getElementsByName('camera_feed')
  camera_feeds.forEach(fixCameraFeed)
</script>
    </body>
</html>""")

print(template.render(camera_ids=camera_ids))
