import json

import traceback

def get_subtexts_and_subtimestamp(list_global_timestamp, max_minutes = 15):
    if not list_global_timestamp:
        raise ValueError("No timestamps provided to process.")

    if max_minutes <= 0:
        raise ValueError("max_minutes must be a positive number.")

    youtube_list_subtexts = []
    youtube_list_subtiemstamps = []
    indexcurrent_chuck = 0
    current_subtext_lines = []
    current_lesson_timestamp = []
    end_time_current_chuck = max_minutes * 60 * (indexcurrent_chuck + 1)
    start_current_chuck = list_global_timestamp[0]['start']


    for item in list_global_timestamp:
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
            indexcurrent_chuck += 1
            start_current_chuck = item['start']
            end_time_current_chuck = max_minutes * 60 * (indexcurrent_chuck + 1)

    if current_subtext_lines:
        youtube_list_subtexts.append({
            'text': '\n'.join(current_subtext_lines),
            'start': start_current_chuck
        })     


        youtube_list_subtiemstamps.append(current_lesson_timestamp)

    return youtube_list_subtexts, youtube_list_subtiemstamps


