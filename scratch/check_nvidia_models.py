import requests

api_key = "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"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

try:
    print("Testing GET /v1/models...")
    res = requests.get("https://integrate.api.nvidia.com/v1/models", headers=headers, timeout=10)
    print("Status Code:", res.status_code)
    if res.status_code == 200:
        data = res.json()
        models = [m["id"] for m in data.get("data", [])]
        print("Available models:", len(models))
        print("First 10 models:", models[:10])
        # Check if meta/llama-3.1-8b-instruct or meta/llama-3.1-70b-instruct is in models
        for m in models:
            if "llama" in m.lower():
                print("Llama model:", m)
    else:
        print("Error Response:", res.text)
except Exception as e:
    print("Request failed:", e)
