import html
import json
from pathlib import Path

import webvtt

base_dir = Path(r"C:\Users\PC\Desktop\debug")
vtt_files = sorted(base_dir.glob("*.vtt"))
if not vtt_files:
    raise FileNotFoundError(f"No .vtt files found in {base_dir}")

vtt_path = vtt_files[0]
captions = webvtt.read(str(vtt_path))


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
    # text = text.replace("\n", " ").strip()
    return text
raw_timestamp = []
for caption in captions:
    text_norm = convert_text(caption.text)
    text_norm = text_norm.replace("\n", " ").strip()
    raw_timestamp.append({
        "start": convert_time_stamp(caption.start),
        "end": convert_time_stamp(caption.end),
        "text": text_norm,
    })
with open("raw.json", "w", encoding="utf-8") as f:
    json.dump(raw_timestamp, f, ensure_ascii=False, indent=4)


list_timestamp = []
last_line = convert_text(captions[0].text)
current_end = convert_time_stamp(captions[0].end)
current_start = 0
current_text = convert_text(captions[0].text)

for c in captions:

    text_norm = convert_text(c.text)
    last_line = text_norm
    if not text_norm:
        continue
    if '\n' in text_norm :
        current_start  = convert_time_stamp(c.start)
    else:
        current_end = convert_time_stamp(c.end)
        current_text = text_norm

        list_timestamp.append({
            "start": current_start,
            "end": current_end,
            "text": current_text,
        })

with open("rawdata.json", "w", encoding="utf-8") as f:
    json.dump(list_timestamp, f, ensure_ascii=False, indent=4)


