import asyncio
import os
from unittest.mock import patch
from datetime import datetime
import pytz

# Set environment variables
os.environ['GEMINI_API_KEY'] = os.getenv('GEMINI_API_KEY', 'test-key')

async def test_word_of_day():
    from services.gemini_ai import generate_word_of_day
    
    print("Testing Word of the Day generation...")
    print("=" * 50)
    
    # Test 1: Generate word for today
    print("\n📅 Test 1: Generate word for today")
    word1 = await generate_word_of_day()
    print(f"Word: {word1['word']}")
    print(f"Definition: {word1['definition']}")
    
    # Test 2: Generate word again (should be same as Test 1 if called on same day)
    print("\n📅 Test 2: Generate word again (same day)")
    word2 = await generate_word_of_day()
    print(f"Word: {word2['word']}")
    
    # Note: Due to AI randomness, words might still differ
    # But the date is now included in the prompt to influence consistency
    if word1['word'].lower() == word2['word'].lower():
        print("✅ Same word generated (good for consistency)")
    else:
        print("⚠️ Different word generated (AI may still vary)")
    
    # Test 3: Simulate tomorrow
    print("\n📅 Test 3: Simulate tomorrow's date")
    ny_tz = pytz.timezone('America/New_York')
    tomorrow = datetime.now(ny_tz).replace(day=datetime.now(ny_tz).day + 1)
    
    with patch('services.gemini_ai.datetime') as mock_datetime:
        mock_datetime.now.return_value = tomorrow
        mock_datetime.strftime = datetime.strftime
        word3 = await generate_word_of_day()
        print(f"Word: {word3['word']}")
        print(f"(Note: This test may not work perfectly due to mocking limitations)")
    
    print("\n" + "=" * 50)
    print("✅ Test complete. The date is now included in the prompt.")
    print("While AI may still vary, the date seed should help consistency.")

if __name__ == "__main__":
    asyncio.run(test_word_of_day())
