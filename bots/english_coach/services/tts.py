from gtts import gTTS
import os

async def text_to_speech(text: str, filename: str = 'pronunciation.mp3'):
    """Convert text to speech audio file."""
    tts = gTTS(text=text, lang='en', slow=False)
    filepath = f'/tmp/{filename}'
    tts.save(filepath)
    return filepath
