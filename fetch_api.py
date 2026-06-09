import urllib.request
import re

try:
    html = urllib.request.urlopen('https://viralops-staging.vercel.app').read().decode('utf-8')
    js_files = re.findall(r'src="(/assets/[^"]+\.js)"', html)
    print(f"Found JS files: {js_files}")
    for j in js_files:
        js_url = 'https://viralops-staging.vercel.app' + j
        print(f"Fetching {js_url}")
        js_content = urllib.request.urlopen(js_url).read().decode('utf-8')
        urls = re.findall(r'https://[^"]*onrender\.com', js_content)
        if urls:
            print(f"Found Render URLs: {set(urls)}")
except Exception as e:
    print(f"Error: {e}")
