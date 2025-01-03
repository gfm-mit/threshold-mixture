import json
import os
import os
import pprint
import requests
import time
import tqdm
import py.openreview
import py.pdf
import py.anthropic


def process(icml_dict, overwrite=False):
  icml_dict = {
    k: v['value']
    for k, v in icml_dict['content'].items()
  }
  tpl_url = "https://openreview.net/{}"
  pdf_url = tpl_url.format(icml_dict['pdf'])
  raw_filename = "raw_pdfs/{}.pdf".format(
    icml_dict['paperhash'].replace('|', '_')
  )
  stripped_filename = "stripped_pdfs/{}.pdf".format(
    icml_dict['paperhash'].replace('|', '_')
  )
  if os.path.exists(stripped_filename) and not overwrite:
    print("PDF already exists")
    return stripped_filename
  response = requests.get(pdf_url)
  with open(raw_filename, 'wb') as f:
      f.write(response.content)
  py.pdf.clip_and_compress_pdf(raw_filename, stripped_filename, max_pages=8, image_max_size=(100, 100), image_quality=10)
  return stripped_filename

def load_json(kind, api_key=None):
  with open(f"./data/icml_2024_{kind}.json", 'r') as f:
      data = json.load(f)['notes']
  
  for icml_dict in tqdm.cli.tqdm(data):
    paperhash = icml_dict['content']['paperhash']['value']
    raw_path = py.openreview.download(icml_dict, prefix=f"icml_2024_{kind}_", already_downloaded=True)
    #stripped_path = py.pdf.strip_pdf(raw_path, verbose=False)
    text_path = py.pdf.text_pdf(raw_path)
    out_path = text_path.replace('.pdf', '.txt').replace('text_pdfs/', 'summaries/')
    if api_key is not None:
      if os.path.exists(out_path):
        print('file already exists')
      else:
        if True:
          file_size = os.path.getsize(text_path)
          if file_size > 1000000:
            print("skipping large file")
            continue
          py.anthropic.summarize(text_path, out_path, api_key, pdf=False)
          #time.sleep(10)

# Example usage
if __name__ == "__main__":
  with open('local/anthropic.key', 'r') as f:
      api_key = f.read()
  load_json("poster", api_key=api_key)