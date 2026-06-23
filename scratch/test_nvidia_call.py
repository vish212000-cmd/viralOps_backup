import requests

api_key = "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"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

payload = {
    "model": "meta/llama-3.1-8b-instruct",
    "messages": [{"role": "user", "content": "Say hello!"}],
    "max_tokens": 8000
}

try:
    print("Testing POST with max_tokens=8000...")
    res = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=15
    )
    print("Status Code:", res.status_code)
    print("Response Text:", res.text)
except Exception as e:
    print("Request failed:", e)
