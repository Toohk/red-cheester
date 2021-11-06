import os
from dotenv import load_dotenv
import requests
import json
from azure.cognitiveservices.speech import AudioDataStream, SpeechConfig, SpeechSynthesizer, SpeechSynthesisOutputFormat
from azure.cognitiveservices.speech.audio import AudioOutputConfig
import asyncio
import time

load_dotenv()
SPEECH_KEY = os.getenv('AZURE_SPEECH')
speech_config = SpeechConfig(subscription=SPEECH_KEY, region="francecentral")

speech_config.speech_synthesis_language = "fr-FR" 
speech_config.speech_synthesis_voice_name ="fr-FR-HenriNeural"

f = open('questions.json', "r", encoding='utf8')
quest = json.load(f)

n = 100
x = 0
k = 0

for q in quest["questions"]:
    x = x+1
    if x > n :
        k = k+1
        if k > 3:
            time.sleep(60)
            k = 0
        audio_config = AudioOutputConfig(filename="speech/"+ str(q["id"])+".mp3")
        synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
        result = synthesizer.speak_text_async(q["question"]).get()
        stream = AudioDataStream(result)
        i = 0
        for a in q["answers"]:
            i = i+1
            audio_config = AudioOutputConfig(filename="speech/"+ str(q["id"])+"-"+str(i)+".mp3")
            synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
            result = synthesizer.speak_text_async(a["text"]).get()
            stream = AudioDataStream(result)
    print("Question "+str(q["id"])+" done")