from rest_framework import serializers
from .models import BlogPost
from django.contrib.auth.models import User

class BlogPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogPost
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        
class BlogGenerationRequestSerializer(serializers.Serializer):
    link = serializers.URLField()
    
class BlogGenerationResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    content = serializers.CharField()
    method = serializers.CharField()
    metadata = serializers.DictField()