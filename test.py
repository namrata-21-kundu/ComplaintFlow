
from google import genai

client = genai.Client(api_key="AIzaSyCaewfW6oz40iWPIUenH8TljRz58F9d6q8")

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say Hello"
    )

    print("✅ API Key is working!")
    print("Response:", response.text)

except Exception as e:
    print("❌ API Key failed or invalid.")
    print("Error:", e)