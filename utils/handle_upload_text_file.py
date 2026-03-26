import os 
from ebooklib import epub
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from docx import Document
import chardet
import io
from core.models import Words, Phrases
from utils.extract_data import clean_word
import json
from utils.paths import BASE_DIR
import os


print('BASE_DIR', BASE_DIR)
dict_path = os.path.join(BASE_DIR, 'Dictionary.json')
with open(dict_path, 'r', encoding='utf-8') as file:
    Dict_data = json.load(file)

# ============================================================
# 1. Group words by paragraph index or sentence index
# ============================================================

def group_by_para_or_sentence(timestamp_word_level, group_type):
    """
    Group words by paragraph ('p_idx') or sentence ('s_idx') index.

    Args:
        timestamp_word_level (list): list of word objects with indexes
        group_type (str): key to group by ('p_idx' or 's_idx')

    Returns:
        list[list]: nested list of grouped words
    """
    words_in_the_same_type = []
    current_object = []
    current_idx = 0

    for word in timestamp_word_level:
        # Continue same group if index matches
        if word[group_type] == current_idx:
            current_object.append(word)
        else:
            # Start a new group
            if current_object:
                words_in_the_same_type.append(current_object)
            current_idx = word[group_type]
            current_object = [word]

    if current_object:
        words_in_the_same_type.append(current_object)

    return words_in_the_same_type

# def check_phrase_in_sentence(list_sentence, list_phrase):


def create_lesson(request, list_ref, list_id):
    list_words_in_lesson = []
    list_phrases_in_text = []

    # filter words queryset for words in list_ref to reduce time of query
    words_qs = Words.objects.filter(user = request.user, word_key__in = list_ref)
    status_word_dict = {w.word_key : w.word_status for w in words_qs}
    phrases_qs = Phrases.objects.filter(user = request.user)
    phrase_lists = [(ph.phrase.split() , ph.phrase_status) for ph in phrases_qs]
    
    # ---------------GET CORE DATA--------------
    for  word_idx, item in enumerate(list_id):
        list_words_in_lesson.append({
            "word" : item[0],
            "cleaned": list_ref[word_idx],
            "status" : status_word_dict.get(clean_word(item[0]), 6),
            'w_idx' : word_idx,
            "p_idx" : item[1],
            "s_idx" : item[2],
            "idx_w_in_s": item[3],
            "type" : 'word',
            "visible_in_phrase": True
        })


    core_data_group_by_para = group_by_para_or_sentence(list_words_in_lesson, "p_idx")
    # group by para, then group by sentence
    core_data_group_by_para_and_sentence = [group_by_para_or_sentence(item, "s_idx") for item in core_data_group_by_para]
    # ---------------GET LIST SENTENCE---------------
    group_by_sentence = group_by_para_or_sentence(list_words_in_lesson, "s_idx")
    list_sentences = []
    for items in group_by_sentence:
        list_words = [w['word'] for w in items]
        sentence = ' '.join(list_words)
        list_sentences.append(sentence)

    # ---------------GET LESSON DATA -----------------
    for sentence_idx,  items_in_sentence in enumerate(group_by_sentence):
        sentence_list = [clean_word(item.get("word")) for item in items_in_sentence]
        list_all_phrases = []

        # --------------get list of all phrase --------------
        for phrase_list, phrase_status in phrase_lists:

            if len(sentence_list) < len(phrase_list):
                continue

            for i in range(len(sentence_list) - len(phrase_list) + 1):
                if sentence_list[i: i + len(phrase_list)] == phrase_list:
                    list_phrases_in_text.append((' '.join(phrase_list), phrase_status))
                    chuck = [dict(w) for w in items_in_sentence[i:i+len(phrase_list)]] 
                    list_all_phrases.append({
                        "phrase": chuck,
                        "status": phrase_status,
                        "p_idx" : items_in_sentence[i]["p_idx"],
                        "s_idx": items_in_sentence[i]["s_idx"],
                        "type": "phrase",
                        "visible": True
                    })
        # ------------skip if there is no phrase in sentence ------------
        if len(list_all_phrases) == 0:
            continue

        #------------sort phrase according word start and length --------------
        list_phrase_sorted = sorted(
            list_all_phrases,
            key= lambda p: (p["phrase"][0]['idx_w_in_s'] , -len(p["phrase"]))
        )
        # print("list_all_phrases", list_phrase_sorted)

        # ------------ change status of phrase of word inside phrase-------------
        listPreviousPhraseIndexs = []
        for phrase in list_phrase_sorted:
            for word_in_phrase in phrase['phrase']:
                indexWord = word_in_phrase['idx_w_in_s']
                if indexWord in listPreviousPhraseIndexs:
                    word_in_phrase["visible_in_phrase"] = False                     
                else:
                    word_in_phrase["visible_in_phrase"] = True
                    listPreviousPhraseIndexs.append(indexWord)
            phrase['visible'] = any(w["visible_in_phrase"] == True for w in phrase["phrase"])

        # ---------------build new sentence data------------
        new_sentence_data = []
        index_last_item_in_previous_phrase = -1
        for phrase in list_phrase_sorted:
            list_word_before_current_phrase = [item for item in items_in_sentence if item["idx_w_in_s"] < phrase['phrase'][0]["idx_w_in_s"] and item["idx_w_in_s"] > index_last_item_in_previous_phrase]
            new_sentence_data.extend(list_word_before_current_phrase)
            index_last_item_in_previous_phrase = max(phrase["phrase"][-1]["idx_w_in_s"], index_last_item_in_previous_phrase)
            new_sentence_data.append(phrase)
        list_word = [item for item in items_in_sentence if item["idx_w_in_s"] > index_last_item_in_previous_phrase]
        new_sentence_data.extend(list_word)

        group_by_sentence[sentence_idx] = new_sentence_data
            

    list_words_in_lesson = []

    for items_in_sentence in group_by_sentence:
        list_words_in_lesson.extend(items_in_sentence)

    group_by_para = group_by_para_or_sentence(list_words_in_lesson, "p_idx")

    # ------------- GET TAGS, MEANINGS, STATUS------------------
    Tags_Meanings = {}
    for item in list_ref:
        word = Words.objects.filter(word_key = item, user = request.user).first()
        item_data_in_dict = Dict_data.get(item, {
            "global_tags": [],
            "global_meanings" : []
        })
        global_tags = item_data_in_dict["global_tags"]
        global_meanings = item_data_in_dict["global_meanings"]

  
        if not word:
            tags = []
            meanings = []
            
        else:
            meanings = list(word.word_meanings_set.values_list('meaning', flat= True))
            tags = list(word.word_tags_set.values_list('tag', flat = True))
        Tags_Meanings[item] = {
            'tags': tags,
            'your_meanings': meanings,
            'global_tags': global_tags,
            'global_meanings': global_meanings,
            'status': status_word_dict.get(item, 6)
        }
    for phrase_in_text, phrase_status in list_phrases_in_text:
        print(phrase_in_text)
        phrase = Phrases.objects.get(user = request.user, phrase = phrase_in_text)
        tags = list(phrase.phrase_tags_set.values_list('tag', flat = True))
        meanings = list(phrase.phrase_meanings_set.values_list('meaning', flat = True))
        Tags_Meanings[phrase_in_text] = {
            'tags' : tags,
            'your_meanings': meanings,
            'global_tags': [],
            'global_meanings': [],
            'status': phrase_status
        }
  

    return group_by_para, list_sentences, Tags_Meanings, core_data_group_by_para_and_sentence

# ---------- EPUB ----------     
def convert_epub_to_text(uploaded_file):
    uploaded_file.seek(0)

    book = epub.read_epub(io.BytesIO(uploaded_file.read()))
    texts = []
    for item in book.get_items():
        if item.get_type() == 9:
            soup = BeautifulSoup(item.get_body_content(), 'lxml')
            texts.append(soup.get_text())
    return "\n".join(texts)

# ---------- PDF ----------\
def convert_pdf_to_text(uploaded_file):
    uploaded_file.seek(0)
    text = extract_text(io.BytesIO(uploaded_file.read()))
    return text

# ---------- DOCX ----------
def convert_docx_to_text(uploaded_file):
    uploaded_file.seek(0)
    doc  = Document(io.BytesIO(uploaded_file.read()))
    return "\n".join([p.text for p in doc.paragraphs])

# ---------- TXT ----------
def convert_txt_to_text(uploaded_file):
    uploaded_file.seek(0)  
    raw_data = uploaded_file.read()
    encoding = chardet.detect(raw_data)["encoding"] or "utf-8"
    return raw_data.decode(encoding, errors="ignore")

def convert_input_to_text(uploaded_file):
    filename = uploaded_file.name
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".epub":
        content = convert_epub_to_text(uploaded_file)
    elif ext == ".pdf":
        content = convert_pdf_to_text(uploaded_file)
    elif ext == ".docx":
        content = convert_docx_to_text(uploaded_file)
    elif ext == ".txt":
        content = convert_txt_to_text(uploaded_file)
    else:
        raise ValueError(f"[⚠] Unsupported format: {ext}")
    print(f"[✔] Converted {ext} file → txt")
    return content




