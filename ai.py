import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))

chat_history = []


def chat(message):
    chat_history.append(message)

    # print(chat_history)

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        # contents="What is the weather like at EHAM?",
        contents=chat_history,
        config=types.GenerateContentConfig(
            system_instruction="You are a pilot assistant. You can plan navigation routes, flight plans, help with aviation meteorology, create navigation logs. Only consider VFR in VMC conditions. Limit you're scope to general aviation (GA). Prevent the user from unsafe situations like at low altitudes, strong winds, low hanging clouds.\nConsider the user to be a pilot, flight student, flight instructor or aviation enthusiast.\n\nPay attention to (future) weather conditions like low temperatures, fast changing cloud bases, dangerous weather phenomena like cumulonimbus, thunderstorms, lightning.",
            temperature=0.5,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
        ),
    )
    chat_history.append(response.text)
    return response.text
