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
    text = text.replace(">>", "")
    # 3. Clean up whitespace
    text = text.replace("\n", " ").strip()
    return text

def get_timestamp_by_deduplicating(captions):
    # this function get timestamp by deduplicatiing the subtitle text

    list_global_timestamp = []

    last_line = ""
    for c in captions:
        text_norm = convert_text(c.text)

        # subtitles_lines.append(text_norm)
        
        if not text_norm:
            continue
        if text_norm == last_line:
            continue
        if last_line and text_norm.startswith(last_line):

            list_global_timestamp[-1]['end'] = convert_time_stamp(c.end)
            list_global_timestamp[-1]['text'] = text_norm
        else:

            list_global_timestamp.append({
                "start": convert_time_stamp(c.start),
                "end": convert_time_stamp(c.end),
                "text": text_norm
            })
        
        last_line = text_norm

    
    list_global_timestamp = [{**item, 'sIdx': idx} for idx, item in enumerate(list_global_timestamp)]
    return  list_global_timestamp





# def get_subtexts_and_timestamp(caption):
#     list_time_stamp = []
#     current_subtext_lines = []
#     youtube_list_subtexts = []
#     current_lesson_time_stamp = []
#     index_current_chuck = 0
#     max_time_current_chuck = 15 * 60 * (index_current_chuck +1)
#     start_current_chuck = convert_time_stamp(caption[0].start)

#     for c in caption:
#         line_text = convert_text(c.text)

#         if convert_time_stamp(c.end) <= max_time_current_chuck:
#             current_subtext_lines.append(line_text)
#             current_lesson_time_stamp.append({
#                 'start': convert_time_stamp(c.start),
#                 'end': convert_time_stamp(c.end),
#                 'text' : line_text
#             })
#         else:
#             youtube_list_subtexts.append({
#                 'start': start_current_chuck,
#                 'text': '\n'.join(current_subtext_lines)
#             })

#             list_time_stamp.append(current_lesson_time_stamp)

#             current_subtext_lines = [line_text]
#             current_lesson_time_stamp = [{
#                 'start': convert_time_stamp(c.start),
#                 'end': convert_time_stamp(c.end),
#                 'text': line_text
#             }]
#             start_current_chuck = convert_time_stamp(c.start)
#             index_current_chuck += 1
#             max_time_current_chuck = 15 * 60 * (index_current_chuck +1)

         
    
#     if current_subtext_lines:
#         youtube_list_subtexts.append({
#             'start': start_current_chuck,
#             'text': '\n'.join(current_subtext_lines)
#         })

#         list_time_stamp.append(current_lesson_time_stamp)

#     return list_time_stamp, youtube_list_subtexts
def get_subtexts_and_subtimestamp(list_timestamp, max_minutes = 15):
    # hard code her for check youtube 15 minutes

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
        }

        if settings.IS_PROD:
            base_opts["cookiefile"] = "/home/ec2-user/cookies.txt"
            base_opts["js_runtimes"] = {
                "node": {
                    "path": "/usr/bin/node"
                }
            }


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

        except Exception as e:
            traceback.print_exc()
            print(f"Error downloading subtitles: {e}")

        captions = webvtt.read(vtt_files[0])
        list_global_timestamp = get_timestamp_by_deduplicating(captions)

        if not list_global_timestamp:
            raise ValueError("No valid subtitles found after processing VTT file.")
        youtube_list_subtexts, youtube_list_subtiemstamps = get_subtexts_and_subtimestamp(list_global_timestamp)
        # list_timestamp, youtube_list_subtexts = get_subtexts_and_timestamp(captions)

    # return list_timestamp, youtube_list_subtexts, info['id'], info.get("title").strip().replace(" ", "_")
    return youtube_list_subtiemstamps, youtube_list_subtexts,  info['id'], info.get("title").strip()
    


# def get_thumbnail_url(url):
#     ydl_opts = {
#         "quiet": True,
#         "no_warnings": True,

#         # We are not downloading anything
#         "skip_download": True,
#     }

#     if settings.IS_PROD:
#             ydl_opts["cookiefile"] = "/home/ec2-user/cookies.txt"
#             base_opts["js_runtimes"] = {
#                 "node": {
#                     "path": "/usr/bin/node"
#                 }
#             }
#     with YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=False)
#         return info.get("thumbnail")
    
def get_thumbnail_from_youtube_id(youtube_id):
    return f"https://img.youtube.com/vi/{youtube_id}/hqdefault.jpg"

if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=ePMDcfFO9cw"

    list_time_stamp , json_dict, youtube_list_subtiemstamps, id, title = get_timestamp(url)
    print("title", title)
    with open(f"youtube.json", "w", encoding="utf-8") as f:
        json.dump(list_time_stamp, f, indent=2, ensure_ascii=False)

