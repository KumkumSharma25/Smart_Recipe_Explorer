import os
import requests
from dotenv import load_dotenv


load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json"
}

def simplify_recipe(instructions: str) -> str:
    """
    Simplify recipe instructions using OpenRouter AI.
    """
    prompt = f"Simplify the following recipe instructions for beginners in easy language:\n\n{instructions}"

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 500
    }

    response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
    response.raise_for_status() 

    data = response.json()
    return data['choices'][0]['message']['content']

def suggest_recipe(ingredients: str) -> str:
    """
    Suggest a recipe given a list of ingredients.
    Returns "INVALID_INGREDIENTS" if input contains non-edible items.
    """
    prompt = f"""
You are a cooking assistant.

Rules:
- ONLY respond if all ingredients are edible food items.
- If the input contains non-food items (e.g., clothes, phone, chair),
respond exactly with:
"INVALID_INGREDIENTS"

Ingredients:
{ingredients}

If valid:
- Suggest ONE recipe
- Provide recipe name
- Provide 3–4 simple steps
"""

    payload = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 500
    }

    response = requests.post(OPENROUTER_URL, json=payload, headers=headers)
    response.raise_for_status()

    data = response.json()
    return data['choices'][0]['message']['content'].strip()

