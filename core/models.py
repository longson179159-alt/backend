# Import necessary modules from Django
from django.db import models
from django.contrib.auth.models import User

# Import datetime helpers to handle time calculations
from datetime import timedelta
from django.utils import timezone


# ----------------------------
# Customer Profile Model
# ----------------------------
class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    daily_goal = models.IntegerField(default=120)

    is_paying_customer = models.BooleanField(default=False)

    paid_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {'Paying' if self.is_paying_customer == True else 'Free'}"
    
    def activate_monthly_payment(self):
        self.is_paying_customer = True

        self.paid_until = timezone.now() + timedelta(days=30)

        self.save()

        print(f"activated monthly payment!")
    
    def check_status(self):
        if self.paid_until:
            if self.paid_until <= timezone.now():
                self.is_paying_customer = False
                self.save()
                print("This is a expired account!")
            else:
                print(f"This a paying customer until {self.paid_until}")
        else:
            print("This is a free account")


class SystemTopics(models.Model):
    topic_name = models.CharField(max_length=100)

    def __str__(self):
        return self.topic_name
    
def upload_system_course_file(instance, filename):
    return f"system/{instance.topic_name}/{filename}"

class SystemCourses(models.Model):
    topic = models.ForeignKey(SystemTopics, on_delete=models.CASCADE)

    course_name = models.CharField(max_length=100)

    course_img_file = models.FileField(upload_to= upload_system_course_file, null=True, blank=True)

    def __str__(self):
        return f"{self.topic.topic_name} - {self.course_name}"

def upload_system_lesson_file(instance, filename):  
    return f"system/{instance.course.topic.topic_name}/{instance.course.course_name}/{filename}"
    

class SystemLessons(models.Model):
    course = models.ForeignKey(SystemCourses, on_delete=models.CASCADE)

    lesson_name = models.CharField(max_length=100)

    youtube_id = models.CharField(max_length=255, null=True, blank=True)

    text_file = models.FileField(upload_to=upload_system_lesson_file)
    
    youtube_start_time = models.FloatField(null=True, blank=True)

    youtube_duration = models.PositiveIntegerField(null=True, blank=True)


    lesson_img_file = models.FileField(upload_to=upload_system_lesson_file, null=True, blank=True)

    has_audio = models.BooleanField(default=False)

    audio_file = models.FileField(upload_to=upload_system_lesson_file, null=True, blank=True)

    has_timestamp = models.BooleanField(default=False)

    whisper_file = models.FileField(upload_to=upload_system_lesson_file, null=True, blank=True)

    timestamp_file = models.FileField(upload_to=upload_system_lesson_file, null=True, blank=True)

    def __str__(self):
        return f"{self.course.course_name} - {self.lesson_name}"

    



def upload_course_file(instance, filename):
    return f"{instance.user.username}/{filename}"
    
class Courses(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    system_course = models.ForeignKey(
        SystemCourses,
        on_delete= models.SET_NULL,
        null = True,
        blank= True
    )

    course_name = models.CharField(max_length=100)

    last_open_at = models.DateTimeField(null = True, blank=True)

    # is_system = models.BooleanField(default=False) # This field is not necessary because system courses are stored in SystemCourses model

    course_img_file = models.FileField(upload_to= upload_course_file, null = True, blank=True)

    def __str__(self):
        return self.course_name
    
def upload_lesson_file(instance, filename):
    return f"{instance.course.user.username}/{filename}"

class Lessons(models.Model):
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)

    system_lesson = models.ForeignKey(
        SystemLessons,
        on_delete= models.SET_NULL,
        null = True,
        blank=True
    )

    lesson_name = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add= True)

    last_open_at = models.DateTimeField(null = True, blank=True)

    # is_system_lesson = models.BooleanField(default=False) 


    text_file = models.FileField(upload_to=upload_lesson_file, null = True, blank=True)

    youtube_id = models.CharField(max_length=255, null = True, blank=True)

    youtube_start_time = models.FloatField(null = True, blank=True)

    youtube_duration = models.PositiveIntegerField(null= True, blank=True)


    lesson_img_file = models.FileField(upload_to=upload_lesson_file, null=True, blank=True)

    has_audio = models.BooleanField(default=False)

    audio_file = models.FileField(upload_to=upload_lesson_file, null=True, blank=True)

    has_timestamp = models.BooleanField(default=False)

    whisper_file = models.FileField(upload_to=upload_lesson_file, null=True, blank=True)

    timestamp_file = models.FileField(upload_to=upload_lesson_file, null=True, blank=True)

    def __str__(self):
        return self.lesson_name
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["course", 'lesson_name'], name= 'uniq_course_lesson_name')
        ]


class Words(models.Model):
    user = models.ForeignKey(User, on_delete= models.CASCADE)


    created_at = models.DateTimeField(auto_now_add=True)

    change_to_learn_at = models.DateTimeField(null=True, blank=True)  

    word_key = models.CharField(max_length=50)

    word_status = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.word_key}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'word_key'], name = "uniqu_words_word_word_key")
        ]
    
class Word_Meanings(models.Model):
    word = models.ForeignKey(Words, on_delete= models.CASCADE)

    meaning = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.word} - {self.meaning[:20]}"
    class Meta: 
        constraints = [
            models.UniqueConstraint(fields=['word', 'meaning'], name="uniq_word_word_meaning")
        ]
    

class Word_Tags(models.Model):
    word = models.ForeignKey(Words, on_delete=models.CASCADE)

    tag = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.word} - {self.tag}"
    
    class Meta: 
        constraints = [
            models.UniqueConstraint(fields= ['word', 'tag'], name="uniq_word_tag")
        ]

class Phrases(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    created_at = models.DateTimeField(auto_now_add=True)

    change_to_learn_at = models.DateTimeField(null=True, blank=True)

    phrase = models.CharField(max_length=100)

    phrase_status = models.IntegerField()

    def __str__(self):
        return f"{self.user.username} - {self.phrase}"
    
    class Meta:
        constraints= [
            models.UniqueConstraint(fields= ['user', 'phrase'], name = "uniq_phrase_user_phrase")
        ]

    
class Phrase_Meanings(models.Model):
    phrase = models.ForeignKey(Phrases, on_delete=models.CASCADE)

    meaning = models.CharField(max_length=500)

    def __str__(self):
        return f"{self.phrase} - {self.meaning[:20]}"
    
    class Meta:
        constraints= [
            models.UniqueConstraint(fields = ["phrase", "meaning"], name= "uniq_phrase_meaning")
        ]
    
class Phrase_Tags(models.Model):
    phrase = models.ForeignKey(Phrases, on_delete=models.CASCADE)

    tag = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.phrase} - {self.tag}"
    
    class Meta:
        constraints= [
            models.UniqueConstraint(fields = ['phrase', 'tag'], name = "uniq_phrase_tag")
        ]
