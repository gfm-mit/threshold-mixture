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
                    "type": "image",
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
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            messages=messages,
            max_tokens=1024
        )
        return response.content[0].text
    except Exception as e:
        raise Exception(f"Error calling Anthropic API: {str(e)}")

process(data[0])

with open('llm/anthropic.key', 'r') as f:
    key = f.read()
client = anthropic.Anthropic(api_key=key)