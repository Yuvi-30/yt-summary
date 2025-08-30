from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .serializers import BlogPostSerializer, BlogGenerationRequestSerializer
from .models import BlogPost

from .views import (
    extract_video_id, 
    get_transcript_instant, 
    get_video_info_enhanced,
    generate_blog_instant,
    get_transcription_enhanced,
    generate_blog_from_transcription_enhanced
)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_blog_api(request):
    """REST API endpoint for blog generation"""
    serializer = BlogGenerationRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({'error': 'Invalid input', 'details': serializer.errors}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    yt_link = serializer.validated_data['link']
    
    try:
        video_id = extract_video_id(yt_link)
        if not video_id:
            return Response({'error': 'Invalid YouTube URL'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Method 1: Try fast generation with captions
        try:
            transcript = get_transcript_instant(yt_link)
            if transcript and len(transcript.strip()) > 100:
                try:
                    video_info = get_video_info_enhanced(yt_link)
                except:
                    video_info = {'title': 'Unknown Title', 'channel': 'Unknown Channel', 'duration': 'Unknown'}
                
                blog_content = generate_blog_instant(transcript, video_info)
                
                # Save to database
                new_blog_article = BlogPost.objects.create(
                    user=request.user,
                    youtube_title=video_info.get('title', 'Unknown Title'),
                    youtube_link=yt_link,
                    generated_content=blog_content,
                )
                
                return Response({
                    'success': True,
                    'content': blog_content,
                    'method': 'fast_captions',
                    'blog_id': new_blog_article.id,
                    'metadata': {
                        'title': video_info.get('title'),
                        'channel': video_info.get('channel'),
                        'duration': video_info.get('duration'),
                        'word_count': len(blog_content.split())
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            print(f"Fast method failed: {e}")
            
        # Method 2: Fallback to full transcription
        try:
            video_info = get_video_info_enhanced(yt_link)
            transcript_data = get_transcription_enhanced(yt_link)
            
            if not transcript_data or not transcript_data.get('text'):
                return Response({'error': 'No audio/transcript available'}, 
                              status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            blog_content = generate_blog_from_transcription_enhanced(transcript_data, video_info)
            
            # Save to database
            new_blog_article = BlogPost.objects.create(
                user=request.user,
                youtube_title=video_info.get('title', 'Unknown Title'),
                youtube_link=yt_link,
                generated_content=blog_content,
            )
            
            return Response({
                'success': True,
                'content': blog_content,
                'method': 'full_transcription',
                'blog_id': new_blog_article.id,
                'metadata': {
                    'title': video_info.get('title'),
                    'channel': video_info.get('channel'),
                    'duration': video_info.get('duration'),
                    'word_count': len(blog_content.split()),
                    'speakers_detected': len(transcript_data.get('speakers', {})),
                    'transcript_confidence': transcript_data.get('confidence', 0.95)
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({'error': f'Full transcription failed: {str(e)}'}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({'error': str(e)}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def blog_list_api(request):
    """REST API endpoint for listing user's blogs"""
    blogs = BlogPost.objects.filter(user=request.user).order_by('-created_at')
    serializer = BlogPostSerializer(blogs, many=True)
    return Response({
        'count': blogs.count(),
        'blogs': serializer.data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def blog_detail_api(request, pk):
    """REST API endpoint for blog details"""
    try:
        blog = BlogPost.objects.get(id=pk, user=request.user)
        serializer = BlogPostSerializer(blog)
        return Response(serializer.data)
    except BlogPost.DoesNotExist:
        return Response({'error': 'Blog not found'}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def blog_delete_api(request, pk):
    """REST API endpoint for deleting blogs"""
    try:
        blog = BlogPost.objects.get(id=pk, user=request.user)
        blog.delete()
        return Response({'message': 'Blog deleted successfully'}, 
                       status=status.HTTP_200_OK)
    except BlogPost.DoesNotExist:
        return Response({'error': 'Blog not found'}, 
                       status=status.HTTP_404_NOT_FOUND)