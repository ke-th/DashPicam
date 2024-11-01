import os
import time
import shutil
from picamera2 import Picamera2, MappedArray
from picamera2.encoders import H264Encoder
from datetime import datetime
import cv2

# Configuration
VIDEO_DIR = "./dashcam_videos"
VIDEO_DURATION = 300  # 5 minutes in seconds
STORAGE_THRESHOLD_MB = 500  # Minimum free space in MB before deleting old files

# Initialize Picamera2
picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": (1280, 720)})  # HD resolution
picam2.configure(video_config)

# Ensure video directory exists
os.makedirs(VIDEO_DIR, exist_ok=True)

def get_free_space_mb(directory):
    """Check free space in the given directory in MB."""
    total, used, free = shutil.disk_usage(directory)
    return free // (1024 * 1024)

def delete_oldest_video():
    """Delete the oldest video file in the directory to free up space."""
    files = sorted((f for f in os.listdir(VIDEO_DIR) if f.endswith(".h264")),
                   key=lambda x: os.path.getctime(os.path.join(VIDEO_DIR, x)))
    if files:
        os.remove(os.path.join(VIDEO_DIR, files[0]))
        print(f"Deleted oldest video: {files[0]}")

def apply_timestamp(request):
    """Overlay a timestamp on the video frame."""
    timestamp = time.strftime("%Y-%m-%d %X")
    colour = (0, 255, 0)  # Green color for text
    origin = (10, 30)     # Position of the text
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 1
    thickness = 2

    with MappedArray(request, "main") as m:
        cv2.putText(m.array, timestamp, origin, font, scale, colour, thickness)

def record_video():
    """Record a video with a timestamped filename using H.264 encoding."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(VIDEO_DIR, f"dashcam_{timestamp}.h264")
    print(f"Recording: {filename}")

    picam2.pre_callback = apply_timestamp  # Set the timestamp overlay function
    encoder = H264Encoder(bitrate=10000000)  # Set desired bitrate

    picam2.start_recording(encoder, filename)
    time.sleep(VIDEO_DURATION)  # Record for the specified duration
    picam2.stop_recording()
    print(f"Saved video: {filename}")

def manage_storage():
    """Check storage space and delete oldest files if below threshold."""
    free_space = get_free_space_mb(VIDEO_DIR)
    print(f"Free space: {free_space} MB")
    
    while free_space < STORAGE_THRESHOLD_MB:
        delete_oldest_video()
        free_space = get_free_space_mb(VIDEO_DIR)

def main():
    picam2.start(show_preview=True)  # Start the camera with preview
    try:
        while True:
            manage_storage()  # Check and manage storage before each recording
            record_video()    # Record a 5-minute video
            time.sleep(1)     # Short pause between recordings
    except KeyboardInterrupt:
        print("Dashcam stopped.")
    finally:
        picam2.stop()

if __name__ == "__main__":
    main()

