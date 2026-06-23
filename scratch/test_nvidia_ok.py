import time
import requests

api_key = "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"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

payload = {
    "model": "meta/llama-3.1-8b-instruct",
    "messages": [{"role": "user", "content": "reply with OK"}],
    "max_tokens": 100
}

url = "https://integrate.api.nvidia.com/v1/chat/completions"

print("--- Testing NVIDIA completions call ---")
start_time = time.time()
print("Request Start:", start_time)

try:
    res = requests.post(url, headers=headers, json=payload, timeout=30)
    end_time = time.time()
    print("Request End:", end_time)
    print("HTTP Status:", res.status_code)
    print("Response Length:", len(res.text))
    print("Response Text:", res.text)
    print("Duration:", end_time - start_time)
except Exception as e:
    print("Request failed:", e)
