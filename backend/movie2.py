import os
import io
import time
import requests
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
from moviepy.video.fx.all import crop
import whisper_timestamped as whisper

load_dotenv()

CHUNK_SIZE = 1024

def download_videos(urls):
    # Send an HTTP GET request to the URL
    i = 1
    for url in urls:
        response = requests.get(url)
    
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Open the file in binary write mode and write the content
            with open(f'video-downloaded{i}.mp4', 'wb') as f:
                f.write(response.content)
            print(f'Video downloaded successfully as video-downloaded{i}.mp4')
        else:
            print("Failed to download video")
        i = i + 1

def get_daily_horoscope(zodiac_sign):
    url = "https://horoscope-astrology.p.rapidapi.com/horoscope"

    querystring = {"day":"today","sunsign":zodiac_sign.lower()}

    headers = {
    	"X-RapidAPI-Key": os.getenv('HOROSCOPE_API_KEY'),
    	"X-RapidAPI-Host": "horoscope-astrology.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()


    return data['horoscope']

def get_video_url(el):
    return el['video_files'][0]['link']

def get_random_videos():
    # Replace <YOUR_API_KEY> with your actual API key
    pexels_api_url = "https://api.pexels.com/videos/popular"
    querystring = {"min_width":"1000","min_height":"1800", "min_duration": 20, "max_duration": 30, "per_page": 3}
    headers = {
        "Authorization": os.getenv("PEXELS_API_KEY")
    }
    response = requests.get(pexels_api_url, headers=headers, params=querystring)
    data = response.json()
    video_urls = list(map(get_video_url, data['videos']))
    return video_urls

def get_narrator_audio(horoscope):

    url = "https://api.elevenlabs.io/v1/text-to-speech/pFZP5JQG7iQjIQuC4Bku"

    payload = {
        "text": horoscope,
        "voice_settings": {
            "similarity_boost": 1,
            "stability": 1
        },
        "model_id": "eleven_monolingual_v1"
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "audio/mpeg",
        "xi-api-key":os.getenv("X11_API_KEY")
    }

    response = requests.request("POST", url, json=payload, headers=headers)

    with open('narration.mp3', 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)
    return "narration.mp3"

def get_word_timestamps(filename):
    audio = whisper.load_audio(filename)

    model = whisper.load_model("tiny", device="cpu")

    result = whisper.transcribe(model, audio, language="en")

    return result


def generate_video():



    zodiac_sign = "Scorpio"




    horoscope = get_daily_horoscope(zodiac_sign)
    video_urls = get_random_videos()
    audio_filename = get_narrator_audio(horoscope)
    # word_timestamps = get_word_timestamps(audio_filename)
    # download_videos(video_urls)

    # Sleep for a little bit to filesystem time to catch up
    time.sleep(5)

    # Load tts + music for use in each of the videos
    audio = AudioFileClip(audio_filename)
    music = AudioFileClip("oneheart.mp3")
    music = music.set_duration(audio.duration + 1)
    full_audio = CompositeAudioClip([audio, music])

    print("Editing Video")

    for x in range(len(video_urls)):
        background_video = VideoFileClip(f'./video-downloaded{x + 1}.mp4')
        cropx = (background_video.w - 1080) / 2
        if (cropx < 0):
            cropx = 0
        cropy = (background_video.h - 1920) / 2
        if (cropy < 0):
            cropy = 0
        background_video = crop(background_video, x1=cropx, y1=cropy, width=1080, height=1920)
        if background_video.h < 1920:
            background_video = background_video.resize((1080, 1920))
        screensize = (800,None)
        # Create a text clip for the header message
        header_text = TextClip(f'{zodiac_sign} Daily Horoscope:', fontsize=90, font="Arial-Bold", color='white', stroke_color='black', size=screensize, method='caption').set_position(('center', 100))

        # Create a text clip for the horoscope
        horoscope_text = TextClip(horoscope, fontsize=60, color='white', size = screensize, stroke_color='black', bg_color="rgba(0, 0, 0, 0.38)", method='caption').set_position('center')

        # Composite the text clips on top of the background video
        background_video.audio = full_audio
        final_clip = CompositeVideoClip([background_video, header_text.set_duration(background_video.duration), horoscope_text.set_duration(background_video.duration)])

        # Write the edited video to a file
        print("Saving Video...")
        final_clip.write_videofile(f'../videos/final_{x + 1}.mp4', codec="libx264")

    # with open("edited_video.mp4", "rb") as video_file:
    #     video_blob = video_file.read()

    # Return a sample response for now
    # return send_file(io.BytesIO(video_blob), mimetype='video/mp4')
    print("Done!")
    return True

generate_video();