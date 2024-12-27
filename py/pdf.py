import os
import tempfile
from PyPDF2 import PdfReader, PdfWriter

def process_large_xobject(xobject, size_threshold, location_info="", verbose=True):
    """Helper function to check and potentially remove an image XObject"""
    if hasattr(xobject, "_data"):
        try:
            data_size = len(xobject._data)
            if data_size > size_threshold:
                if verbose:
                    print(f"Removed Object {location_info} ({data_size/1024:.1f}KB)")
                return True
        except Exception as e:
            print(f"Warning: Could not process object {location_info}: {str(e)}")
    if hasattr(xobject, "get_data"):
        try:
            data_size = len(xobject.get_data())
            if data_size > size_threshold:
                if verbose:
                    print(f"Removed Object {location_info} ({data_size/1024:.1f}KB)")
                return True
        except Exception as e:
            print(f"Warning: Could not process object {location_info}: {str(e)}")
    return False

def process_form_xobject(form, size_threshold, parent_key="", verbose=True, ancestors=set()):
    """Process images inside a Form XObject"""
    if "/Resources" in form:
        resources = form["/Resources"]
        if "/XObject" in resources:
            xobjects = resources["/XObject"]
            for key in list(xobjects.keys()):
                try:
                    xobject = xobjects[key]
                    location = f"{parent_key}->Form->{key}" if parent_key else f"Form->{key}"
                    print(location)
                    
                    # Handle nested forms
                    if xobject.get("/Subtype") == "/Form":
                        assert location not in ancestors, "cursed! object tree has a cycle: {}\n{}\n".format(ancestors, location)
                        process_form_xobject(xobject, size_threshold, location, verbose=verbose, ancestors=ancestors | {location})
                    
                    # Handle images within the form
                    if process_large_xobject(xobject, size_threshold, location, verbose=verbose):
                        del xobjects[key]
                        
                except Exception as e:
                    print(f"Warning: Error processing form XObject {key}: {str(e)}")


def remove_large_xobjects(input_filename, output_filename, max_size=1024, max_pages=10, verbose=True):
    """
    Reads a PDF, removes XObjects larger than the specified size, and writes it back out.

    :param input_filename: Path to the input PDF file
    :param output_filename: Path to the output PDF file
    :param max_size: Maximum allowed size for XObjects (in bytes)
    """
    # Open the input PDF file
    print("reading pdf", input_filename)
    reader = PdfReader(input_filename)
    writer = PdfWriter()

    for page_num, page in enumerate(reader.pages, 1):
        if page_num > max_pages:
            break
        if "/Resources" in page:
            resources = page["/Resources"]
            if "/XObject" in resources:
                xobjects = resources["/XObject"]
                to_remove = []

                for key, obj in xobjects.items():
                    # Access the XObject stream
                    xobject = reader.get_object(obj)
                    location = f"Page{page_num}->{key}"
                    # Handle forms (which might contain images)
                    if xobject.get("/Subtype") == "/Form":
                        process_form_xobject(xobject, max_size, location, verbose=verbose, ancestors=set())
                    if process_large_xobject(xobject, max_size, location, verbose=verbose):
                        to_remove.append(key)

                # Remove the large XObjects from the page
                for key in to_remove:
                    del xobjects[key]

        # Add the cleaned-up page to the writer
        writer.add_page(page)

    # Use a temporary file if the input and output filenames are the same
    temp_file = None
    if input_filename == output_filename:
        temp_fd, temp_file = tempfile.mkstemp(suffix='.pdf')
        os.close(temp_fd)  # Close the file descriptor
        output_filename = temp_file

    # Write the updated PDF to the output file
    with open(output_filename, 'wb') as output_file:
        writer.write(output_file)

    # Replace the original file with the updated file if a temporary file was used
    if temp_file:
        os.replace(temp_file, input_filename)

def extract_pdf_text(input_filename, output_filename=None, max_pages=None):
    """
    Extracts text from a PDF file while maintaining reading order.
    
    Args:
        input_filename (str): Path to the input PDF file
        output_filename (str, optional): Path to save the extracted text. If None, returns the text as a string
        max_pages (int, optional): Maximum number of pages to process. If None, processes all pages
    
    Returns:
        str: Extracted text if output_filename is None, otherwise None
    """
    try:
        # Open and read the PDF file
        print(f"Reading PDF: {input_filename}")
        reader = PdfReader(input_filename)
        
        # Determine number of pages to process
        num_pages = len(reader.pages)
        if max_pages is not None:
            num_pages = min(num_pages, max_pages)
        
        # Extract text from each page
        extracted_text = []
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            # Extract text while preserving order
            text = page.extract_text()
            if text.strip():  # Only add non-empty pages
                extracted_text.append(text)
        
        # Join all text with double newlines between pages
        full_text = "\n\n".join(extracted_text)
        
        # If output filename is provided, save to file
        if output_filename:
            os.makedirs(os.path.dirname(output_filename), exist_ok=True)
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f"Text saved to: {output_filename}")
            return None
        
        return full_text
    
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return None

def strip_pdf(raw_filename, verbose=True):
  stripped_filename = raw_filename.replace('raw_pdfs/', 'stripped_pdfs/')
  if os.path.exists(stripped_filename):
      #print("stripped pdf already exists:", stripped_filename)
      return stripped_filename
  remove_large_xobjects(raw_filename, stripped_filename, max_pages=10, max_size=1024, verbose=verbose)
  return stripped_filename

def text_pdf(raw_filename):
  text_filename = raw_filename.replace('raw_pdfs/', 'text_pdfs/')
  if os.path.exists(text_filename):
      #print("stripped pdf already exists:", text_filename)
      return text_filename
  extract_pdf_text(raw_filename, text_filename, max_pages=None)
  return text_filename