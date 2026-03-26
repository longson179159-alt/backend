from core.models import Words, Phrases, Word_Meanings, Phrase_Meanings, Lessons, Courses
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
import traceback
from django.core.paginator import Paginator
from django.core.paginator import EmptyPage, PageNotAnInteger
from utils.handle_upload_text_file import group_by_para_or_sentence

# sort quesries set by options: 1: alphabetical order, 2: reverse alphabetical order, 3: by date added (newest first))
def order_by_options(querieset, option , type):
    if type == 'words':
        if option == 1:
            return querieset.order_by("word_key")
        elif option == 2:
            return querieset.order_by("-word_key")
        else :
            return querieset.order_by("-created_at")
    else: 
        if option == 1:
            return querieset.order_by("phrase")
        elif option == 2:
            return querieset.order_by("-phrase")
        else :
            return querieset.order_by("-created_at")



def get_lesson_sets(lesson_obj,  list_all_phrases):
    found_phrases = []
    with lesson_obj.text_file.open('r') as f:
        data = json.load(f)
        list_ref = data["list_ref"]
        list_id = data["list_id"]

    list_words_in_lesson = []
    for word_idx,  item in enumerate(list_id):
        list_words_in_lesson.append({
            "word": list_ref[word_idx],
            "s_idx": item[2]
        })
    group_by_sentence = group_by_para_or_sentence(list_words_in_lesson, 's_idx')

    # Filter phrase in this text
    for items_in_sentence in group_by_sentence:
        sentence_list = [item['word'] for item in items_in_sentence]
        for phrase_list in list_all_phrases:
            if len(sentence_list) < len(phrase_list) :
                continue
            
            for i in range(len(sentence_list) - len(phrase_list) + 1):
                if sentence_list[i : i + len(phrase_list)] == phrase_list:
                    found_phrases.append(phrase_list)
                    break


    set_words = set(list_ref)
    set_phrases = set(' '.join(phrase_list) for phrase_list in found_phrases)

    total_words = len(list_ref)
    return set_words, set_phrases, total_words



@csrf_exempt
@login_required
def get_list_words_or_phrases(request):
    if request.method != 'GET':
        return JsonResponse({'message': 'Invalid request method!'}, status=405)
    
    if not request.user.is_authenticated:
        return JsonResponse({'eror': 'Authentication required'}, status=401)
    
    try:

        type = request.GET.get('type', "words")
        statuses = request.GET.getlist('statuses')
        statuses = [int(s) for s in statuses] if statuses else [1,2,3,4,5]
        selected_sort_option = int(request.GET.get('selectSortOption', 1))
        page_size = int(request.GET.get('pageSize', 25))
        current_page = int(request.GET.get('currentPage', 1))

        lesson_name = request.GET.get('lessonName', "")
        course_name = request.GET.get("courseName", "")

        
        # if not lesson_name and not course_name:
        if lesson_name and course_name:
            lesson_obj = Lessons.objects.get(course__user = request.user, course__course_name = course_name, lesson_name = lesson_name)
            if type == 'words':
                with lesson_obj.text_file.open('r') as f:
                    data = json.load(f)
                    list_ref = data["list_ref"]
                    set_words = set(list_ref)
                
                words_obj = Words.objects.filter(user = request.user, word_key__in = set_words, word_status__in = statuses).prefetch_related('word_meanings_set')
                words_ordered_obj = order_by_options(words_obj, selected_sort_option,type)

                paginator = Paginator(words_ordered_obj, page_size)
                page = paginator.get_page(current_page)

                list_words_data = [{
                    'word' : word_obj.word_key,
                    'status' : word_obj.word_status,
                    'showMeaning' : False,
                    'meaning' : "; ".join(m.meaning for m in word_obj.word_meanings_set.all())
                } for word_obj in page.object_list]

                return JsonResponse({
                    "listWordsData": list_words_data,
                    "hasNextPage": page.has_next(),
                    "hasPreviousPage": page.has_previous(),
                    "totalPages": paginator.num_pages
                }, status = 200)
            
            else: # if type == 'phrases'

                
                phrase_qs = Phrases.objects.filter(user = request.user, phrase_status__in = statuses).prefetch_related('phrase_meanings_set')
                status_phrase_dict = {ph.phrase : ph.phrase_status for ph in phrase_qs}
                list_all_phrases = [phrase.split() for phrase in status_phrase_dict.keys()]
                
                set_words, set_phrases, total_words = get_lesson_sets(lesson_obj, list_all_phrases)

                phrases_obj = Phrases.objects.filter(user = request.user, phrase__in = set_phrases, phrase_status__in = statuses).prefetch_related('phrase_meanings_set')
                phrases_ordered_obj = order_by_options(phrases_obj, selected_sort_option, type)

                paginator = Paginator(phrases_ordered_obj, page_size)
                page = paginator.get_page(current_page)
                list_phrase_data = [{
                    'word': phrase_obj.phrase,
                    'status': phrase_obj.phrase_status,
                    'showMeaning': False,
                    'meaning': '; '.join(m.meaning for m in phrase_obj.phrase_meanings_set.all()),
                } for phrase_obj in page.object_list]

                return JsonResponse({
                    "listPhrasesData": list_phrase_data,
                    "hasNextPage": page.has_next(),
                    "hasPreviousPage": page.has_previous(),
                    "totalPages": paginator.num_pages
                }, status = 200)

        else: # if not lesson_name and not course_name:
            if type == 'words':
                words_obj = Words.objects.filter(user = request.user, word_status__in = statuses).prefetch_related('word_meanings_set')

                words_ordered_obj = order_by_options(words_obj, selected_sort_option, type)

                paginator = Paginator(words_ordered_obj, page_size)
                page = paginator.get_page(current_page)


                list_words_data = [{
                    'word': word_obj.word_key,
                    'status': word_obj.word_status,
                    'showMeaning': False,
                    'meaning': '; '.join(m.meaning for m in word_obj.word_meanings_set.all()),
                } for word_obj in page.object_list]

                return JsonResponse({
                    'listWordsData' : list_words_data,
                    "hasNextPage": page.has_next(),
                    "hasPreviousPage": page.has_previous(),
                    "totalPages": paginator.num_pages,
                }, status = 200)


            else:
                    phrases_obj = Phrases.objects.filter(user = request.user, phrase_status__in = statuses).prefetch_related("phrase_meanings_set")

                    phrases_ordered_obj = order_by_options(phrases_obj, selected_sort_option, type)

                    paginator = Paginator(phrases_ordered_obj, page_size)
                    page = paginator.get_page(current_page)

                    list_phrase_data = [{
                        'word': phrase_obj.phrase,
                        'status': phrase_obj.phrase_status,
                        'showMeaning': False,
                        'meaning': '; '.join(m.meaning for m in phrase_obj.phrase_meanings_set.all()),
                    } for phrase_obj in page.object_list]

                    return JsonResponse({
                        "listPhrasesData": list_phrase_data,
                        "hasNextPage": page.has_next(),
                        "hasPreviousPage": page.has_previous(),
                        "totalPages": paginator.num_pages
                    }, status = 200)

    except Exception as e:
        print("❌ Exception occurred:", e)
        # traceback.print_exc()
        return JsonResponse({
            "message": f"There is a problem with getting lesson: {str(e)}"
        }, status=500)


