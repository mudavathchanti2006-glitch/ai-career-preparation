import os
from dotenv import load_dotenv
from google import genai

load_dotenv(override=True)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def test_model(model_name):
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model=model_name,
            contents="Hello"
        )
        print(f"Success with {model_name}: {response.text}")
    except Exception as e:
        print(f"Error with {model_name}: {e}")

test_model("gemini-3.8-flash")
test_model("gemini-pro")
test_model("gemini-1.5-pro")
test_model("gemini-2.5-flash")
