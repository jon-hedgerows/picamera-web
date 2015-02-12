__author__ = "jon@hedgerows.org.uk"

import time
import picamera
import subprocess as sp
import threading


# pi camera:  usage of splitter_ports:
# 0 hd stream (h264, 1920x1080)
# 1 preview stream (h264, 862x480)
# 2 (hd video recording?)
# 3 (stills?)

class Camera:
    __shared_state = {}  # from the Borg pattern
    my_camera = None
    camera_lock = threading.Lock()  # a mutex lock to prevent the camera being initialised more than once at a time
    ffmpeg_preview = None  # ffmpeg process
    ffmpeg_live = None  # ffmpeg process

    def __init__(self, config):
        """create a camera object and set basic parameters"""
        self.__dict__ = self.__shared_state  # from the Borg pattern
        print "Camera.__init__():",
        # setup the _camera if it isn't already set up
        # acquire a lock without blocking - if we can't get the lock then someone else is initialising the
        # camera anyway, so we don't care
        have_lock = Camera.camera_lock.acquire(False)
        if have_lock:
            if not Camera.my_camera:
                print "new"
                Camera.my_camera = picamera.PiCamera()

                # camera setup
                Camera.my_camera.resolution = (1920, 1080)
                Camera.my_camera.rotation = 180
                Camera.my_camera.iso = 800
                Camera.my_camera.meter_mode = "matrix"

                # let camera warm up by starting the preview window in the pi itself
                Camera.my_camera.start_preview()
                time.sleep(2)

                # start streaming both the preview and the live streams
                self.start_preview_stream(config)
                self.start_live_stream(config)
            else:
                print "exists"
            # try to release the lock, but just carry on regardless
            try:
                Camera.camera_lock.release()
            finally:
                pass
        else:
            # well, we're stuck...
            print "failed to get lock, my_camera will exist soon"

    def __enter__(self):
        """called when you entering 'with Camera() as...'"""
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        """called when exiting 'with Camera() as...'"""
        pass

    def __del__(self):
        """close the camera properly"""
        # actually, don't close the camera - if we have multiple objects, then we only really
        # want the last deleted one to close the camera, but that's not implemented
        print "Camera.__del__():",
        if Camera.my_camera is not None:
            self.stop_live_stream()
            self.stop_preview_stream()
            Camera.my_camera.close()
        print "deleted"

    @staticmethod
    def set_resolution(resolution):
        Camera.my_camera.resolution = resolution

    @staticmethod
    def get_resolution():
        return Camera.my_camera.resolution

    @staticmethod
    def start_preview_stream(config):
        """start capturing a preview stream (to rtmp and hls)"""
        ffmpeg_command =\
            ['ffmpeg',
             '-f', 'h264', '-analyzeduration', '50', '-i', '-',
             '-an', '-c:v', 'copy',
             '-f', 'flv',
             '-rtmp_buffer', '100', '-rtmp_live', 'live', "rtmp://localhost/" + config['live_preview_rtmp_stream'],
             '-an', '-c:v', 'copy',
             '-f', 'hls',
             '-hls_time', '1', '-hls_list_size', '5', '-hls_wrap', '5',
             # TODO: remove the hard-coded url
             '-hls_base_url', 'http://pidad.hedgerows.org.uk:8080/static/live/preview/', config['live_preview_hls_folder']
             ]
        # start ffmpeg
        Camera.ffmpeg_preview = sp.Popen(ffmpeg_command, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
        # and start feeding ffmpeg with resized video
        Camera.my_camera.start_recording(Camera.ffmpeg_preview.stdin, format='h264',
                                         resize=config['live_preview_resolution'],
                                         splitter_port=1,
                                         # bitrate=config['live_preview_bps'],
                                         quality=27,
                                         intra_period=25*5, inline_headers=True)
        print "started preview stream"

    @staticmethod
    def start_live_stream(config):
        """start capturing an HD stream (to rtmp and hls)"""
        ffmpeg_command =\
            ['ffmpeg',
             '-f', 'h264', '-analyzeduration', '50', '-i', '-',
             '-an', '-c:v', 'copy',
             '-f', 'flv',
             '-rtmp_buffer', '100', '-rtmp_live', 'live', "rtmp://localhost/" + config['live_hd_rtmp_stream'],
             '-an', '-c:v', 'copy',
             '-f', 'hls',
             '-hls_time', '1', '-hls_list_size', '5', '-hls_wrap', '5',
             # TODO: remove the hard-coded url
             '-hls_base_url', 'http://pidad.hedgerows.org.uk:8080/static/live/hd/', config['live_hd_hls_folder']
             ]
        # start ffmpeg
        Camera.ffmpeg_preview = sp.Popen(ffmpeg_command, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE)
        # and start feeding ffmpeg with resized video
        Camera.my_camera.start_recording(Camera.ffmpeg_preview.stdin, format='h264',
                                         # resize=config['live_hd_resolution'],
                                         splitter_port=0,
                                         # bitrate=config['live_hd_bps'],
                                         quality=27,
                                         intra_period=25*5, inline_headers=True)
        print "started HD stream"

    @staticmethod
    def stop_preview_stream():
        """stop capturing the preview stream"""
        Camera.my_camera.stop_recording(splitter_port=1)
        Camera.ffmpeg_preview.terminate()


    @staticmethod
    def stop_live_stream():
        """stop capturing the live stream"""
        Camera.my_camera.stop_recording(splitter_port=0)
        Camera.ffmpeg_live.terminate()