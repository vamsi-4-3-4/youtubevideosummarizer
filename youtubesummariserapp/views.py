from django.shortcuts import render

# Create your views here.
def index(request):
	return render(request,"index.html")







from django.http import JsonResponse
from youtube_transcript_api import YouTubeTranscriptApi
import whisper
import os
import re
import yt_dlp
from googletrans import Translator

def get_transcript_from_api(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([item['text'] for item in transcript])
        return full_text
    except Exception as e:
        print("Transcript not available via API:", e)
        return None

def download_audio(video_url):
    command = f"yt-dlp -x --audio-format mp3 -o 'audio.mp3' {video_url}"
    os.system(command)

def transcribe_with_whisper(audio_file='audio.mp3'):
    model = whisper.load_model("base")
    result = model.transcribe(audio_file)
    return result["text"]

def get_video_metadata(video_url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
        return {
            'title': info.get('title'),
            'description': info.get('description'),
            'thumbnail_url': info.get('thumbnail')
        }

def summarize_points(transcript, lang_code='en'):
    # Naive summary: break into 10 chunks and get first sentence from each
    sentences = transcript.split('.')
    chunks = max(len(sentences) // 10, 1)
    points = [sentences[i * chunks].strip() + '.' for i in range(min(10, len(sentences)))]
    summary = '\n'.join(points)

    if lang_code != 'en':
        translator = Translator()
        translated = translator.translate(summary, dest=lang_code)
        return translated.text
    return summary

def summarize_video(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        lang = request.POST.get('lang', 'en')
        if not video_url:
            return JsonResponse({'error': 'No video URL provided'}, status=400)

        try:
            match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", video_url)
            video_id = match.group(1) if match else None
            if not video_id:
                return JsonResponse({'error': 'Invalid YouTube URL'}, status=400)

            metadata = get_video_metadata(video_url)

            transcript = get_transcript_from_api(video_id)
            source = "YouTube API"
            if not transcript:
                download_audio(video_url)
                transcript = transcribe_with_whisper("audio.mp3")
                source = "Whisper"

            summary = summarize_points(transcript, lang_code=lang)

            return JsonResponse({
                'video_id': video_id,
                'transcript_source': source,
                'transcript': transcript[:100],
                'title': metadata.get('title'),
                'description': metadata.get('description'),
                'thumbnail_url': metadata.get('thumbnail_url'),
                'summary': summary
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)











"""other"""


"""OLD WORKING CODE"""






