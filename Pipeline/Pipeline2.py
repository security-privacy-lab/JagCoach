import os
import sys
import re
import subprocess
from io import StringIO
import json
import whisper
import torch
import nltk
nltk.download('punkt')

mysp = __import__("my-voice-analysis")


def convert_to_wav(video, output_name):
    try:
        command = [
            "ffmpeg",
            "-y",
            "-i",
            video,
            "-vn",  # Disable video recording
            "-acodec",
            "pcm_s16le",  # Set audio codec to PCM 16-bit little-endian
            "-ar",
            "44100",  # Set audio sample rate to 44100 Hz
            "-ac",
            "2",  # Set number of audio channels to 2 (stereo)
            output_name,
        ]
        subprocess.run(command, check=True)
        print("Conversion successful!")
    except subprocess.CalledProcessError as e:
        print("Error:", e)


def process_video(video):
    video_name = os.path.splitext(os.path.basename(video))[0]
    print(video_name)
    audio_output_name = video_name + ".wav"
    print(audio_output_name)
    json_output_name = video_name + ".json"
    print(json_output_name)
    script_output_name = video_name + "transcript.json"
    video_format = os.path.splitext(video)[1][1:].lower()

    convert_to_wav(video, audio_output_name)

    old_stdout = sys.stdout
    sys.stdout = my_buffer = StringIO()
    mysp.myspbala(video_name, "/home/rudito/Code/Cao_Research/JagCoach/Pipeline")
    output = my_buffer.getvalue()
    sys.stdout = old_stdout
    balance_str = output[3::].strip(
        "balance= # ratio (speaking duration)/(original duration)\n"
    )
    balance = float(balance_str)

    old_stdout = sys.stdout
    sys.stdout = my_buffer = StringIO()
    mysp.myspatc(video_name, "/home/rudito/Code/Cao_Research/JagCoach/Pipeline")
    output2 = my_buffer.getvalue()
    sys.stdout = old_stdout
    rate_str = output2[3::].strip(
        "articulation_rate= # syllables/sec speaking duration"
    )
    rate_str = rate_str.replace("# syllables/sec speaking duration", "")
    rate = float(rate_str)

    old_stdout = sys.stdout
    sys.stdout = my_buffer = StringIO()
    mysp.myspf0sd(video_name, "/home/rudito/Code/Cao_Research/JagCoach/Pipeline")
    output3 = my_buffer.getvalue()
    sys.stdout = old_stdout
    stdd_str = output3[3::].strip(
        "f0_SD= # Hz global standard deviation of fundamental frequency distribution"
    )
    stdd_str = stdd_str.replace(
        "# Hz global standard deviation of fundamental frequency distribution", ""
    )
    stdd = float(stdd_str)

    raw_stats = {
        "Speech to Noise Ratio:": balance_str,
        "Speech Rate (Syllables per Sec):": int(rate),
        "Speech Fundamental Frequency STD Deviation:": stdd_str,
    }
    with open(json_output_name, "w") as outfile:
        json.dump(raw_stats, outfile)

    model = whisper.load_model("medium.en")
    result = model.transcribe(audio_output_name)

    sentences = nltk.tokenize.sent_tokenize(result["text"])
    formatted_text = "<br>".join(sentences)
    print(formatted_text)
    json_output = {"text": formatted_text}

    with open(script_output_name, "w") as f:
        json.dump(json_output, f)
    torch.cuda.empty_cache()
    return {
        "audio_output": audio_output_name,
        "json_output": json_output_name,
        "script_output": script_output_name,
    }
