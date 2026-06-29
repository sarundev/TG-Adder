import hashlib
import requests

url = "https://khqr.cc/api/payment/request/pNiGKZdBf8OMDhiIiRa5TmzCZiYJ16tB"
secret = "GD2jqnaMErwOTV180AbNzWfjp5clLMPL"
profile_id = "pNiGKZdBf8OMDhiIiRa5TmzCZiYJ16tB"

amounts = ["1", "1.0", "1.00", "100"]

for amount in amounts:
    permutations = [
        f"{amount}{secret}",
        f"{secret}{amount}",
        f"{profile_id}{amount}{secret}",
        f"{secret}{profile_id}{amount}",
        f"{amount}{profile_id}{secret}",
        f"{amount}|{secret}",
        f"{profile_id}{secret}",
        f"{secret}{profile_id}",
        secret
    ]

    for p in permutations:
        h = hashlib.md5(p.encode()).hexdigest()
        res = requests.get(url, params={"amount": amount, "hash": h})
        try:
            data = res.json()
            if data.get("responseCode") != 1:
                print(f"SUCCESS: {amount} {p} -> {data}")
        except:
            pass
