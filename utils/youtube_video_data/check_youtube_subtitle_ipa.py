from yt_dlp import YoutubeDL
import webvtt

# get youtubetext from this url https://www.youtube.com/watch?v=rIoOSCcIkr8

import os
import glob
import json
import tempfile
import traceback
import html
def convert_time_stamp(time):
    parts= [float(t) for  t in time.split(":")]
    # seconds = hour_minute_second[0]*3600 + hour_minute_second[1]*60 + hour_minute_second[2]
    if len(parts) == 3:
        return round(parts[0] * 3600 + parts[1] * 60 + parts[2], 2)
    if len(parts) == 2:
        return round(parts[0] * 60 + parts[1], 2)

    return 0

def convert_text(text):
    # 1. Fix HTML entities like &gt; to >
    text = html.unescape(text)
    # 2. Remove speaker change symbols (>>)
    text = text.replace(">>", "")
    # 3. Clean up whitespace
    text = text.replace("\n", " ").strip()
    return text



def deduplicate_subtitles(captions):
    list_timestamp = []
    clean_lines = []
    last_line = ""

    for c in captions:
        text_norm = convert_text(c.text)

        # subtitles_lines.append(text_norm)
        
        if not text_norm:
            continue
        if text_norm == last_line:
            continue
        if last_line and text_norm.startswith(last_line):
            clean_lines[-1] = text_norm
            list_timestamp[-1]['end'] = convert_time_stamp(c.end)
            list_timestamp[-1]['text'] = text_norm
        else:
            clean_lines.append(text_norm)
            list_timestamp.append({
                "start": convert_time_stamp(c.start),
                "end": convert_time_stamp(c.end),
                "text": text_norm
            })
        
        last_line = text_norm
    
    subtitles_text = "\n".join(clean_lines)
    return subtitles_text, list_timestamp
            



# To get the professional (manual) subtitles when they exist,
# and strictly fall back to the auto-generated ones if they don't,
# the most reliable method using your current approach is to execute yt-dlp in a two-step process.


# add create time stamp in return
def check_youtube_created_text(url):
    # create a temporary directory to store downloaded subtitles
    with tempfile.TemporaryDirectory() as tmpdir:
        base_opts = {
            "skip_download": True,
            # "writesubtitles": True,
            # "writeautomaticsub": True,  
            "subtitlesformat": "vtt",
            "quiet": True,
            "no_warnings": True,
            "subtitleslangs": ["en"],
            "outtmpl": os.path.join(tmpdir, '%(title)s.%(ext)s'),  # ← THIS IS THE KEY
        }

        try: 
            # First, try to download professional subtitles
            yld_opts = {
                **base_opts,
                "writesubtitles": True,
                "writeautomaticsub": False,
            }
            with YoutubeDL(yld_opts) as ydl:
                info = ydl.extract_info(url, download=True)
            
            vtt_files = glob.glob(os.path.join(tmpdir, "*.vtt"))
            if vtt_files:
                print("Professional subtitles found and downloaded.")
            # if no professional subtitles, try to download auto-generated subtitles
            else :
                yld_opts = {
                    **base_opts,
                    "writesubtitles": False,
                    "writeautomaticsub": True,
                }
                with YoutubeDL(yld_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                print("No professional subtitles found. Auto-generated subtitles downloaded.")
            vtt_files = glob.glob(os.path.join(tmpdir, "*.vtt"))
            if not vtt_files:
                raise FileNotFoundError("No VTT subtitle file found")
            

            captions = webvtt.read(vtt_files[0])
            # list_timestamp = []
            # subtitles_lines = []
            # for c in captions:
            #     text_norm = convert_text(c.text)
            #     subtitles_lines.append(text_norm)
            #     list_timestamp.append({
            #         "start": convert_time_stamp(c.start),
            #         "end": convert_time_stamp(c.end),
            #         "text": text_norm
            #     })
                
            subtitles_text, list_timestamp = deduplicate_subtitles(captions)
            # subtitles_text = "\n".join(subtitles_lines)

        except Exception as e:
            traceback.print_exc()
            print(f"Error processing YouTube URL: {str(e)}")
            return None, None
            # return f"Error processing YouTube URL: {str(e)}"
    return subtitles_text, list_timestamp


if __name__ == "__main__":
    # url = "https://www.youtube.com/watch?v=rIoOSCcIkr8"
    # https://www.youtube.com/watch?v=pAeoJVXrZo4
    url = input("Enter YouTube URL: ")
    subtitles_text, list_timestamp = check_youtube_created_text(url)

    # write this text to txt file next to this script
    with open("subtitles_text.text", "w", encoding="utf-8") as f:
        f.write(subtitles_text)

    # write timestamp to json file
    with open("subtitles_timestamp.json", "w", encoding="utf-8") as f:
        json.dump(list_timestamp, f, ensure_ascii=False, indent=4)




