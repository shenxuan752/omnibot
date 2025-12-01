import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure Gemini
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in .env")
    exit(1)

genai.configure(api_key=api_key)

# Check available models
print("🔍 Checking available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f" - {m.name}")
except Exception as e:
    print(f"❌ Error listing models: {e}")

# Test the specific model
model_name = 'gemini-3-pro-preview' # The one in the code
print(f"\n�� Testing model: {model_name}")

try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Say 'Hello' if you are working.")
    print(f"✅ Success! Response: {response.text}")
except Exception as e:
    print(f"❌ Failed to use {model_name}: {e}")
    
    # Fallback test
    print("\n🔄 Trying fallback: gemini-1.5-flash")
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'Hello' from Flash.")
        print(f"✅ Flash Success! Response: {response.text}")
    except Exception as e2:
        print(f"❌ Flash Failed: {e2}")
