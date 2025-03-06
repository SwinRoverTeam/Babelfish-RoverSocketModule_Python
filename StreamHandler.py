import subprocess

class Stream:
    __slots__ = ["id", "command", "process"]

    def __init__(self, id, command, process):
        self.id = id
        self.command = command
        self.process = process

class WebcamStreamHandler:
    def __init__(self):
        self.stream1 = Stream(0, "", 0)
        self.stream2 = Stream(1, "", 0)
    
    def getStream(self, streamNumber):
        match streamNumber:
            case 0:
                return self.stream1
            case 1:
                return self.stream2
            case _:
                print("Invalid stream number")
                return None

    def switch_camera(self, streamNumber, cameraNumber):
        print(f"Switching camera {cameraNumber} to stream {streamNumber}")
        requested_process = f"ffmpeg -f v4l2 -i /dev/video{cameraNumber} -c:v libx264 -preset ultrafast -tune zerolatency -f rtsp rtsp://0.0.0.0:8554/stream{streamNumber}"
        match streamNumber:
            case 0:
                if self.stream1.command == requested_process:
                    return # already running
                if (self.stream1.process) and self.stream1.process.poll() != 0:
                    self.stream1.process.terminate()
                self.stream1.command = requested_process
                parsed_requested_process = requested_process.split()
                self.stream1.process = subprocess.Popen(parsed_requested_process)

            case 1:
                if self.stream2.command == requested_process:
                    return # already running
                if (self.stream2.process) and self.stream2.process.poll() != 0:
                    self.stream2.process.terminate()
                self.stream2.command = requested_process
                parsed_requested_process = requested_process.split()
                self.stream2.process = subprocess.Popen(parsed_requested_process)
            case _:
                print("Invalid stream number")