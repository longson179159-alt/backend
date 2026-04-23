# Import YoutubeDL class from yt-dlp (used to extract subtitles)
from yt_dlp import YoutubeDL

# Import webvtt to parse .vtt subtitle files
import webvtt

# json is used to save the final timestamps to a .json file
import json

# tempfile lets us create a temporary folder that auto-deletes
import tempfile

# os is used to build file paths safely
import os

import glob

import html

from django.conf import settings
 

import traceback
# from extract_data import get_lists_from_text

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
    text = text.replace(">>", "").strip()

    return text

def get_auto_generated_timestamp(captions):
    if not captions:
        raise ValueError("No captions provided to process.")
    # this function get timestamp by deduplicatiing the subtitle text
    list_global_timestamp = []
    current_end = convert_time_stamp(captions[0].end)
    current_start = 0
    current_text = convert_text(captions[0].text)

    
    for c in captions:

        text_norm = convert_text(c.text)
        if not text_norm:
            continue
        if '\n' in text_norm :
            current_start  = convert_time_stamp(c.start)
        else:
            current_end = convert_time_stamp(c.end)
            current_text = text_norm

            list_global_timestamp.append({
                "start": current_start,
                "end": current_end,
                "text": current_text,
            })

    return list_global_timestamp

def get_professinal_timestamp(captions):
    list_global_timestamp = []
    for c in captions:
        text_norm = convert_text(c.text)
        text_norm = text_norm.replace("\n", " ").strip()
        if not text_norm:
            continue
        list_global_timestamp.append({
            "start": convert_time_stamp(c.start),
            "end": convert_time_stamp(c.end),
            "text": text_norm
        })
    return list_global_timestamp




def get_subtexts_and_subtimestamp(list_timestamp, max_minutes = 15):
    # hard code her for check youtube 15 minutes
    if not list_timestamp:
        raise ValueError("No timestamps provided to process.")
    youtube_list_subtexts = []
    index_current_chuck = 0
    current_subtext_lines = []
    end_time_current_chuck = max_minutes * 60 * (index_current_chuck + 1)
    start_current_chuck = list_timestamp[0]['start']

    youtube_list_subtiemstamps = []
    current_lesson_timestamp = []

    for item in list_timestamp:
        if item['end'] <= end_time_current_chuck:
            current_subtext_lines.append(item['text'])
            current_lesson_timestamp.append(item)
        else:
            youtube_list_subtexts.append({
                'text': '\n'.join(current_subtext_lines),
                'start': start_current_chuck
            })

            youtube_list_subtiemstamps.append(current_lesson_timestamp)

            current_subtext_lines = [item['text']]
            current_lesson_timestamp = [item]
            index_current_chuck += 1
            start_current_chuck = item['start']
            end_time_current_chuck = max_minutes * 60 * (index_current_chuck + 1)

            current_lesson_timestamp


    if current_subtext_lines:
        youtube_list_subtexts.append({
            'text': '\n'.join(current_subtext_lines),
            'start': start_current_chuck
        })     


        youtube_list_subtiemstamps.append(current_lesson_timestamp)

    return youtube_list_subtexts, youtube_list_subtiemstamps





# To get the professional (manual) subtitles when they exist,
# and strictly fall back to the auto-generated ones if they don't,
# the most reliable method using your current approach is to execute yt-dlp in a two-step process.



def get_timestamp(url):
    # Create a temporary directory
    # Everything inside this folder will be deleted automatically
    with tempfile.TemporaryDirectory() as tmpdir:
        list_global_timestamp = []
        info = None
        vtt_files = []
        chosen_lang = "en"
        # yt-dlp configuration options
        base_opts  = {
            "skip_download": True,          # Do NOT download the video
            "subtitlesformat": "vtt",       # Force VTT format (important)
            "quiet": True,                  # Reduce console noise
            "no_warnings": True,
            "subtitleslangs": [chosen_lang],
            "outtmpl": os.path.join(tmpdir, "%(id)s.%(lang)s.%(ext)s"),
            "cookiefile": "/home/ec2-user/cookies.txt",
            # "js_runtimes": ["node:/usr/bin/node"],
            "js_runtimes": {
                "node": {
                    "path": "/usr/bin/node"
                }
            },
            "user_agent": "Mozilla/5.0",
            "sleep_requests": 1,

        }

        # if settings.IS_PROD:
        #     # base_opts["remote_components"] = ["ejs:github"]

        #     base_opts["cookiefile"] = "/home/ec2-user/cookies.txt"
            # base_opts["js_runtimes"] = {
            #     "node": {
            #         "path": "/usr/bin/node"
            #     }
            # }

   

        try:
            ydl_opts = {
                **base_opts,
                "writesubtitles": True,        # Try to download manual subtitles first
                "writeautomaticsub": False,     # Do NOT download auto-generated subtitles in this step
            }  

            with YoutubeDL(ydl_opts) as ydl:
                # Extract metadata AND download subtitles (because download=True)
                info = ydl.extract_info(url, download=True)  
            vtt_files = glob.glob(os.path.join(tmpdir, "*.vtt"))
            if vtt_files:
                print("Professional subtitles found and downloaded.")
                captions = webvtt.read(vtt_files[0])
                list_global_timestamp = get_professinal_timestamp(captions)
            else:
                ydl_opts = {
                    **base_opts,
                    "writesubtitles": False,       # Do NOT download manual subtitles in this step
                    "writeautomaticsub": True,     # Try to download auto-generated subtitles
                }

                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                vtt_files = glob.glob(os.path.join(tmpdir, "*.vtt"))
                if not vtt_files:
                    raise FileNotFoundError("No VTT subtitle file found")
                print("No professional subtitles found. Auto-generated subtitles downloaded.")

                captions = webvtt.read(vtt_files[0])
                list_global_timestamp = get_auto_generated_timestamp(captions)

            if not list_global_timestamp:
                raise ValueError("No valid subtitles found after processing VTT file.")
            youtube_list_subtexts, youtube_list_subtiemstamps = get_subtexts_and_subtimestamp(list_global_timestamp)
            return youtube_list_subtiemstamps, youtube_list_subtexts,  info['id'], info.get("title").strip()
        except Exception as e:
            traceback.print_exc()
            print(f"Error downloading subtitles: {e}")
            raise ValueError(f"Failed to download subtitles for the provided YouTube URL: {url}. Error: {e}")

    
    
 
def get_thumbnail_from_youtube_id(youtube_id):
    return f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"

if __name__ == "__main__":
    # url = "https://www.youtube.com/watch?v=rIoOSCcIkr8"
    # https://www.youtube.com/watch?v=pAeoJVXrZo4
    # https://www.youtube.com/watch?v=d9NZS2P_Va4
    url = input("Enter YouTube URL: ")

    list_time_stamp , json_dict, id, title = get_timestamp(url)
    print("title", title)
    with open(f"youtube.json", "w", encoding="utf-8") as f:
        json.dump(list_time_stamp, f, indent=2, ensure_ascii=False)
    with open(f"youtube_subtexts.json", "w", encoding="utf-8") as f:
        json.dump(json_dict, f, indent=2, ensure_ascii=False)

