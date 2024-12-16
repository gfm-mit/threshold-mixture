import anthropic
import base64

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
            max_tokens=2048,
            betas=["pdfs-2024-09-25"],
        )
        return response.content[0].text
    except Exception as e:
        raise Exception(f"Error calling Anthropic API: {str(e)}")

def summarize(pdf_path, txt_path, api_key):
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
    question = """
Here is the full text of the research paper you need to analyze:

<research_paper>
{{pdf}}
</research_paper>

You are an AI assistant specializing in analyzing research papers in the field of machine learning and data science. Your task is to examine the content of a research paper and identify which binary classification evaluation metrics are used.

Your goal is to determine which of the following binary classification evaluation metrics are used in the paper:
Recall, Precision, F1, Accuracy, Net Cost, Net Benefit, AUC-ROC, AUC-PR, Decision Curve Analysis, Brier Score, Log Loss, Cross Entropy, Perplexity, RMSE

Follow these steps:

1. Carefully read through the research paper content.
2. In <metric_scan> tags, for each metric in the list above:
   a. Search for mentions of the metric in the paper.
   b. If found, write down relevant quotes that mention or describe the use of the metric.
   c. If not found, note its absence.
3. In <metric_evaluation> tags, analyze your findings for each metric:
   - Determine if it is present in the paper based on the quotes you found.
   - If present, briefly explain the context of its use.
   - If not present, note its absence.
   - Keep your analysis concise to ensure all metrics can be covered.
4. After analyzing all metrics, compile your findings into a structured JSON array.

Your final output should be a JSON array containing objects for each of the listed metrics, regardless of whether they are present in the paper or not. The array should have the following structure:

[{
  "name": "Metric Name",
  "present": true/false,
  "notes": "Brief details or context (max 50 words)"
}]

Ensure that your JSON output:
- Includes all the metrics mentioned in the list above, even if they are not present in the paper.
- Is correctly formatted as an array of dictionaries, with proper syntax.
- Contains brief notes (maximum 50 words per metric) to keep the overall length manageable.

If you find that your analysis is becoming too long (approaching 1024 tokens), prioritize the most relevant and clearly present metrics in your detailed analysis, while still including all metrics in the final JSON output.

Begin your response with your metric scan, followed by your metric evaluation, and then the JSON output.
"""
    try:
        response = query_pdf(pdf_path, question, api_key)
        with open(txt_path, 'w') as f:
            f.write(response)
        #print("Response:", response)
    except Exception as e:
        print(f"Error: {str(e)}")