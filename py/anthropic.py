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
    question = """
You are an AI assistant specializing in analyzing research papers, particularly in the field of machine learning and data science. Your task is to examine the content of a research paper and identify which binary classification evaluation metrics are used.

Your goal is to determine which of the following binary classification evaluation metrics are used in the paper:
Recall, Precision, F1, Accuracy, Net Cost, Net Benefit, AUC-ROC, AUC-PR, Decision Curve Analysis, Brier Score, Log Loss, Cross Entropy, Perplexity, RMSE

Please follow these steps:

1. Analyze the PDF content and identify any mentions of the listed metrics or related concepts.
2. For each metric, determine whether it is present in the paper.
3. If a metric is present, note any relevant details or context about its use.
4. Compile your findings into a structured JSON format.

Conduct your analysis inside <metric_analysis> tags. In your analysis, consider each metric individually and provide brief notes on why you believe it is or isn't present in the paper. Quote relevant text from the PDF content for each metric. It's OK for this section to be quite long.

Your final output should be a JSON array containing objects for each of the listed metrics, regardless of whether they are present in the paper or not. Each object should have the following structure:

{
  "name": "Metric Name",
  "present": true/false,
  "notes": "Any relevant details or context"
}

Ensure that your JSON output includes all the metrics mentioned in the list above, even if they are not present in the paper. For metrics not present, set "present" to false and include a brief note explaining their absence.
    """
    try:
        response = query_pdf(pdf_path, question, api_key)
        with open(txt_path, 'w') as f:
            f.write(response)
        #print("Response:", response)
    except Exception as e:
        print(f"Error: {str(e)}")