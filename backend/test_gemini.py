import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
api_key = os.getenv('GEMINI_API_KEY')
print(f"API Key found: {'Yes' if api_key else 'No'}")

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    print("Model initialized. Testing generation...")
    response = model.generate_content("Say hello")
    print(response.text)
except Exception as e:
    import traceback
    traceback.print_exc()
