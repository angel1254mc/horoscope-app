import ollama
import os
import io
import time
import requests
import random
from tqdm import tqdm
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, CompositeAudioClip
from moviepy.video.fx.all import crop, colorx
import whisper_timestamped as whisper

load_dotenv()

CHUNK_SIZE = 1024

def download_videos(urls):
    i = 1
    for url in urls:
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Open the file in binary write mode and write the content
            with open(f'../videos/video-downloaded{i}.mp4', 'wb') as f:
                f.write(response.content)
            print(f'Video downloaded successfully as video-downloaded{i}.mp4')
        else:
            print("Failed to download video")
        i = i + 1

def get_daily_horoscope(zodiac_sign):
    response = ollama.generate(model='mistral', prompt=f"Generate a creative daily horoscope for {zodiac_sign}s. Imagine yourself as an expert in astrology, deeply attuned to the cosmic energies that influence our lives. Craft a personalized horoscope that offers insightful guidance and inspiration for {zodiac_sign} based on today's celestial alignments. Ensure each horoscope is unique and tailored to the individual characteristics and current planetary positions. Your goal is to provide a fresh and engaging perspective with each reading, avoiding repetition and clichés. Please keep it to 4 sentences at most and respond only with the daily horoscope message. You do not need to specify it as 'daily horoscope', just return the message and nothing else")
    print(response)
    return response['response']

def get_video_url(el):
    return el['video_files'][0]['link']

def get_random_videos(duration, clip_count):
    # Replace <YOUR_API_KEY> with your actual API key
    pexels_api_url = "https://api.pexels.com/videos/search"
    querystring = {"query": "scenic", "orientation": "portrait", "size":"medium", "per_page": 20}
    headers = {
        "Authorization": os.getenv("PEXELS_API_KEY")
    }
    response = requests.get(pexels_api_url, headers=headers, params=querystring)
    data = response.json()
    video_urls = data['videos']
    video_urls = list(filter(lambda obj: obj["duration"] > duration/(clip_count - 1), video_urls))
    video_urls = list(map(get_video_url, video_urls))
    video_urls = random.sample(video_urls, clip_count)
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

# Gets the total width in pixels of an array of strings 
def get_text_width(word_arr, fontsize):
    total = 0
    for word in word_arr:
        total = total + len(word["text"])*fontsize 
    return total

def transcribe_audio(audio_filename):
    print("Transcribing Audio...")
    audio = whisper.load_audio(audio_filename)
    model = whisper.load_model("large", device="cpu")
    result = whisper.transcribe(model, audio, language="en")
    return result["segments"]

# Gets clip durations
def get_clip_durations(segments, start_delay, end_delay, clip_count):
    clip_durations = []
    # Split segments into `clip_count` composite segments to extract start + end durations from
    composite_segments = [segments[i:(i + int(len(segments)/clip_count))] for i in range(0, int(len(segments)),int(len(segments)/clip_count) )]

    for idx, segment in enumerate(composite_segments):
        if idx == 0:
            clip_durations.append([segment[0]["words"][0]["start"] - start_delay, segment[-1]["words"][-1]["end"]])
        elif idx == 2:
            clip_durations.append([composite_segments[idx - 1][-1]["words"][-1]["end"], segment[-1]["words"][-1]["end"] + end_delay])
        else:
            clip_durations.append([composite_segments[idx - 1][-1]["words"][-1]["end"], segment[-1]["words"][-1]["end"]])
    return clip_durations

# Gets Transcribed Text based on an audiofile, with the ability to set a max size (screensize), a delay for when the text should start, and a fontsize
# Optionally returns durations for `clip_count` number of clips, based on grouping of speech segments to make transitions feel more natural
def get_transcribed_text_v2(audio_filename, start_delay=1, end_delay=10, fontsize=100, screensize=1000, clip_count=3, stroke_width=7, color="white", emphasis_color="#79f035", stroke_color="black", font="Arial", original_script=None):

    text_elements = []

    # Transcribe text into JSON  structure
    segments = transcribe_audio(audio_filename)
    original_arr = original_script.split() if original_script != None else None
    # Delay each word by start_delay
    # AND replace recognized words with cttual word
    word_idx = 0
    for segment in segments:
        for word in segment["words"]:
            word["start"] = word["start"] + start_delay
            word["end"] = word["end"] + start_delay
            if original_script != None:
                word["text"] = original_arr[word_idx]
                word_idx = word_idx + 1

    # Get duration of background clips
    clip_durations = get_clip_durations(segments, start_delay, end_delay, clip_count)

    # For a textclip of n words where n > 1 and all words fit onscreen, we render n textclips where the emphasized word is highlighted for the duration of the word
    # For textclips where just one word is onscreen, we don't need to do any highlighting
    curr_text_clip = []
    print("Proccessing Transcribed Text...")
    for segment in tqdm(segments):
        for idx, word in enumerate(segment["words"]):
            curr_text_clip.append(word)
            if (idx == (len(segment["words"]) - 1)):
                # One text clip for every emphasized word
                if  (len(curr_text_clip) == 1):
                    text_elements.append(
                        TextClip(f'<b>{curr_text_clip[0]["text"]}</b>',
                            fontsize=fontsize,
                            method='pango',
                            stroke_width=stroke_width, 
                            stroke_color=stroke_color, 
                            font=font,
                            size = (screensize, None),
                              color=color)
                        .set_start(word["start"])
                        .set_end(word["end"])   
                        .set_position("center") 
                    )
                    
                else: 
                    for word in curr_text_clip:
                        curr_text_clip_strings = list(map(lambda w: w["text"], curr_text_clip))
                        emphasis_string =" ".join(curr_text_clip_strings).replace(word["text"], f'<span foreground="{emphasis_color}">{word["text"]}</span>')
                        text_elements.append(
                            TextClip( f'<b>{emphasis_string}</b>',
                                fontsize=fontsize,
                                method='pango',
                                stroke_width=stroke_width, 
                                stroke_color=stroke_color, 
                                font=font,
                                size = (screensize, None),
                                  color=color)
                            .set_start(word["start"])
                            .set_end(word["end"])   
                            .set_position("center") 
                            
                        )
                        
                curr_text_clip= []
            else:
                if (get_text_width(curr_text_clip, fontsize) + (len(segment["words"][idx + 1]["text"]) * fontsize)) > screensize:

                    if  (len(curr_text_clip) == 1):
                        text_elements.append(
                            TextClip(f'<b>{curr_text_clip[0]["text"]}</b>',
                                fontsize=fontsize,
                                method='pango',
                                stroke_width=stroke_width, 
                                stroke_color=stroke_color, 
                                font=font,
                                size = (screensize, None),
                                  color=color)
                            .set_start(word["start"])
                            .set_end(word["end"])   
                            .set_position("center") 
                        )
                        
                    else:
                        # Create text clip, push to array
                        for word in curr_text_clip:
                            curr_text_clip_strings = list(map(lambda w: w["text"], curr_text_clip))
                            print(curr_text_clip_strings)
                            emphasis_string = " ".join(curr_text_clip_strings).replace(word["text"], f'<span foreground="{emphasis_color}">{word["text"]}</span>')
                            text_elements.append(
                                TextClip(f'<b>{emphasis_string}</b>',
                                    fontsize=fontsize,
                                    method='pango',
                                    stroke_width=stroke_width, 
                                    stroke_color=stroke_color, 
                                    font=font,
                                    size = (screensize, None),
                                      color=color)
                                .set_start(word["start"])
                                .set_end(word["end"])   
                                .set_position("center") 
                            )
                            
                    curr_text_clip = []
                else:
                    continue
    return [text_elements, clip_durations]


def generate_video():



    zodiac_sign = "Aries"

    audio_start_delay = 2
    audio_end_delay = 8


    horoscope = get_daily_horoscope(zodiac_sign)
    print(horoscope)
    audio_filename = get_narrator_audio(horoscope)
    # Array of textclip
    [text_clips, durations] = get_transcribed_text_v2(audio_filename=audio_filename, start_delay=audio_start_delay, end_delay=audio_end_delay)


    # Load tts + music for use in each of the videos
    audio = AudioFileClip("narration.mp3")
    music = AudioFileClip("../audio/oneheart.mp3")
    audio = audio.set_start(audio.start + audio_start_delay)
    music = music.set_duration(audio.duration + audio_end_delay)
    full_audio = CompositeAudioClip([audio, music])

    video_urls = get_random_videos(duration=int(music.duration), clip_count=3)
    download_videos(video_urls)
    # Sleep for a little bit to filesystem time to catch up
    time.sleep(5)
    
    print("Editing Video")
    finalized_videos = []
    for x in range(len(video_urls)):
        curr_video = VideoFileClip(f'../videos/video-downloaded{x + 1}.mp4')
        print(x)
        curr_video = curr_video.set_start(durations[x][0])
        curr_video = curr_video.set_end(durations[x][1])
        if x == (len(video_urls) - 1):
            curr_video = curr_video.set_end(music.end)
        cropx = (curr_video.w - 1080) / 2
        if (cropx < 0):
            cropx = 0
        cropy = (curr_video.h - 1920)
        if (cropy < 0):
            cropy = 0
        curr_video = crop(curr_video, x1=cropx, y1=cropy, width=1080, height=1920)
        if curr_video.h < 1920:
            curr_video = curr_video.resize((1080, 1920))
        screensize = (800 , None)
        curr_video = curr_video.fx(colorx, 0.7) 
        finalized_videos.append(curr_video)

    # Create a text clip for the header message
    header_text = TextClip(f'{zodiac_sign} Daily Horoscope:', fontsize=100, font="Arial-Black", color='white', stroke_color='black', size=screensize, method='caption').set_position(('center', 100))
    final_clip = CompositeVideoClip(finalized_videos + text_clips + [header_text]).set_duration(music.duration)
    final_clip.audio = full_audio
    # Write the edited video to a file
    print("Saving Video...")
    final_clip.write_videofile(f'../videos/final_{1}.mp4', codec="libx264")

    # with open("edited_video.mp4", "rb") as video_file:
    #     video_blob = video_file.read()

    # Return a sample response for now
    # return send_file(io.BytesIO(video_blob), mimetype='video/mp4')
    print("Done!")
    return True

generate_video();