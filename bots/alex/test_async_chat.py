import google.generativeai as genai
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

async def test_async_chat():
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    chat = model.start_chat(history=[])
    
    print("Testing send_message_async...")
    try:
        response = await chat.send_message_async("Hello")
        print(f"Success: {response.text}")
    except AttributeError:
        print("Error: send_message_async does not exist.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_async_chat())
