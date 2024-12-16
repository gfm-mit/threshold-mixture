import os
import tempfile
from PyPDF2 import PdfReader, PdfWriter

def process_image_xobject(xobject, size_threshold, location_info=""):
    """Helper function to check and potentially remove an image XObject"""
    if (xobject.get("/Subtype") == "/Image" and 
        hasattr(xobject, "get_data")):
        try:
            data_size = len(xobject.get_data())
            if data_size > size_threshold:
                print(f"Removed Image {location_info} ({data_size/1024:.1f}KB)")
                return True
        except Exception as e:
            print(f"Warning: Could not process image {location_info}: {str(e)}")
    return False

def process_form_xobject(form, size_threshold, parent_key=""):
    """Process images inside a Form XObject"""
    if "/Resources" in form:
        resources = form["/Resources"]
        if "/XObject" in resources:
            xobjects = resources["/XObject"]
            for key in list(xobjects.keys()):
                try:
                    xobject = xobjects[key]
                    location = f"{parent_key}->Form->{key}" if parent_key else f"Form->{key}"
                    
                    # Handle nested forms
                    if xobject.get("/Subtype") == "/Form":
                        process_form_xobject(xobject, size_threshold, location)
                    
                    # Handle images within the form
                    elif process_image_xobject(xobject, size_threshold, location):
                        del xobjects[key]
                        
                except Exception as e:
                    print(f"Warning: Error processing form XObject {key}: {str(e)}")


def remove_large_xobjects(input_filename, output_filename, max_size=1024):
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

    for page in reader.pages:
        if "/Resources" not in page:
            continue
        resources = page["/Resources"]
        if "/XObject" not in resources:
            continue
        xobjects = resources["/XObject"]
        to_remove = []

        for key, obj in xobjects.items():
            # Access the XObject stream
            xobject = reader.get_object(obj)
            if hasattr(xobject, 'get_data'):
                data = xobject.get_data()
                if len(data) > max_size:
                    to_remove.append(key)

            # Handle forms (which might contain images)
            elif xobject.get("/Subtype") == "/Form":
                process_form_xobject(xobject, size_threshold, location)

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

def clip_and_compress_pdf(name0, name1, max_pages=8, image_max_size=(100, 100), image_quality=10):
    remove_large_xobjects(name0, name1, max_size=1024)