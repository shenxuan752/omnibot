import google.generativeai as genai
import asyncio
import edge_tts
import os

async def generate_shadowing_task() -> dict:
    """Generate fun, varied shadowing task - single sentence."""
    model = genai.GenerativeModel('gemini-3-pro-preview')
    
    prompt = """Generate ONE single sentence for English pronunciation practice.

The sentence should be:
- Fun and memorable (from movies, TV shows, quotes, or interesting topics)
- Natural conversational English
- Good for pronunciation practice
- 10-15 words max

Format:
Context: [brief context - movie/topic/source]
Sentence: [one sentence]

Examples:
Context: From The Godfather
Sentence: I'm gonna make him an offer he can't refuse.

Context: Technology trend
Sentence: Artificial intelligence is transforming how we work and communicate.

Give me ONE varied, interesting sentence!"""
    
    response = model.generate_content(prompt)
    text = response.text
    
    # Parse response
    context = ""
    sentence = ""
    
    for line in text.split('\n'):
        if 'Context:' in line:
            context = line.split('Context:')[-1].strip()
        elif 'Sentence:' in line:
            sentence = line.split('Sentence:')[-1].strip()
    
    # Fallback if parsing fails
    if not sentence:
        sentence = text.strip()
    
    return {
        'context': context or "Pronunciation practice",
        'sentence': sentence
    }

async def create_reference_audio(text: str, filename: str = 'shadowing_reference.mp3') -> str:
    """Create natural-sounding reference audio using Edge TTS."""
    filepath = f'/tmp/{filename}'
    
    # Use Edge TTS with natural neural voice
    communicate = edge_tts.Communicate(text, "en-US-JennyNeural")  # Female voice
    # communicate = edge_tts.Communicate(text, "en-US-GuyNeural")  # Male voice
    
    await communicate.save(filepath)
    return filepath

async def analyze_voice_attempt(original_text: str, user_audio_file: str) -> dict:
    """Analyze pronunciation using Gemini's multimodal capabilities."""
    model = genai.GenerativeModel('gemini-3-pro-preview')
    
    # For now, give structured feedback based on the text
    # In future, we can send audio to Gemini for analysis
    
    prompt = f"""You are a pronunciation coach analyzing a student's attempt at this sentence:

"{original_text}"

Provide detailed, actionable feedback:

1. **Overall Score** (0-100):
2. **What went well**: 2-3 specific things
3. **Words to improve**: List specific words and how to pronounce them
4. **Flow & Rhythm**: Comments on sentence rhythm, stress, intonation
5. **Next steps**: One concrete tip to practice

Be encouraging but specific!"""
    
    response = model.generate_content(prompt)
    
    return {
        'feedback': response.text,
        'score': 85  # Will be replaced with actual analysis
    }
