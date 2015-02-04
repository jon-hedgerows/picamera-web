#!/usr/bin/env python

from flask import Flask, render_template, Response, request
from camera_pi import Camera
from urlparse import urlparse
import random

app = Flask(__name__)

@app.route('/')
def index():
    """Camera home page."""
    links = [{'url': "/preview/", 'title': "Preview"},
             {'url': "/stop/", 'title': "Stop"},
             {'url': "/random/", 'title': "Random Number"}
            ]
    return render_template("home.html", title="Camera", links=links)


@app.route('/preview/')
def preview():
    """Preview the camera image"""
    netloc = urlparse(request.url).hostname
    cam.start_preview_stream()
    return render_template("preview.html", title="Preview", my_hostname=netloc)

@app.route('/stop/')
def stop_preview():
    """stop showing the camera preview"""
    cam.stop_preview_stream()
    return ""

def gen_stream():
    """Video streaming generator function."""
    while True:
        frame = cam.get_frame()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")


@app.route('/random/')
def random_route():
    template_data = {
        'title': 'Random Number',
        'content': '%f' % random.random()
    }
    return render_template("320simple.html", **template_data)


@app.route('/preview/video')
def video_feed():
    """renders an mjpeg video stream. Put this in the src attribute of an img tag."""
    cam.start_preview_stream()
    return Response(gen_stream(), mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == '__main__':
    cam = Camera()
    app.run(host='0.0.0.0', port=8080, debug=True)
