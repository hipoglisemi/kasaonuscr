import requests

url = "https://dunyakatilim.com.tr/kampanyalar/jack-jones"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Accept": "text/html"}
try:
    res = requests.get(url, headers=headers, timeout=15)
    with open("jack_jones.html", "w", encoding="utf-8") as f:
        f.write(res.text)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
