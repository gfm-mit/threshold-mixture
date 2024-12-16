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

def strip_large_images(input_file, output_file, size_threshold_kb=1):
    """
    Strips images larger than the specified threshold from a PDF file,
    including images inside forms.
    
    Args:
        input_file (str): Path to input PDF file
        output_file (str): Path to output PDF file
        size_threshold_kb (float): Size threshold in kilobytes (default: 1)
    """
    # Convert threshold to bytes
    size_threshold = size_threshold_kb * 1024
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_path = temp_file.name
        
        # Read the input PDF
        reader = PdfReader(input_file)
        writer = PdfWriter()
        
        # Process each page
        for page_num, page in enumerate(reader.pages, 1):
            if "/Resources" in page:
                resources = page["/Resources"]
                
                # Process XObjects (including forms)
                if "/XObject" in resources:
                    xobjects = resources["/XObject"]
                    for key in list(xobjects.keys()):
                        try:
                            xobject = xobjects[key]
                            location = f"Page{page_num}->{key}"
                            
                            # Handle forms (which might contain images)
                            if xobject.get("/Subtype") == "/Form":
                                process_form_xobject(xobject, size_threshold, location)
                            
                            # Handle direct images
                            elif process_image_xobject(xobject, size_threshold, location):
                                del xobjects[key]
                                
                        except Exception as e:
                            print(f"Warning: Error processing XObject {key}: {str(e)}")
                
                # Process regular images
                if "/Images" in resources:
                    images = resources["/Images"]
                    for key in list(images.keys()):
                        try:
                            image = images[key]
                            location = f"Page{page_num}->Images->{key}"
                            if process_image_xobject(image, size_threshold, location):
                                del images[key]
                        except Exception as e:
                            print(f"Warning: Error processing Image {key}: {str(e)}")
            
            # Add the modified page to the writer
            writer.add_page(page)
        
        # Write to temporary file first
        with open(temp_path, "wb") as temp_output:
            writer.write(temp_output)
        
        # If input and output are different, directly move the temp file
        if input_file != output_file:
            os.rename(temp_path, output_file)
        else:
            # If they're the same, we need to do a replace
            os.remove(input_file)
            os.rename(temp_path, output_file)

def clip_and_compress_pdf(name0, name1, max_pages=8, image_max_size=(100, 100), image_quality=10):
    strip_large_images(name0, name1, size_threshold_kb=1)

# Example usage
if __name__ == "__main__":
    strip_large_xobjects("input.pdf", "output.pdf", size_threshold_kb=1)