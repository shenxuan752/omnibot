import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Fast model for simple tasks (word lookup, WOD)
model_fast = genai.GenerativeModel('gemini-2.5-flash')

# High-quality model for complex tasks (voice analysis, shadowing)
model = genai.GenerativeModel('gemini-3-pro-preview')

async def lookup_word(word: str) -> dict:
    """Look up a word and get definition, Chinese translation, and example."""
    prompt = f"""Define the word '{word}' in 1-2 concise sentences for MBA students.
    Provide the Chinese translation.
    Give a practical business/MBA example sentence.
    
    Format your response EXACTLY as:
    Definition: [definition]
    IPA: [American IPA pronunciation, e.g. /wɜrd/]
    Chinese: [chinese translation]
    Example: [example sentence]
    """
    
    response = model_fast.generate_content(prompt)
    text = response.text
    
    # Parse response
    definition = ""
    ipa = ""
    chinese = ""
    example = ""
    
    for line in text.split('\n'):
        if line.startswith('Definition:'):
            definition = line.replace('Definition:', '').strip()
        elif line.startswith('IPA:'):
            ipa = line.replace('IPA:', '').strip()
        elif line.startswith('Chinese:'):
            chinese = line.replace('Chinese:', '').strip()
        elif line.startswith('Example:'):
            example = line.replace('Example:', '').strip()
    
    return {
        'word': word,
        'definition': definition,
        'ipa': ipa,
        'chinese': chinese,
        'example': example
    }

async def analyze_pronunciation(text: str, expected: str) -> dict:
    """Analyze pronunciation quality from transcribed text (legacy)."""
    prompt = f"""You are a pronunciation coach. Compare what the student said vs what they should have said.

Expected text: "{expected}"
What they said: "{text}"

Provide:
1. Overall score (0-100)
2. Specific words pronounced incorrectly
3. Helpful tips

Keep feedback encouraging and concise!"""
    
    response = model.generate_content(prompt)
    return {'feedback': response.text, 'score': 85}

async def analyze_audio_file(audio_path: str) -> dict:
    """Analyze audio file directly using Gemini multimodal."""
    try:
        # Upload file to Gemini
        myfile = genai.upload_file(audio_path)
        
        prompt = """Listen to this audio.
        1. Transcribe exactly what was said.
        2. Analyze the pronunciation, intonation, and fluency.
        3. Give a score (0-100).
        4. Provide specific feedback on words to improve.
        
        IMPORTANT: Output PLAIN TEXT ONLY. Do NOT use bold (**), italics (_), or any markdown characters.
        Telegram will crash if you use them. Just use plain text.
        
        Format:
        Transcription: [text]
        Feedback: [detailed feedback]
        Score: [number]
        """
        
        response = model.generate_content([prompt, myfile])
        return {'text': response.text}
    except Exception as e:
        return {'text': f"Error analyzing audio: {str(e)}"}

async def generate_word_of_day() -> dict:
    """Generate interesting word for the day."""
    from datetime import datetime
    import pytz
    
    # Get current date in New York timezone
    ny_tz = pytz.timezone('America/New_York')
    today = datetime.now(ny_tz).strftime('%Y-%m-%d')
    
    # Use date as seed in prompt to ensure consistency within the day
    prompt = f"""Generate ONE interesting business/MBA vocabulary word for international students.
    
    Today's date: {today}
    
    Important: Generate a DIFFERENT word each day based on the date. Use the date to select a unique word.
    Do NOT repeat words from previous days.
    
    Format:
    Word: [word]
    Definition: [definition]
    Chinese: [chinese]
    Example: [example]
    
    Make it relevant and useful!"""
    
    response = model_fast.generate_content(prompt)
    text = response.text
    
    # Parse response (handle markdown formatting)
    word = ""
    definition = ""
    chinese = ""
    example = ""
    
    for line in text.split('\n'):
        # Remove markdown formatting (** and *)
        clean_line = line.replace('**', '').replace('*', '').strip()
        
        if clean_line.startswith('Word:'):
            word = clean_line.replace('Word:', '').strip()
        elif clean_line.startswith('Definition:'):
            definition = clean_line.replace('Definition:', '').strip()
        elif clean_line.startswith('Chinese:'):
            chinese = clean_line.replace('Chinese:', '').strip()
        elif clean_line.startswith('Example:'):
            example = clean_line.replace('Example:', '').strip()
    
    return {
        'word': word,
        'definition': definition,
        'chinese': chinese,
        'example': example
    }

async def generate_journal_prompt() -> str:
    """Return the standard daily reflection prompt."""
    return """
1. 3 things you feel gratitude for and did well
2. 3 things you think you can do better
3. 3 things you plan to do tomorrow"""

async def generate_weekly_mission() -> dict:
    """Generate a real-world English mission."""
    prompt = """Generate a fun, practical English learning mission for the week.
    Target: Intermediate/Advanced learner.
    
    Format:
    Title: [Mission Title]
    Task: [Specific task, e.g., "Order coffee using 3 adjectives"]
    Tip: [One helpful tip]
    """
    response = model.generate_content(prompt)
    text = response.text
    
    title = ""
    task = ""
    tip = ""
    
    for line in text.split('\n'):
        if line.startswith('Title:'):
            title = line.replace('Title:', '').strip()
        elif line.startswith('Task:'):
            task = line.replace('Task:', '').strip()
        elif line.startswith('Tip:'):
            tip = line.replace('Tip:', '').strip()
            
    return {'title': title, 'task': task, 'tip': tip}
