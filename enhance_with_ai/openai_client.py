import requests
import json

API_URL = "https://api.openai.com/v1/chat/completions"

class OpenAIClient:
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model

    def stream(self, prompt):
        with requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "stream": True,
                "messages": [{"role": "user", "content": prompt}],
            },
            stream=True,
            timeout=60,
        ) as r:

            r.raise_for_status()

            for line in r.iter_lines():
                if not line:
                    continue

                # OpenAI sends: b"data: {...}"
                if line.startswith(b"data: "):
                    payload = line[6:]

                    if payload == b"[DONE]":
                        break

                    data = json.loads(payload)
                    delta = data["choices"][0]["delta"]

                    if "content" in delta:
                        yield delta["content"]
