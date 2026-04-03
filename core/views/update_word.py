from core.models import Words, Word_Tags, Word_Meanings, Phrase_Meanings, Phrase_Tags, Phrases
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
import json
from django.utils import timezone
import traceback
from django.db import transaction
from utils.extract_data import clean_word, is_valid_word, is_valid_phrase

def is_word(text):
    listWords = text.split()
    if len(listWords) == 1:
        return True
    else:
        return False
    


# @csrf_exempt
@login_required
@transaction.atomic
def update_word(request):
    if request.method != "PUT":
        return JsonResponse({"message" : "Invaid request method!"}, status=405)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    try:
        data = json.loads(request.body.decode("utf-8"))
        print('data text: ', data.get('phrase', ''))
        list_changes = data.get("changes", [])

        text = data.get('phrase', '')
        tags = list(set(data.get('tags', [])))
        your_meanings = list(set(data.get('your_meanings', [])))
        status = int(data.get("status", 0))


        if not text:
            return JsonResponse({"message": "Text is required"}, status=400)

        if is_word(text): 
            # check if it is a valid word, if not return error message
            if not is_valid_word(clean_word(text)):
                return JsonResponse({'message': "Invalid word"}, status=400)
            if status == 6:
                return JsonResponse({'message': "Can't add a word with status as 6"}, status = 401)
            word, created = Words.objects.get_or_create(user = request.user, word_key = text, defaults= {"word_status" : status})
            if created:
                print(f'Created {text} sucessfully')
            if "your_meanings" in list_changes:
                meanings_qs = Word_Meanings.objects.filter( word = word)
                meanings_qs.delete()
                for meaning in your_meanings:
                    Word_Meanings.objects.create(word = word, meaning = meaning )
                list_new_meanings = list(Word_Meanings.objects.filter(word = word).values_list("meaning", flat = True))
                print(f"Change meangings of {text} :", list_new_meanings)
            if "tags" in list_changes:
                tags_qs = Word_Tags.objects.filter(word = word)
                tags_qs.delete()
                for tag in tags:
                    Word_Tags.objects.create(word = word, tag = tag)
                list_new_tags = list(Word_Tags.objects.filter(word = word).values_list("tag", flat=True))
                print(f"Change tags of {text} :", list_new_tags)
            if "status" in list_changes:
                print(f"Change status {text} from {word.word_status} to {status}")
                if status == 0:
                    Word_Meanings.objects.filter(word = word).delete()
                    Word_Tags.objects.filter(word = word).delete()
                word.word_status = status
                
                if status == 4 or status == 5:
                    word.change_to_learn_at = timezone.now()
                word.save()
        else:
            # check if it is a valid phrase, if not return error messageif
            if not is_valid_phrase(text):
                return JsonResponse({'message': "Invalid phrase"}, status=400)
            if status == 0:
                Phrase_Meanings.objects.filter(phrase__user = request.user, phrase__phrase = text).delete()
                Phrase_Tags.objects.filter(phrase__user = request.user, phrase__phrase = text).delete()
                phrase_qs = Phrases.objects.filter(user = request.user, phrase = text)
               
                print(f"Delete {text}")
                phrase_qs.delete()
            elif status ==6:
                return JsonResponse({"message" : "there is no phrase having status 6"})
         
            else: 
                phrase, created = Phrases.objects.get_or_create(user= request.user, phrase = text, defaults= {"phrase_status" : status})
                if created:
                    print(f'Created {text} sucessfully')
                if "your_meanings" in list_changes:
                    Phrase_Meanings.objects.filter(phrase = phrase).delete()
                    for meaning in your_meanings:
                        Phrase_Meanings.objects.create(phrase = phrase, meaning = meaning)
                    list_new_meanings = list(Phrase_Meanings.objects.filter(phrase = phrase).values_list("meaning", flat=True))
                    print(f"Change meangings of {text} :", your_meanings)
                if "tags" in list_changes:
                    Phrase_Tags.objects.filter(phrase = phrase).delete()
                    for tag in tags:
                        Phrase_Tags.objects.create(phrase = phrase, tag = tag)
                    list_new_tags = list(Phrase_Tags.objects.filter(phrase = phrase).values_list("tag", flat= True))
                    print(f"Change tags of {text} :", list_new_tags)
                if "status" in list_changes:
                    print(f"Change status {text} from {phrase.phrase_status} to {status}")
                    phrase.phrase_status = status
                    if status == 4 or status == 5:
                        phrase.change_to_learn_at = timezone.now()
                    phrase.save()
    except Exception as e:
        print("❌ Exception occurred:", e)
        # traceback.print_exc()
        return JsonResponse({
            "message": f"There is a problem with getting lesson: {str(e)}"
        }, status=500)
    return JsonResponse({"message" : f"updated '{text}' sucessfull!"})


# @csrf_exempt
@login_required
def finish_lesson(request):
    if request.method != "PUT":
        return JsonResponse({"message": "Invalid method"}, status = 405)
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)
    data = json.loads(request.body.decode("utf-8"))
    list_words_update = []
    for key, value in data.items():  
        if not key:
            continue
        if len(key.split()) > 1 or value != 6 :
            continue
        Words.objects.update_or_create(user = request.user, word_key = key, defaults= {"word_status" : 5}, change_to_learn_at = timezone.now())
        list_words_update.append(key)
    

    return JsonResponse({"message": "Successfully updated word from this lesson!", "list_words_updated": list_words_update}, status = 200)









# def finish_lesson(request):
#     if request.method != "PUT":
#         return JsonResponse({"message": "Invalid request method!"}, status= 405)
#     data = json.loads(request.body.decode("utf-8"))
#     list_words_updated = []
#     for key, value in data.items():
#         if len(key.split()) >1 or value != 6:
#             continue
#         Words.objects.create(user = request.user, word_key =key,  word_status = 5)
#         list_words_updated.append(key)
        
#     return JsonResponse({"message": "updated all new words to knowned words", "list_words_updated": list_words_updated}, status=200)
    