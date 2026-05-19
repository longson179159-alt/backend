from django.http import JsonResponse
from utils.handle_upload_text_file import create_lesson
from utils.extention import get_subtexts_and_subtimestamp
from utils.extract_data import get_lists_from_text, get_subtexts, validate_file_size
from utils.handle_upload_text_file import convert_input_to_text
from django.views.decorators.csrf import csrf_exempt
import json
from core.models import Lessons, Courses
import traceback  
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db import transaction

import requests
import os
from urllib.parse import urlparse

@login_required
def get_lesson(request):
    if request.method != "GET":
        return JsonResponse({"message" : "Invalid request!"}, status = 405)
    lesson_name = request.GET.get("lesson_name", "").strip()
    course_name = request.GET.get("course_name", "").strip()
    print("CONTENT_TYPE", request.content_type)
    print("GET", request.GET)
    print("USER", request.user)
    if not lesson_name or not course_name:
        return JsonResponse({"message": "Missing lesson name or course name!"}, status = 400)

    try:
        course = Courses.objects.get(user = request.user, course_name = course_name)
        lesson = Lessons.objects.get(course = course ,lesson_name=lesson_name)
        print("get lesson object :",  lesson.lesson_name)
        

        with lesson.text_file.open("rb") as f:
            raw = f.read()

            data = json.loads(raw.decode('utf-8'))
            list_ref = data["list_ref"]
            list_id = data["list_id"]
        lesson.last_open_at = timezone.now()
        lesson.save(update_fields=["last_open_at"])
        course.last_open_at = timezone.now()
        course.save(update_fields=["last_open_at"])
        lesson_data, list_sentences, Tags_Meanings, core_data = create_lesson(request, list_ref, list_id)

        list_timestamp = None
        if lesson.has_timestamp and lesson.timestamp_file and lesson.timestamp_file.name:
            with lesson.timestamp_file.open('rb') as f:
                raw = f.read()
                list_timestamp = json.loads(raw.decode('utf-8'))

        youtube_id = lesson.youtube_id if lesson.youtube_id else ""
        youtube_start_time = lesson.youtube_start_time if lesson.youtube_start_time else 0
        youtube_duration = lesson.youtube_duration if lesson.youtube_duration else 0

        # audio_url = lesson.audio_file.url if (lesson.has_audio and lesson.audio_file and lesson.audio_file.name) else ""
        youtube_data ={
            "youtube_id": youtube_id,
            "youtube_start_time": youtube_start_time,
            'youtube_duration': youtube_duration
        }
        #content as a python list
        return JsonResponse({
            "lesson_data": lesson_data,
            "list_sentences": list_sentences,
            "Tags_Meanings" : Tags_Meanings,
            "youtube_data": youtube_data,
            "core_data": core_data,
            "timestamp": list_timestamp 
        },  
        status = 200,
        json_dumps_params={"ensure_ascii": False},
        content_type="application/json; charset=utf-8",)
    

    except Exception as e:
        print("❌ Exception occurred:", e)
        traceback.print_exc()
        return JsonResponse({
            "message": f"There is a problem with getting lesson: {str(e)}"
        }, status=404)
    



@login_required
def delete_lesson(request):
    if request.method != 'POST':
        return JsonResponse({"message" : "Invalid request!"}, status = 405)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    data = json.loads(request.body.decode('utf-8') or '{}')
    lesson_name = data.get('lesson_name', '').strip()
    course_name = data.get('course_name', '').strip()
    if not lesson_name or not course_name:
        return JsonResponse({'message': f'Missing required fields'}, status = 400)

    try: 
        course = Courses.objects.get(user = request.user, course_name = course_name)
        lesson_obj = Lessons.objects.get(course = course, lesson_name = lesson_name)
        lesson_obj.delete()
        return JsonResponse({'message': f'Detele {lesson_name} successfully!' }, status = 200)
    except Exception as e:
        print("Exception occurred :", e)
        return JsonResponse({'message': f'There is a problem with deleting {lesson_name} lesson'}, status = 404)



def generate_unique_lesson_name(course_obj, basename):
    if not Lessons.objects.filter(course = course_obj, lesson_name = basename).exists():
        return  basename
    counter = 2
    while True:
        new_name = f"{basename}_{counter}"
        if not Lessons.objects.filter(course = course_obj, lesson_name = new_name).exists():
            return new_name       
        counter += 1

# Subfunciton one
def lesson_create_textfile(lesson, textFileName, subtext):
    list_ref, list_id = get_lists_from_text(subtext)
    json_dict = {'list_ref': list_ref, 'list_id': list_id}
    textFileBytes = json.dumps(json_dict, ensure_ascii=False, indent=2).encode('utf-8')
    textFile = ContentFile(textFileBytes)
    lesson.text_file.save(textFileName, textFile, save = True)


def lesson_create_timestamp(lesson, timestampFileName, listTimestamp):
    timestampFileBytes = json.dumps(
        listTimestamp,
        indent=2,
        ensure_ascii=False
    ).encode('utf-8')
    timestampFile = ContentFile(timestampFileBytes)
    lesson.timestamp_file.save(timestampFileName, timestampFile, save = True )

@csrf_exempt
@transaction.atomic
@login_required
def create_youtube_lesson(request):
    if request.method != "POST":
        return JsonResponse({"message" : "Invalid request !"}, status = 405) 
    
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    
    data = json.loads(request.body) 
    youtubeId = data.get('youtubeId', "").strip()
    lessonName = data.get('lessonName', "").strip()
    courseName = data.get('courseName', "").strip()
    youtubeGlobalTimestamp = data.get('youtubeGlobalTimestamp', [])
    language = data.get('language', 'en').strip()
    print("In youtube branch, useName : ", request.user.username)
    print("first subtitle : ", youtubeGlobalTimestamp[0].get('text', ''))
    if language != "English":
        return JsonResponse({"message": "Currently, only English lessons are supported."}, status=400)

    if not lessonName or not courseName or not youtubeId:
        return JsonResponse({"message": "Missing required fields"}, status = 400)

    
    course, created = Courses.objects.get_or_create(
        user = request.user,
        course_name = courseName,
        defaults= {'last_open_at': timezone.now()}
    )

    if not created:
        course.last_open_at = timezone.now()
        course.save(update_fields=['last_open_at'])

    
    try:
        youtubeListSubtexts, youtubeListSubtiemstamps = get_subtexts_and_subtimestamp(youtubeGlobalTimestamp, max_minutes=15)
    except Exception as e:
        print("Exception occurred while processing timestamps: ", e)
        return JsonResponse({
            "message": f"There is a error with processing youtube timestamps : {str(e)}"
        }, status = 500)
    

    try:
        if len(youtubeListSubtiemstamps) == 1:
            # check and generate unique lesson name
            lessonName = generate_unique_lesson_name(course, lessonName)
            # create new lesson
            lesson = Lessons.objects.create(
                course = course,
                lesson_name = lessonName, 
                youtube_id = youtubeId,
                has_timestamp = True,
                youtube_start_time = youtubeListSubtexts[0].get('start'),
                last_open_at = timezone.now()
            )

            # Save text file to lesson
            textFileName = youtubeId + '.json'
            subtext = youtubeListSubtexts[0].get('text')
            lesson_create_textfile(lesson, textFileName, subtext)

            # Save timestamp
            listTimestamp = youtubeListSubtiemstamps[0]
            timestampFileName = youtubeId + "_timestamp" + ".json"
            lesson_create_timestamp(lesson, timestampFileName, listTimestamp)
            return JsonResponse({
                "message": f"Create lesson {lessonName} successfully!",
                "lesson_name": lessonName,
                "course_name": courseName
            }, status = 200)
        else:
            for idx, item in enumerate(youtubeListSubtexts):
                youtubeStartTime = item.get("start")
                if idx == 0:
                    subLessonName = generate_unique_lesson_name(course, lessonName)
                    fristLessonName = subLessonName
                else:
                    basename = f'{lessonName} {idx + 1}'
                    subLessonName = generate_unique_lesson_name(course, basename)
                
                lesson_obj = Lessons.objects.create(
                    course = course,
                    lesson_name = subLessonName,
                    youtube_id = youtubeId,
                    youtube_start_time = youtubeStartTime,
                    has_timestamp = True,
                    last_open_at = timezone.now()
                )
                
                # Save textFile to the lesson
                textFileName = f'{youtubeId}_{idx}.json'
                subtext = item.get('text')
                lesson_create_textfile(lesson_obj, textFileName, subtext)

                # Save timestamp to the lesson
                timestampFileName = f'{youtubeId}_{idx}_timestamp.json'
                listTimestamp = youtubeListSubtiemstamps[idx]
                lesson_create_timestamp(lesson_obj, timestampFileName, listTimestamp)
            return JsonResponse({
                "message": f"Create lesson {lessonName} successfully!",
                "lesson_name": fristLessonName,
                "course_name": courseName
            }, status = 200)
    except Exception as e:
        print("Exception occurred while creating lesson: ", e)
        traceback.print_exc()
        return JsonResponse({
            "message": f"There is a error with creating lesson : {str(e)}"
        }, status = 500)


@csrf_exempt
@login_required
@transaction.atomic
def create_lesson_manually(request):
    if request.method != "POST":
        return JsonResponse({'message' : 'Invalid request !'}, status = 405)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    
    if request.content_type and "application/json" in request.content_type:
        try:
            data = json.loads(request.body.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return JsonResponse({"message": "Invalid JSON body"}, status=400)
    else:
        data = request.POST

    lessonName = (data.get("lessonName") or data.get("lesson_name") or "").strip()
    courseName = (data.get("courseName") or data.get("course_name") or "default").strip()
    inputText = (data.get("inputText") or data.get("input_text") or "").strip()
    language = (data.get("language") or "English").strip()
    print('useName :', request.user.username)
    print('inputText :', inputText)

    if language.lower() not in {"english", "en"}:
        return JsonResponse({"message": "Currently, only English lessons are supported."}, status=400)

    frontend_text_file = request.FILES.get("textfile")
    pictureFile = request.FILES.get("picture")

    if language.lower() not in {"english", "en"}:
        return JsonResponse({"message": "Currently, only English lessons are supported."}, status=400)


    if not lessonName or not courseName or (not inputText and not frontend_text_file):
        return JsonResponse({'message' : 'Missing necessary fields!'}, status = 400)

    course, created = Courses.objects.get_or_create(
        user = request.user,
        course_name = courseName,
        defaults= {'last_open_at': timezone.now()}
    )

    if not created:
        course.last_open_at = timezone.now()
        course.save(update_fields=['last_open_at'])
    

    try:
        if inputText:
            # print('debug get sub texts')
            listSubtexts = get_subtexts(inputText)
    
        else:
            if not validate_file_size(frontend_text_file): 
                return JsonResponse({'message': 'File size must be under 50MB'}, status = 400)
            text = convert_input_to_text(frontend_text_file)
            if not text.strip():
                return JsonResponse({'message': 'Uploaded file is empty'}, status=400)
            listSubtexts = get_subtexts(text)


        if len(listSubtexts) == 1:
            firstLessonName = generate_unique_lesson_name(course, lessonName)
            subtext = listSubtexts[0]

            lesson = Lessons.objects.create(
                course = course,
                lesson_name = firstLessonName, 
                last_open_at = timezone.now()
            )
            lesson_create_textfile(lesson, firstLessonName, subtext)


            if pictureFile:
                lesson.lesson_img_file.save(pictureFile.name, pictureFile, save = True)
            
            return JsonResponse({
                'message' : f'Create lesson {firstLessonName} successfully!',
                "lesson_name": firstLessonName,
                "course_name": courseName
            }, status = 200)

            
        else:
            for idx, subtext in enumerate(listSubtexts):

                basename = f'{lessonName} {idx + 1}'
                if idx == 0:
                    subLessonName = generate_unique_lesson_name(course, lessonName)
                    firstLessonName = subLessonName
                else:
                    basename = f'{lessonName} {idx + 1}'
                    subLessonName = generate_unique_lesson_name(course, basename)

                lesson_obj = Lessons.objects.create(
                    course = course,
                    lesson_name = subLessonName,
                    last_open_at = timezone.now()
                )

                lesson_create_textfile(lesson_obj, subLessonName, subtext)

                if pictureFile:
                    lesson_obj.lesson_img_file.save(pictureFile.name, pictureFile, save = True)

            return JsonResponse({
                'message' : f'Create lesson {lessonName} successfully!',
                "lesson_name": firstLessonName,
                "course_name": courseName
            }, status = 200)
        
    except Exception as e:
        print("Exception occurred while creating lesson: ", e)
        traceback.print_exc()
        return JsonResponse({
            "message": f"There is a error with creating lesson : {str(e)}"
        }, status = 500)
                
        
    except Exception as e:
        print('Exception occurred: ', e)
        # traceback.print_exc()
        return JsonResponse({'message': str(e)}, status = 500)
    

    
