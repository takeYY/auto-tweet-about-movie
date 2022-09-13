import requests

url = "http://localhost:8080"
payload = {"refresh_token": "YOUR_REFRESH_TOKEN"}

res = requests.post(url=url, params=payload)


print(res.status_code)
print(res.text)
