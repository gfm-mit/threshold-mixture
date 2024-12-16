import json
import pprint
import anthropic
import requests

with open('./data/icml_2024_poster.json', 'r') as f:
    data = json.load(f)['notes']

tpl_url = "https://openreview.net/{}"

def process(icml_dict):
  icml_dict = {
    k: v['value']
    for k, v in icml_dict['content'].items()
  }
  pdf_url = tpl_url.format(icml_dict['pdf'])
  response = requests.get(pdf_url)
  filename = "pdfs/{}.pdf".format(
    icml_dict['paperhash'].replace('|', '_')
  )
  with open(filename, 'wb') as f:
      f.write(response.content)

process(data[0])

with open('llm/anthropic.key', 'r') as f:
    key = f.read()
client = anthropic.Anthropic(api_key=key)