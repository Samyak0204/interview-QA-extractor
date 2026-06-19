import os
import subprocess
import imageio_ffmpeg

def extract_audio(video_path, audio_path):
    if not os.path.exists(video_path):
        print(f"Video file not found: {video_path}")
        return False
    
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    command = [
        ffmpeg_exe,
        "-y",
        "-i", video_path,
        "-vn",
        "-f", "mp3",
        "-q:a", "2",
        audio_path
    ]

    print(f"Extracting audio from '{video_path}' to '{audio_path}'...")

    try:
        result = subprocess.run(command,
                                stdout=subprocess.DEVNULL, 
                                stderr=subprocess.DEVNULL, 
                                check=True)
        
        if result.returncode==0:
            print("Audio extraction completed successfully!")
            return True
    except subprocess.CalledProcessError as e:
        print(f"ffmpeg error during audio extraction: {e}")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False
    
if __name__ == "__main__":
    video_file = "test.mp4" 
    audio_file = "test_audio.mp3"

    success = extract_audio(video_file, audio_file)
    
    if success and os.path.exists(audio_file):
        print(f"Success! Audio file created at: {os.path.abspath(audio_file)}")
    else:
        print("Failed to extract audio.")