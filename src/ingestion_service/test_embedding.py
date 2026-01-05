import requests

url = "http://host.docker.internal:11434/api/embeddings"
payload = {
    "model": "nomic-embed-text:v1.5",
    "prompt": "This is a test of the Ollama embedding API.",
}

resp = requests.post(url, json=payload)
print(resp.status_code)
print(resp.json())
