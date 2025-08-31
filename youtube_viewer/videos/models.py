from django.db import models

class Video(models.Model):
    video_id = models.CharField(max_length=25, unique=True, primary_key=True)
    title = models.CharField(max_length=255, default='')

    def __str__(self):
        return self.title