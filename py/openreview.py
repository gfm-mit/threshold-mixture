import json
import os
import os
import pprint
import requests
import time
import tqdm
import py.pdf
import py.anthropic

import argparse

def scrape_urls(kind, count=2275):
    assert kind in ["Poster", "Oral", "Spotlight"]
    tpl = """https://api2.openreview.net/notes?content.venue=ICML%202024%20{}&details=replyCount,presentation&domain=ICML.cc/2024/Conference&invitation=ICML.cc/2024/Conference/-/Submission&limit=400&offset={}"""

    notes = []
    for k in range(0, count, 400):
            # Start of Selection
            url = tpl.format(kind, k)
            response = requests.get(url)
            json_data = response.json()
            notes += json_data['notes']

    return dict(notes=notes, count=len(notes))

def download(icml_dict):
  icml_dict = {
    k: v['value']
    for k, v in icml_dict['content'].items()
  }
  tpl_url = "https://openreview.net/{}"
  pdf_url = tpl_url.format(icml_dict['pdf'])
  raw_filename = "raw_pdfs/{}.pdf".format(
    icml_dict['paperhash'].replace('|', '_')
  )
  if os.path.exists(raw_filename):
    print("PDF already downloaded:", raw_filename)
    return raw_filename
  response = requests.get(pdf_url)
  with open(raw_filename, 'wb') as f:
      f.write(response.content)
  return raw_filename

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pretty-print a JSON file.')
    parser.add_argument('--filename', type=str, help='Path to the JSON file to pretty-print.')
    parser.add_argument('--kind', type=str, help='Used in the OpenReview scraper')
    args = parser.parse_args()
    assert os.path.exists(args.filename)

    if args.kind:
      data = scrape_urls(args.kind)
    else:
      with open(args.filename, 'r') as f:
          data = json.load(f)

    print(f"Count: {data['count']}")
    data_str = json.dumps(data, indent=2)
    with open(args.filename, 'w') as f:
        f.write(data_str)