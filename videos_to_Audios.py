import os
import subprocess

VIDEO_DIR = "videos"
AUDIO_DIR = "audios"

os.makedirs(AUDIO_DIR, exist_ok=True)

for file in os.listdir(VIDEO_DIR):
    if not file.endswith(".mp4"):
        continue

    try:
        if "#" in file:
            tutorial_number = file.split("#")[1].split(".")[0]
        else:
            tutorial_number = "unknown"

        file_name = file.split(" _")[0]

        input_path = os.path.join(VIDEO_DIR, file)
        output_path = os.path.join(AUDIO_DIR, f"{tutorial_number}_{file_name}.mp3")

        print(f"Converting: {file} → {output_path}")

        result = subprocess.run(
            ["ffmpeg", "-i", input_path, output_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Error converting {file}")
            print(result.stderr)

    except Exception as e:
        print(f"Failed on {file}: {e}")