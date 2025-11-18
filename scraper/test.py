import requests

headers = {"Host": "47.254.197.27"}
proxy = {'https': "127.0.0.1:10809"}
resp = requests.get("https://ibet789.com/", proxies=proxy)
print("resp", resp.text)
