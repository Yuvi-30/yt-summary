# views.py
import json
import os
import re
import tempfile
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
import time
import shutil
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.conf import settings
import yt_dlp
import assemblyai as aai
import google.generativeai as genai
from dotenv import load_dotenv
from .models import BlogPost
from youtube_transcript_api import YouTubeTranscriptApi
from django.http import StreamingHttpResponse

# Load environment variables
load_dotenv()

@login_required
def index(request):
    return render(request, 'index.html')

# Configure APIs
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'login.html', {'error_message': 'Invalid credentials.'})
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        email = request.POST.get('email')
        password2 = request.POST.get('password2')

        if password1 == password2:
            try:
                user = User.objects.create_user(username=username, email=email, password=password1)
                user.save()
                login(request, user)
                return redirect('index')
            except Exception as e:
                return render(request, 'signup.html', {'error_message': str(e)})
        else:
            return render(request, 'signup.html', {'error_message': 'Passwords do not match.'})
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    return redirect('login')

# Add this new unified function to your views.py

@login_required
@csrf_exempt
def generate_blog_smart(request):
    """Smart blog generation - tries fast method first, falls back to full method"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
    try:
        data = json.loads(request.body)
        yt_link = data.get('link', '').strip()
        
        if not yt_link:
            return JsonResponse({'error': 'Please provide a YouTube link'}, status=400)
        
        video_id = extract_video_id(yt_link)
        if not video_id:
            return JsonResponse({'error': 'Invalid YouTube URL'}, status=400)
        
        # Method 1: Try fast generation with captions
        try:
            transcript = get_transcript_instant(yt_link)
            if transcript and len(transcript.strip()) > 100:  # Valid transcript
                video_info = get_video_info_enhanced(yt_link)
                blog_content = generate_blog_instant(transcript, video_info)
                
                # Save to database
                new_blog_article = BlogPost.objects.create(
                    user=request.user,
                    youtube_title=video_info.get('title', 'Unknown Title'),
                    youtube_link=yt_link,
                    generated_content=blog_content,
                )
                new_blog_article.save()
                
                return JsonResponse({
                    'success': True,
                    'content': blog_content,
                    'method': 'fast_captions',
                    'metadata': {
                        'title': video_info.get('title'),
                        'channel': video_info.get('channel'),
                        'duration': video_info.get('duration'),
                        'word_count': len(blog_content.split())
                    }
                })
                
        except Exception as e:
            print(f"Fast method failed: {e}")
            
        # Method 2: Fallback to full transcription
        try:
            video_info = get_video_info_enhanced(yt_link)
            transcript_data = get_transcription_enhanced(yt_link)
            
            if not transcript_data or not transcript_data.get('text'):
                return JsonResponse({'error': 'No audio/transcript available'}, status=500)
            
            blog_content = generate_blog_from_transcription_enhanced(transcript_data, video_info)
            
            # Save to database
            new_blog_article = BlogPost.objects.create(
                user=request.user,
                youtube_title=video_info.get('title', 'Unknown Title'),
                youtube_link=yt_link,
                generated_content=blog_content,
                channel_name=video_info.get('channel', ''),
                video_duration=video_info.get('duration', ''),
                word_count=len(blog_content.split()),
                transcript_confidence=transcript_data.get('confidence', 0.95)
            )
            new_blog_article.save()
            
            return JsonResponse({
                'success': True,
                'content': blog_content,
                'method': 'full_transcription',
                'metadata': {
                    'title': video_info.get('title'),
                    'channel': video_info.get('channel'),
                    'duration': video_info.get('duration'),
                    'word_count': len(blog_content.split()),
                    'speakers_detected': len(transcript_data.get('speakers', {})),
                    'transcript_confidence': transcript_data.get('confidence', 0.95)
                }
            })
            
        except Exception as e:
            return JsonResponse({'error': f'Full transcription failed: {str(e)}'}, status=500)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Fix the instant functions
def get_transcript_instant(link):
    """Get transcript using YouTube Transcript API"""
    try:
        video_id = extract_video_id(link)
        if not video_id:
            return None
            
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US'])
        return ' '.join([item['text'] for item in transcript_list])
    except Exception as e:
        print(f"Caption fetch failed: {e}")
        return None

def generate_blog_instant(transcript, video_info):
    """Fast blog generation with Gemini Flash"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Limit transcript to avoid token limits
        limited_transcript = transcript[:8000] if len(transcript) > 8000 else transcript
        
        prompt = f"""Create a well-structured blog article from this YouTube video transcript:

Title: {video_info.get('title', 'Video Analysis')}
Channel: {video_info.get('channel', 'YouTube')}

Transcript:
{limited_transcript}

Write a comprehensive blog article with:
- Engaging introduction
- Clear headings and subheadings  
- Key insights and takeaways
- Professional conclusion
- 500-800 words

Make it readable and engaging for a general audience."""
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        raise ValueError(f"Blog generation failed: {str(e)}")


# @login_required
# @csrf_exempt  
# def generate_blog_fast(request):
#     """Fast 2-second blog generation"""
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Invalid request method'}, status=405)
    
#     try:
#         data = json.loads(request.body)
#         yt_link = data.get('link', '').strip()
        
#         if not yt_link:
#             return JsonResponse({'error': 'Please provide a YouTube link'}, status=400)
        
#         video_id = extract_video_id(yt_link)
#         if not video_id:
#             return JsonResponse({'error': 'Invalid YouTube URL'}, status=400)
        
#         # Fast transcript
#         transcript = get_transcript_instant(yt_link)
#         if not transcript:
#             return JsonResponse({'error': 'No transcript available'}, status=500)
        
#         # Fast video info
#         video_info = {'title': f'Video Analysis', 'channel': 'YouTube'}
        
#         # Fast blog generation
#         blog_content = generate_blog_instant(transcript, video_info)
        
#         # Save to database
#         new_blog_article = BlogPost.objects.create(
#             user=request.user,
#             youtube_title=video_info.get('title', 'Unknown Title'),
#             youtube_link=yt_link,
#             generated_content=blog_content,
#         )
#         new_blog_article.save()
        
#         return JsonResponse({
#             'success': True,
#             'content': blog_content,
#             'method': 'fast_generation'
#         })
        
#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)



def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info_enhanced(link):
    """Get enhanced video information using yt-dlp"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            
            return {
                'title': info.get('title', 'Unknown Title'),
                'duration': format_duration(info.get('duration', 0)),
                'channel': info.get('uploader', 'Unknown Channel'),
                'description': info.get('description', '')[:300] + '...' if info.get('description') else '',
                'view_count': info.get('view_count', 0),
                'upload_date': info.get('upload_date', ''),
                'tags': info.get('tags', [])[:5]  # First 5 tags for SEO
            }
            
    except Exception as e:
        print(f"Error getting video info: {e}")
        return {'title': 'Unknown Title', 'channel': 'Unknown Channel'}

def format_duration(seconds):
    """Convert seconds to readable duration"""
    if not seconds:
        return "Unknown"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    else:
        return f"{minutes}m {secs}s"

def download_audio_enhanced(link):
    """Simplified audio download"""
    try:
        temp_dir = tempfile.mkdtemp()
        
        ydl_opts = {
            'format': 'worst[ext=mp4]',  # Use worst quality for speed
            'outtmpl': f'{temp_dir}/%(id)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            
            # Find downloaded file
            import glob
            files = glob.glob(f"{temp_dir}/*")
            if files:
                return files[0], temp_dir
                    
        return None, None
        
    except Exception as e:
        print(f"Audio download failed: {e}")
        return None, None

def get_transcription_enhanced(link):
    """Simplified transcription without advanced features"""
    try:
        if not os.getenv("ASSEMBLYAI_API_KEY"):
            raise ValueError("AssemblyAI API key not configured")
        
        # Download audio
        audio_file, temp_dir = download_audio_enhanced(link)
        if not audio_file:
            raise ValueError("Failed to download audio from video")
        
        try:
            # Basic transcription only
            config = aai.TranscriptionConfig(
                punctuate=True,
                format_text=True,
            )
            
            transcriber = aai.Transcriber(config=config)
            transcript = transcriber.transcribe(audio_file)
            
            if transcript.status == aai.TranscriptStatus.error:
                raise ValueError(f"Transcription failed: {transcript.error}")
            
            # Return simple transcript data
            return {
                'text': transcript.text or '',
                'highlights': [],
                'speakers': {},
                'sentiment': [],
                'entities': [],
                'confidence': 0.95
            }
            
        finally:
            # Clean up
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                
    except Exception as e:
        print(f"Transcription error: {e}")
        raise ValueError(f"Failed to get transcript: {str(e)}")

def generate_blog_from_transcription_enhanced(transcript_data, video_info):
    """Enhanced blog generation with video context and transcript insights"""
    try:
        if not os.getenv('GEMINI_API_KEY'):
            raise ValueError("Gemini API key not configured")
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Extract transcript components
        transcript_text = transcript_data.get('text', '')
        highlights = transcript_data.get('highlights', [])
        speakers = transcript_data.get('speakers', {})
        entities = transcript_data.get('entities', [])
        
        # Build enhanced prompt
        prompt = f"""
        Create a comprehensive, well-structured blog article based on this YouTube video content:

        VIDEO DETAILS:
        - Title: {video_info.get('title', 'Unknown')}
        - Channel: {video_info.get('channel', 'Unknown')}
        - Duration: {video_info.get('duration', 'Unknown')}
        - Description: {video_info.get('description', '')[:200]}

        TRANSCRIPT ANALYSIS:
        - Word Count: {len(transcript_text.split())} words
        - Speakers Detected: {len(speakers)} {"(Multi-speaker content)" if len(speakers) > 1 else "(Single speaker)"}
        - Key Entities: {', '.join([e.get('text', '') for e in entities[:5]])}

        KEY HIGHLIGHTS FROM AI ANALYSIS:
        {chr(10).join([f"• {h.get('text', '')}" for h in highlights[:8]])}

        FULL TRANSCRIPT:
        {transcript_text[:3000]}  # Limit for token efficiency

        INSTRUCTIONS:
        1. Create a professional blog article (NOT a video transcript)
        2. Use proper blog structure with engaging headings
        3. Include an compelling introduction and conclusion
        4. Incorporate the key highlights naturally
        5. Make it SEO-friendly with relevant keywords
        6. Write in a conversational yet professional tone
        7. Include 600-800 words
        8. Add subheadings to break up content

        BLOG STRUCTURE:
        - Compelling headline
        - Introduction hook
        - Main content sections with subheadings
        - Key takeaways section
        - Conclusion with call-to-action

        Generate a complete, publication-ready blog article:
        """
        
        response = model.generate_content(prompt)
        generated_content = response.text
        
        if not generated_content:
            raise ValueError("No content generated from Gemini")
        
        return generated_content
        
    except Exception as e:
        print(f"Blog generation error: {e}")
        raise ValueError(f"Failed to generate blog article: {str(e)}")



# @login_required
# @csrf_exempt
# def generate_blog(request):
#     """Enhanced blog generation with better error handling and features"""
#     if request.method != 'POST':
#         return JsonResponse({'error': 'Invalid request method'}, status=405)
    
#     try:
#         # Parse request data
#         data = json.loads(request.body)
#         yt_link = data.get('link', '').strip()
        
#         if not yt_link:
#             return JsonResponse({'error': 'Please provide a YouTube link'}, status=400)
        
#         # Validate URL format
#         video_id = extract_video_id(yt_link)
#         if not video_id:
#             return JsonResponse({'error': 'Invalid YouTube URL format'}, status=400)
        
#         # Ensure user is authenticated
#         if not request.user.is_authenticated:
#             return JsonResponse({'error': 'Authentication required'}, status=403)
        
#         # Step 1: Get enhanced video information
#         try:
#             video_info = get_video_info_enhanced(yt_link)
#         except Exception as e:
#             return JsonResponse({
#                 'error': f'Failed to fetch video information: {str(e)}'
#             }, status=500)
        
#         # Step 2: Get enhanced transcription
#         try:
#             transcript_data = get_transcription_enhanced(yt_link)
#             if not transcript_data or not transcript_data.get('text'):
#                 return JsonResponse({
#                     'error': 'Failed to get transcript. Video may not have audio or may be private.'
#                 }, status=500)
#         except Exception as e:
#             return JsonResponse({
#                 'error': f'Transcription failed: {str(e)}'
#             }, status=500)
        
#         # Step 3: Generate enhanced blog content
#         try:
#             blog_content = generate_blog_from_transcription_enhanced(transcript_data, video_info)
#             if not blog_content:
#                 return JsonResponse({
#                     'error': 'Failed to generate blog content'
#                 }, status=500)
#         except Exception as e:
#             return JsonResponse({
#                 'error': f'Blog generation failed: {str(e)}'
#             }, status=500)
        

#         try:
#             new_blog_article = BlogPost.objects.create(
#                 user=request.user,
#                 youtube_title=video_info.get('title', 'Unknown Title'),
#                 youtube_link=yt_link,
#                 generated_content=blog_content,
#                 channel_name=video_info.get('channel', ''),
#                 video_duration=video_info.get('duration', ''),
#                 word_count=len(blog_content.split()),
#                 transcript_confidence=transcript_data.get('confidence', 0.95)
#             )
#             new_blog_article.save()
            
#             # Return success response with metadata
#             return JsonResponse({
#                 'success': True,
#                 'content': blog_content,
#                 'metadata': {
#                     'title': video_info.get('title'),
#                     'channel': video_info.get('channel'),
#                     'duration': video_info.get('duration'),
#                     'word_count': len(blog_content.split()),
#                     'speakers_detected': len(transcript_data.get('speakers', {})),
#                     'transcript_confidence': transcript_data.get('confidence', 0.95)
#                 }
#             })
                
#         except Exception as e:
#             return JsonResponse({
#                 'error': f'Failed to save blog post: {str(e)}'
#             }, status=500)
    
#     except json.JSONDecodeError:
#         return JsonResponse({'error': 'Invalid JSON data'}, status=400)
#     except Exception as e:
#         return JsonResponse({
#             'error': f'Unexpected error: {str(e)}'
#         }, status=500)

@login_required
def blog_list(request):
    """Display user's blog articles"""
    blog_articles = BlogPost.objects.filter(user=request.user).order_by('-created_at')
    return render(request, "all-blogs.html", {'blog_articles': blog_articles})

@login_required
def blog_details(request, pk):
    """Display specific blog article"""
    try:
        blog_article_detail = BlogPost.objects.get(id=pk)
        if request.user == blog_article_detail.user:
            return render(request, 'blog-details.html', {'blog_article_detail': blog_article_detail})
        else:
            return JsonResponse({'error': 'Access denied'}, status=403)
    except BlogPost.DoesNotExist:
        return JsonResponse({'error': 'Blog post not found'}, status=404)

# Legacy functions for backward compatibility
def yt_title(link):
    """Legacy function - use get_video_info_enhanced instead"""
    try:
        info = get_video_info_enhanced(link)
        return info.get('title', 'Unknown Title')
    except Exception as e:
        raise ValueError(f"Failed to fetch video title: {str(e)}")

def download_audio(link):
    """Legacy function - use download_audio_enhanced instead"""
    try:
        audio_file, temp_dir = download_audio_enhanced(link)
        if audio_file:
            return audio_file
        else:
            raise ValueError("Failed to download audio")
    except Exception as e:
        raise ValueError(f"Failed to download audio: {str(e)}")

def get_transcription(link):
    """Legacy function - use get_transcription_enhanced instead"""
    try:
        transcript_data = get_transcription_enhanced(link)
        return transcript_data.get('text', '')
    except Exception as e:
        raise ValueError(f"Failed to get transcript: {str(e)}")

def generate_blog_from_transcription(transcription):
    
    """Legacy function - use generate_blog_from_transcription_enhanced instead"""
    try:
        # Create minimal video_info for legacy support
        video_info = {'title': 'Blog Article', 'channel': 'Unknown'}
        transcript_data = {'text': transcription, 'highlights': [], 'speakers': {}}
        
        return generate_blog_from_transcription_enhanced(transcript_data, video_info)
    except Exception as e:
        raise ValueError(f"Failed to generate blog: {str(e)}")
    

