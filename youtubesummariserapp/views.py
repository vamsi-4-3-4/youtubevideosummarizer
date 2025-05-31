from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from youtube_transcript_api import YouTubeTranscriptApi
import whisper
import os
import re
import subprocess
import yt_dlp
from googletrans import Translator





BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COOKIES_FILE_PATH = os.path.join(BASE_DIR, 'cookies.txt')



def index(request):
    return render(request, "index.html")


def is_valid_cookies_file():
    """Return True if cookies.txt file is valid and non-empty"""
    try:
        with open(COOKIES_FILE_PATH, encoding="utf-8") as f:
            first_line = f.readline().strip()
            if not first_line or not first_line.startswith("# Netscape HTTP Cookie File"):
                return False
        return os.path.getsize(COOKIES_FILE_PATH) > 0
    except:
        return False


def get_transcript_from_api(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item['text'] for item in transcript])
    except Exception as e:
        print("Transcript not available via API:", e)
        return None


def download_audio(video_url):
    ydl_cmd = [
        "yt-dlp",
        "-x", "--audio-format", "mp3",
        "-o", "audio.%(ext)s",
        video_url
    ]

    if is_valid_cookies_file():
        ydl_cmd.insert(1, "--cookies")
        ydl_cmd.insert(2, COOKIES_FILE_PATH)

    print(f"Running yt-dlp command: {' '.join(ydl_cmd)}")
    try:
        subprocess.run(ydl_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print("yt-dlp error output:", e)
        raise Exception("yt-dlp failed. This video may require login or be private. Your cookies.txt may be missing or empty.")


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

    if is_valid_cookies_file():
        ydl_opts['cookiefile'] = COOKIES_FILE_PATH

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'description': info.get('description', ''),
                'thumbnail_url': info.get('thumbnail', '')
            }
    except Exception as e:
        print("Metadata fetch failed:", e)
        return {
            'title': 'Unknown',
            'description': '',
            'thumbnail_url': ''
        }


def summarize_points(transcript, lang_code='en'):
    sentences = transcript.split('.')
    chunks = max(len(sentences) // 10, 1)
    points = [sentences[i * chunks].strip() + '.' for i in range(min(10, len(sentences))) if sentences[i * chunks].strip()]
    summary = '\n'.join(points)

    if lang_code != 'en':
        translator = Translator()
        try:
            translated = translator.translate(summary, dest=lang_code)
            return translated.text
        except Exception as e:
            print("Translation failed:", e)
            return summary

    return summary


@csrf_exempt
def summarize_video(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid request method'}, status=405)

    video_url = request.POST.get('video_url')
    lang = request.POST.get('lang', 'en')

    if not video_url:
        return JsonResponse({'error': 'No video URL provided'}, status=400)

    try:
        match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", video_url)
        video_id = match.group(1) if match else None

        if not video_id:
            return JsonResponse({'error': 'Invalid YouTube URL'}, status=400)

        metadata = get_video_metadata(video_url)
        transcript = get_transcript_from_api(video_id)
        source = "YouTube API"

        if not transcript:
            print("Falling back to Whisper transcription")
            download_audio(video_url)
            transcript = transcribe_with_whisper("audio.mp3")
            source = "Whisper"

        summary = summarize_points(transcript, lang_code=lang)

        return JsonResponse({
            'video_id': video_id,
            'transcript_source': source,
            'transcript': transcript[:500],
            'title': metadata.get('title'),
            'description': metadata.get('description'),
            'thumbnail_url': metadata.get('thumbnail_url'),
            'summary': summary
        })

    except Exception as e:
        print("Error during video summarization:", e)
        return JsonResponse({'error': str(e)}, status=500)
