from django.db import models
from django.contrib.auth.models import User

class BlogPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    youtube_title = models.CharField(max_length=300)
    youtube_link = models.URLField()
    generated_content = models.TextField()
    
    
    # Enhanced fields (add these if they don't exist)
    channel_name = models.CharField(max_length=200, blank=True, default='')
    video_duration = models.CharField(max_length=20, blank=True, default='')
    word_count = models.IntegerField(default=0)
    transcript_confidence = models.FloatField(default=0.95)
    speakers_detected = models.IntegerField(default=1)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.youtube_title} - {self.user.username}"