import requests

url = "http://host.docker.internal:11434/api/embed"
payload = {
    "model": "nomic-embed-text:v1.5",
    "input": "This is a test of the Ollama embedding API.",
}

resp = requests.post(url, json=payload)
print(resp.status_code)
print(resp.json())
