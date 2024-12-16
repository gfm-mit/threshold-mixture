import json
import pprint
import anthropic
import requests

with open('llm/icml_poster.json', 'r') as f:
    data = json.load(f)['notes']
    data = [d['content'] for d in data]

tpl_url = "https://openreview.net/{}"

pdf_url = tpl_url.format(data[0]['pdf']['value'])
response = requests.get(pdf_url)

with open('downloaded.pdf', 'wb') as f:
    f.write(response.content)

with open('llm/anthropic.key', 'r') as f:
    key = f.read()
client = anthropic.Anthropic(api_key=key)