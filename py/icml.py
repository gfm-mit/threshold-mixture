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

def read_pdf_as_base64(file_path: str) -> str:
    """Read a PDF file and convert it to base64 encoding."""
    with open(file_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def query_pdf(pdf_path: str, question: str, api_key: str) -> str:
    """
    Upload a PDF and ask a question about it using the Anthropic API.
    
    Args:
        pdf_path: Path to the PDF file
        question: Question to ask about the PDF
        api_key: Anthropic API key
    
    Returns:
        str: The model's response
    """
    # Initialize the client
    client = anthropic.Client(api_key=api_key)
    
    # Read and encode the PDF
    try:
        pdf_base64 = read_pdf_as_base64(pdf_path)
    except Exception as e:
        raise Exception(f"Error reading PDF file: {str(e)}")
    
    # Create the message content
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_base64
                    }
                },
                {
                    "type": "text",
                    "text": question
                }
            ]
        }
    ]
    
    # Send the request
    try:
        response = client.beta.messages.create(
            model="claude-3-5-sonnet-20241022",
            messages=messages,
            max_tokens=1024,
            betas=["pdfs-2024-09-25"],
        )
        return response.content[0].text
    except Exception as e:
        raise Exception(f"Error calling Anthropic API: {str(e)}")

def summarize(pdf_path, txt_path, api_key):
    question = "What binary classification evaluation metrics are used in this paper?  In particular does it use any of Recall, Precision, F1, Accuracy, Net Cost, Net Benefit, AUC-ROC, AUC-PR, Decision Curve Analysis, Brier Score, Log Loss, Perplexity, RMSE?"
    try:
        response = query_pdf(pdf_path, question, api_key)
        with open(txt_path, 'w') as f:
            f.write(response)
        #print("Response:", response)
    except Exception as e:
        print(f"Error: {str(e)}")

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
      if os.path.exists(txt_path):
        print('file already exists')
      else:
        summarize(pdf_path, txt_path, api_key)
        time.sleep(1)