from django.urls import path
from django.contrib import admin
# from core.views.upload_audio import upload_audio, create_timestamp
from core.views.auth import register_user, login_user, jwt_login, jwt_refresh
from core.views.create_delete_course import create_course, delete_course
from core.views.get_create_delete_lesson import get_lesson, delete_lesson, create_youtube_lesson, create_lesson_manually
from core.views.upload_text_and_audio import upload_text, upload_audio
from core.views.update_word import update_word, finish_lesson
from core.views.caculate_specifications import  show_course_infos, get_list_courses, calculate_progress_data, get_data_courses_cards, get_data_lessons_cards
from core.views.review import get_list_words_or_phrases
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # auth path
    path("register/", register_user, name = 'signup'),
    path("login/", login_user, name = 'login'),
    path("jwt_login/", jwt_login, name = "jwt_login"),
    path("jwt_refresh/", jwt_refresh, name = "jwt_refresh"),

    # couser path
    path('create_course/', create_course, name = 'create_course'),
    path('delete_course/', delete_course, name = 'delete_course'),
    # Send data to hompage
    # path('continue_study/', get_data_cards, name='get_data_cards'),
    path('get_data_lessons_cards/', get_data_lessons_cards, name='get_data_lessons_cards'),
    path('get_data_courses_cards/', get_data_courses_cards, name='get_data_courses_cards'),
    path('show_course_infos/', show_course_infos, name='show_course_infos'),
    path('get_list_courses/', get_list_courses, name='get_list_courses'),
    path('get_progress_data/', calculate_progress_data, name = "calculate_progress_data"),

    # lesson path
    path("create_youtube_lesson/", create_youtube_lesson, name = "create_youtube_lesson"),
    path("create_lesson_manually/", create_lesson_manually, name = 'create_lesson_manually'),
    path("get_lesson/" , get_lesson, name= "get_lesson"),
    path('delete_lesson/', delete_lesson, name='delete_lesson'),

    #upload text and audio path
    path("upload_text/", upload_text, name = "upload_text"),
    path("upload_audio/", upload_audio, name="upload_audio"),

    # word path
    path("update_word/", update_word, name= "update_word" ),
    path("finish_lesson/",  finish_lesson, name= "finish_lesson" ),

    # review path
    path('get_list_words/', get_list_words_or_phrases, name = "get_list_words_or_phrases"),

    path("admin/", admin.site.urls)
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )