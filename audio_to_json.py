import whisper  # type: ignore
import json
import os

model = whisper.load_model("small") 

audios = os.listdir("audios")

for audio in audios: 
    if("_" in audio):
        parts = audio.split("_")
        number = parts[0]
        
        # --- FIX START ---
        # Instead of just taking parts[1], we join everything after the number 
        # back together. This handles titles with multiple underscores.
        full_title_with_ext = "_".join(parts[1:])
        
        # Remove the .mp3 extension safely
        title = full_title_with_ext.replace(".mp3", "")
        # --- FIX END ---

        print(f"Processing: No. {number} | Title: {title}")
        
        result = model.transcribe(audio = f"audios/{audio}", 
                                  language="hi",
                                  task="translate",
                                  word_timestamps=False )
        
        chunks = []
        for segment in result["segments"]:
            chunks.append({
                "number": number, 
                "title": title, 
                "start": segment["start"], 
                "end": segment["end"], 
                "text": segment["text"]
            })
        
        chunks_with_metadata = {"chunks": chunks, "text": result["text"]}

        # Save to jsons folder
        os.makedirs("jsons", exist_ok=True)
        with open(f"jsons/{audio}.json", "w") as f:
            json.dump(chunks_with_metadata, f, indent=4)