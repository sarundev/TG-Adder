import requests
import json
with open('/Users/bongrun/Documents/855314473942/855314473942.session', 'rb') as f:
    res = requests.post('http://127.0.0.1:8000/api/accounts/upload-session', files={'file': f})
print(res.status_code, res.text)
