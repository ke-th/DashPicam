import os
import time
import shutil
from picamera2 import Picamera2, MappedArray
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
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
    files = sorted((f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")),
                   key=lambda x: os.path.getctime(os.path.join(VIDEO_DIR, x)))
    if files:
        os.remove(os.path.join(VIDEO_DIR, files[0]))
        print(f"Deleted oldest video: {files[0]}")

def add_overlay(request):
    """Adds a date and time overlay to the video frame."""
    with MappedArray(request, "main") as m:
        # Get the current time and format it
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Use PIL to draw the timestamp onto the frame
        img = Image.fromarray(m.array)
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()  # Use default font

        # Position the timestamp in the bottom-right corner
        text_position = (img.width - 200, img.height - 30)
        draw.text(text_position, timestamp, fill="white", font=font)
        
        # Apply the overlay back onto the MappedArray
        m.array[:, :, :] = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def record_video():
    """Record a video with a timestamped filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(VIDEO_DIR, f"dashcam_{timestamp}.mp4")
    print(f"Recording: {filename}")

    # Register the overlay function
    picam2.request_callback = add_overlay

    picam2.start_and_record_video(filename, duration=VIDEO_DURATION)
    print(f"Saved video: {filename}")

def manage_storage():
    """Check storage space and delete oldest files if below threshold."""
    free_space = get_free_space_mb(VIDEO_DIR)
    print(f"Free space: {free_space} MB")
    
    while free_space < STORAGE_THRESHOLD_MB:
        delete_oldest_video()
        free_space = get_free_space_mb(VIDEO_DIR)

def main():
    picam2.start()
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
