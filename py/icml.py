import anthropic
import base64
import io
import json
import os
import os
import pprint
import requests
import shutil
import tempfile
import time
import tqdm
from PIL import Image
from PIL.Image import Resampling
from PIL.Image import open as PILopen
from PyPDF2 import PdfReader, PdfWriter
import zlib
import py.pdf
import py.anthropic


def process(icml_dict, overwrite=False):
  icml_dict = {
    k: v['value']
    for k, v in icml_dict['content'].items()
  }
  tpl_url = "https://openreview.net/{}"
  pdf_url = tpl_url.format(icml_dict['pdf'])
  filename = "pdfs/{}.pdf".format(
    icml_dict['paperhash'].replace('|', '_')
  )
  if os.path.exists(filename) and not overwrite:
    print("file already exists")
  else:
    response = requests.get(pdf_url)
    with open(filename, 'wb') as f:
        f.write(response.content)
  if True:
    py.pdf.clip_and_compress_pdf(filename, filename, max_pages=8, image_max_size=(100, 100), image_quality=10)
  return filename

# Example usage
if __name__ == "__main__":
    with open('./data/icml_2024_poster.json', 'r') as f:
        data = json.load(f)['notes']

    with open('local/anthropic.key', 'r') as f:
        api_key = f.read()
    
    for icml_dict in tqdm.cli.tqdm(data):
      paperhash = icml_dict['content']['paperhash']['value']
      pdf_path = process(icml_dict, overwrite=False)
      txt_path = pdf_path.replace('.pdf', '.txt').replace('pdfs/', 'summaries/')
      #if os.path.exists(txt_path):
        #print('file already exists')
      #else:
        py.anthropic.summarize(pdf_path, txt_path, api_key)
        time.sleep(1)
