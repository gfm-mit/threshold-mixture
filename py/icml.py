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

from PIL.Image import Resampling
from PIL.Image import open as PILopen
from PyPDF2 import PdfReader, PdfWriter



def compress_image_data(image_data, image_format, max_size=(1000, 1000), quality=60):
    """
    Compress an image using PIL/Pillow.
    
    Args:
        image_data (bytes): Original image data
        image_format (str): Format of the input image ('RGB' or 'RGBA')
        max_size (tuple): Maximum dimensions (width, height)
        quality (int): JPEG quality (0-100)
    
    Returns:
        bytes: Compressed image data
    """
    try:
        # Create image from raw data
        if image_format == 'RGBA':
            mode = 'RGBA'
        else:
            mode = 'RGB'
            
        # Get image dimensions from the PDF object
        width = int(size[0])
        height = int(size[1])
        
        # Create Image object from raw data
        img = Image.frombytes(mode, (width, height), image_data)
        
        # Convert RGBA to RGB if necessary
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        
        # Calculate new size while maintaining aspect ratio
        ratio = min(max_size[0] / img.width, max_size[1] / img.height)
        if ratio < 1:
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Save compressed image to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"Error in image compression: {str(e)}")
        return image_data

def clip_and_compress_pdf(input_path, output_path, max_pages=10, image_max_size=(1000, 1000), image_quality=60):
    """
    Creates a new PDF with only the first N pages and compressed images.
    Safely handles cases where input_path and output_path are the same.
    
    Args:
        input_path (str): Path to the input PDF file
        output_path (str): Path where the clipped PDF should be saved
        max_pages (int): Maximum number of pages to include (default: 10)
        image_max_size (tuple): Maximum dimensions for images (width, height)
        image_quality (int): JPEG quality (0-100)
    
    Returns:
        bool: True if successful, False if there was an error
    """
    try:
        # Create a temporary file
        temp_output = None
        using_temp = input_path == output_path
        
        if using_temp:
            temp_fd, temp_output = tempfile.mkstemp(suffix='.pdf')
            os.close(temp_fd)
            actual_output = temp_output
        else:
            actual_output = output_path
            
        # Create PDF reader and writer objects
        reader = PdfReader(input_path)
        writer = PdfWriter()
        
        # Determine how many pages to include
        pages_to_include = min(len(reader.pages), max_pages)
        print(f"Processing {pages_to_include} pages...")
        
        # Process each page
        for page_num in range(pages_to_include):
            page = reader.pages[page_num]
            print(f"Processing page {page_num + 1}")
            
            # Process images on the page if any exist
            if '/Resources' in page and '/XObject' in page['/Resources']:
                xObject = page['/Resources']['/XObject'].get_object()
                
                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        try:
                            global size  # Used in compress_image_data
                            size = (xObject[obj]['/Width'], xObject[obj]['/Height'])
                            
                            if size[0] > image_max_size[0] or size[1] > image_max_size[1]:
                                print(f"Found large image: {size[0]}x{size[1]}")
                                
                                # Extract image data based on colorspace
                                if '/ColorSpace' in xObject[obj]:
                                    if xObject[obj]['/ColorSpace'] == '/DeviceRGB':
                                        mode = 'RGB'
                                    elif xObject[obj]['/ColorSpace'] == '/DeviceCMYK':
                                        print("Skipping CMYK image")
                                        continue
                                    else:
                                        mode = 'RGB'
                                else:
                                    mode = 'RGB'
                                
                                img_data = xObject[obj].get_data()
                                compressed_data = compress_image_data(img_data, mode, image_max_size, image_quality)
                                xObject[obj]._data = compressed_data
                                print("Image compressed successfully")
                                
                        except Exception as e:
                            print(f"Error processing image on page {page_num + 1}: {str(e)}")
                            continue
            
            writer.add_page(page)
        
        # Write the output file
        print(f"Writing compressed PDF to {actual_output}")
        with open(actual_output, 'wb') as output_file:
            writer.write(output_file)
        
        # If we used a temporary file, replace the original
        if using_temp:
            print("Replacing original file with processed version")
            shutil.move(temp_output, output_path)
        
        print("PDF processing completed successfully")
        return True
        
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        # Clean up temporary file if it exists
        if temp_output and os.path.exists(temp_output):
            os.remove(temp_output)
        return False
    finally:
        # Make sure we clean up the temp file if something went wrong
        if temp_output and os.path.exists(temp_output):
            try:
                os.remove(temp_output)
            except:
                pass


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
    return filename
  response = requests.get(pdf_url)
  with open(filename, 'wb') as f:
      f.write(response.content)
  if overwrite:
    clip_and_compress_pdf(filename, filename, 10)
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
      pdf_path = process(icml_dict, overwrite=True)
      txt_path = pdf_path.replace('.pdf', '.txt').replace('pdfs/', 'summaries/')
      #if os.path.exists(txt_path):
      #  print('file already exists')
      #else:
      #  summarize(pdf_path, txt_path, api_key)
      #  time.sleep(1)