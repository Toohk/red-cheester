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


audio_config = AudioOutputConfig(filename="speech/win.mp3")
synthesizer = SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
result = synthesizer.speak_text_async("Bravo vous avez répondu juste au 15 questions, vous gagner ce magnifique robot cuiseur et une encyclopédie Larrousse. ").get()
stream = AudioDataStream(result)
