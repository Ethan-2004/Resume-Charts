import time
import requests

def call_gpt_model(prompt_template,api_url, api_key,api_name):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": f"{api_name}",
        "messages": [
            {"role": "user", "content": f"""{prompt_template}
"""}
        ]
    }

    response = requests.post(api_url, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"❌ 请求失败：{response.status_code} - {response.text}"



