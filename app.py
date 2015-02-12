#!/usr/bin/env python

from flask import Flask, render_template, request, url_for
from camera_pi import Camera
from urlparse import urlparse
import random
import os

app = Flask(__name__)

app.config.update(
    # urls and configuration for live streams
    live_hd_hls_static_url="live/hd/stream.m3u8",
    live_hd_hls_folder=os.path.join(app.static_folder, "live/hd/stream.m3u8"),
    live_hd_rtmp_stream="live/hd",
    live_hd_resolution=(1920, 1080),
    live_hd_bps=2500000,
    live_preview_hls_static_url="live/preview/stream.m3u8",
    live_preview_hls_folder=os.path.join(app.static_folder, "live/preview/stream.m3u8"),
    live_preview_rtmp_stream="live/preview",
    live_preview_resolution=(862, 480),
    live_preview_bps=300000,
)


@app.route('/')
def index():
    """Camera home page."""
    links = [{'url': "/preview/", 'title': "Preview"},
             {'url': "/live/", 'title': "Live HD"},
             {'url': "/start/", 'title': "Start"},
             {'url': "/stop/", 'title': "Stop"},
             {'url': "/random/", 'title': "Random Number"}
             ]
    return render_template("home.html", title="Camera", links=links)


@app.route('/preview/')
def preview():
    """Preview the camera image"""
    global cam
    global app
    url = urlparse(request.url)
    return render_template("video.html",
                           title="Preview",
                           my_hostname=url.hostname,
                           my_http_port=url.port,
                           stream_name=app.config["live_preview_rtmp_stream"],
                           width=app.config["live_preview_resolution"][0],
                           height=app.config["live_preview_resolution"][1],
                           hls_url=url_for("static", filename=app.config["live_preview_hls_static_url"]))


@app.route('/live/')
def live():
    """Preview the camera image"""
    global cam
    url = urlparse(request.url)
    return render_template("video.html",
                           title="Live",
                           my_hostname=url.hostname,
                           my_http_port=url.port,
                           stream_name=app.config["live_hd_rtmp_stream"],
                           width=app.config["live_hd_resolution"][0],
                           height=app.config["live_hd_resolution"][1],
                           hls_url=url_for("static", filename=app.config["live_hd_hls_static_url"]))


@app.route('/start/')
def start_streams():
    """start showing the camera streams"""
    global cam
    global app
    if cam is None:
        cam = Camera(app.config)
    cam.start_preview_stream(app.config)
    cam.start_live_stream(app.config)
    return ""


@app.route('/stop/')
def stop_streams():
    """stop showing the camera streams"""
    global cam
    if cam is None:
        cam = Camera(app.config)
    cam.stop_preview_stream()
    cam.stop_live_stream()
    return ""


@app.route('/random/')
def random_route():
    template_data = {
        'title': 'Random Number',
        'content': '%f' % random.random()
    }
    return render_template("320simple.html", **template_data)

if __name__ == '__main__':
    global cam
    with Camera(app.config) as cam:
        app.run(host='0.0.0.0', port=8080, debug=True, use_reloader=False)
