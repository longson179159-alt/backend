from django.core.management.base import BaseCommand, CommandError
from core.models import SystemCourses, SystemLessons, SystemTopics, Courses, Lessons
from django.db import transaction


default_topics = ["Spirituality", 'Education', 'Self-help', 'Books']


class Command(BaseCommand):
    help = "Create system courses and lessons"

    def add_arguments(self, parser):
        parser.add_argument(
            '--topic',
            type=str,
            help='Topic name for the system course (e.g., Spirituality, Education, Self-help, Books)'
        )

        parser.add_argument(
            '--system_course',
            type=str,
            help='Course name for the system course (e.g., Course 1, Course 2, etc.)'
        )

        parser.add_argument(
            'username',
            type=str,   
            help='Username for the user to associate with the system course'
        )

        parser.add_argument(
            'add_course_or_lesson',
            type=str,
            choices=['course', 'lesson'],
            help='Specify whether to add a course or a lesson (e.g., "course" or "lesson")'
        )

        parser.add_argument(
            '--usercourse',
            type=str,
            help='Course name for the system user course'
        )

        parser.add_argument(
            '--lesson',
            type=str,
            help='Lesson name for the system lesson'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        
        topic = options['topic']
        system_course = options['system_course']
        username = options['username']
        add_course_or_lesson = options['add_course_or_lesson']
        user_course = options['usercourse']
        lesson_name = options['lesson']

        if not topic or not system_course or not add_course_or_lesson or not username:
            raise CommandError('Missing required arguments. Please provide --topic, --system_course, username, and add_course_or_lesson.')

        if topic not in default_topics:
            raise CommandError('Invalid topic name.')
        topic_obj, created = SystemTopics.objects.get_or_create(topic_name=topic)
        if created:
            self.stdout.write(self.style.WARNING(f'Topic "{topic}" just created.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Topic {topic} is valid.'))
    
        system_course_obj, new_system_course_created = SystemCourses.objects.get_or_create(course_name=system_course, topic=topic_obj)
        if new_system_course_created:
            self.stdout.write(self.style.SUCCESS(f'System course "{system_course}" created under topic "{topic}".'))
        else:
            self.stdout.write(self.style.WARNING(f'System course "{system_course}" already exists under topic "{topic}".'))


        if add_course_or_lesson == 'course':
            if not user_course:
                raise CommandError('Missing required argument --usercourse for adding a course. Please provide the user course name using --usercourse.')
        
            try: 
                user_course_obj = Courses.objects.get(user__username = username, course_name = user_course)

            except Courses.DoesNotExist:
                raise CommandError(f'User course "{user_course}" not found for user "{username}". Please provide a valid user course name using --usercourse.')
            

            # Start synchronization of lessons from user course to system course

            # Copy picture course_img_file from user course to system course if it exists
            if user_course_obj.course_img_file and not system_course_obj.course_img_file:
                system_course_obj.course_img_file.save(user_course_obj.course_img_file.name, user_course_obj.course_img_file.file, save=True)
                self.stdout.write(self.style.SUCCESS(f'Course image for system course "{system_course}" copied from user course "{user_course}".'))

            userLessons = Lessons.objects.filter(course = user_course_obj)
            for userLesson in userLessons:
                if userLesson.system_lesson:
                    raise CommandError(f'Lesson "{userLesson.lesson_name}" in user course "{user_course}" is already a system lesson. Please remove the system lesson flag from the user lesson before copying it to the system course.')
                
                if not  userLesson.text_file:
                # Copy text_file from user lesson to system lesson if it exists
                    raise CommandError(f'User lesson "{userLesson.lesson_name}" does not have a text file. Please ensure all user lessons have text files before copying them to the system course.')
                system_Lessons_obj, lesson_created = SystemLessons.objects.get_or_create(lesson_name = userLesson.lesson_name, course = system_course_obj)

                if not lesson_created:
                    raise CommandError(f'Lesson "{userLesson.lesson_name}" already exists in system course "{system_course}".')

                system_Lessons_obj.youtube_id = userLesson.youtube_id if userLesson.youtube_id else None

                system_Lessons_obj.text_file.save(userLesson.text_file.name, userLesson.text_file, save = True)
                

                
                system_Lessons_obj.youtube_start_time = userLesson.youtube_start_time if userLesson.youtube_start_time else None
                system_Lessons_obj.youtube_duration = userLesson.youtube_duration if userLesson.youtube_duration else None

                if userLesson.lesson_img_file:
                    system_Lessons_obj.lesson_img_file.save(userLesson.lesson_img_file.name, userLesson.lesson_img_file, save = True)

                if userLesson.has_audio and userLesson.audio_file:
                    system_Lessons_obj.has_audio = True
                    system_Lessons_obj.audio_file.save(userLesson.audio_file.name, userLesson.audio_file, save = True)

                if userLesson.has_timestamp and userLesson.timestamp_file:
                    system_Lessons_obj.has_timestamp = True
                    system_Lessons_obj.timestamp_file.save(userLesson.timestamp_file.name, userLesson.timestamp_file, save = True)

                system_Lessons_obj.save()

        elif add_course_or_lesson == 'lesson':
            if not user_course or not lesson_name:
                raise CommandError('Missing required arguments for adding a lesson. Please provide the user course name using --usercourse and the lesson name using --lesson.')
            
            try:       
                user_lesson_obj = Lessons.objects.get(course__user__username = username, course__course_name = user_course, lesson_name = lesson_name)
                if user_lesson_obj.system_lesson:
                    raise CommandError(f'Lesson "{lesson_name}" in user course "{user_course}" is already a system lesson. Please remove the system lesson flag from the user lesson before copying it to the system course.')
            except Lessons.DoesNotExist:
                raise CommandError(f'Lesson "{lesson_name}" not found in user course "{user_course}". Please provide a valid lesson name using --lesson.')

            system_lesson_obj, lesson_created = SystemLessons.objects.get_or_create(lesson_name = user_lesson_obj.lesson_name, course = system_course_obj)

            if not lesson_created:
                raise CommandError(f'Lesson "{lesson_name}" already exists in system course "{system_course}".')

            
            # Copy text_file from user lesson to system lesson if it exists
            system_lesson_obj.text_file.save(user_lesson_obj.text_file.name, user_lesson_obj.text_file, save = True)
           
            system_lesson_obj.youtube_id = user_lesson_obj.youtube_id if user_lesson_obj.youtube_id else None
            system_lesson_obj.youtube_start_time = user_lesson_obj.youtube_start_time if user_lesson_obj.youtube_start_time else None
            system_lesson_obj.youtube_duration = user_lesson_obj.youtube_duration if user_lesson_obj.youtube_duration else None
            

            if user_lesson_obj.lesson_img_file:
                system_lesson_obj.lesson_img_file.save(user_lesson_obj.lesson_img_file.name, user_lesson_obj.lesson_img_file, save = True)
            if user_lesson_obj.has_audio and user_lesson_obj.audio_file:
                system_lesson_obj.has_audio = True
                system_lesson_obj.audio_file.save(user_lesson_obj.audio_file.name, user_lesson_obj.audio_file, save = True)

            if user_lesson_obj.has_timestamp and user_lesson_obj.timestamp_file:
                system_lesson_obj.has_timestamp = True
                system_lesson_obj.timestamp_file.save(user_lesson_obj.timestamp_file.name, user_lesson_obj.timestamp_file, save = True)


            system_lesson_obj.save()
        else:
            self.stdout.write(self.style.ERROR('Invalid option for add_course_or_lesson. Please specify "course" or "lesson".'))     



# python manage.py system_import test@example.com course --topic Spirituality --system_course Buddhism --usercourse Buddhism
# python manage.py system_import test@example.com course --topic Spirituality --system_course 'Nas Daily' --usercourse 'Nas Daily'
# python manage.py system_import test@example.com course --topic Spirituality --system_course 'Nas Daily' --usercourse Buddhism

                
            

            
            

            



