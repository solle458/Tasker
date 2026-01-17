from google import genai
from dotenv import load_dotenv
from pathlib import Path
import os

dotenv_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path)
# The client gets the API key from the environment variable `GEMINI_API_KEY`.
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

response = client.models.generate_content(
    model="gemini-3-flash-preview", contents="Explain how AI works in a few words"
)
print(response.text)
