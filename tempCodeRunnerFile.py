
from google import genai
import json
import os
from typing import Optional

client = genai.Client(
    api_key=""
) 

def clean_text(text):
    return text.encode("utf-8", "ignore").decode("utf-8")

with open('test_results/run_20260119_120719/test_data.json', 'r') as f:
    txt = f.read()
prompt = clean_text(txt)


response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=f"I am providing a json format testing report. extract each module and explain teh error found. additionally tell the things to check on. The json report is {prompt}"
)

print(response.text)
