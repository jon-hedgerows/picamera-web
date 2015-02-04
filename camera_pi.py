__author__ = "jon@hedgerows.org.uk"

import time
import io
import threading
import picamera
import subprocess as sp
from lock_timeout import TimeoutLock


_camera_lock = TimeoutLock()


class Camera:
    #__shared_state = {}  # from the Borg pattern - all state is shared
    _camera = None  # object to hold a reference to the camera
    frame = None  # current frame is stored here by background thread
    PREVIEW_URL = 'rtmp://localhost/preview/live'  # rtmp url for preview stream
    ffmpegCommand = ['ffmpeg',
                     '-f', 'h264',
                     '-i', '-',
                     '-an',
                     '-c:v', 'copy',
                     '-f', 'flv',
                     '-rtmp_buffer', '100',
                     '-rtmp_live', 'live',
                     PREVIEW_URL]
    ffmpeg = None  # ffmpeg process

    def __init__(self):
        """create a camera object and set basic parameters"""
        print "Camera.__init__()"
        #self.__dict__ = self.__shared_state  # from the Borg pattern - all state is shared

        # setup the _camera if it isn't already set up
        with _camera_lock.acquire(2) as have_lock:
            if have_lock:
                if not Camera._camera:
                    print "                  - new"
                    Camera._camera = picamera.PiCamera()

                    # camera setup
                    Camera._camera.resolution = (1920, 1080)
                    Camera._camera.rotation = 180
                    # Camera._camera.hflip = True
                    # Camera._camera.vflip = True

                    # let camera warm up
                    Camera._camera.start_preview()
                    time.sleep(2)
                else:
                    print "                  - exists"
                    print "                    rotation = " + str(Camera._camera.rotation)
            else:
                # well, we're stuck...
                print "                  - failed to get lock, gave up"
                pass

    def __del__(self):
        """close the camera properly"""
        if Camera._camera is not None:
            Camera._camera.close()
        print "Camera() deleted"

    def get_frame(self):
        """return the most recent frame captured from the camera"""
        return self.frame

    def set_resolution(self, resolution):
        Camera._camera.resolution = resolution

    def get_resolution(self):
        return Camera._camera.resolution

    def start_preview_stream(self):
        """start capturing a preview stream (to rtmp)"""
        # start ffmpeg
        # ffmpeg = sp.Popen(ffmpegCommand, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
        ffmpeg = sp.Popen(self.ffmpegCommand, stdin=sp.PIPE, stdout=sp.PIPE)
        # and start feeding ffmpeg with video, resized to 426x240
        Camera._camera.start_recording(ffmpeg.stdin, format='h264', resize=(426, 240), splitter_port=1, bitrate=300000)

    @property
    def is_streaming(self):
        """returns 1 if currently streaming
        :rtype : int
        """
        return self.ffmpeg is not None

    def stop_preview_stream(self):
        """stop capturing the preview stream"""
        # self.ffmpeg.terminate()
        Camera._camera.stop_recording(splitter_port=1)
        # self.ffmpeg = None
