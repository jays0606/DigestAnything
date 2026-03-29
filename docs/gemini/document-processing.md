# Gemini Document Processing

Gemini models can process documents in PDF format, using native vision to
understand entire document contexts. This goes beyond just text extraction,
allowing Gemini to:

- Analyze and interpret content, including text, images, diagrams, charts, and tables, even in long documents up to 1000 pages.
- Extract information into structured output formats.
- Summarize and answer questions based on both the visual and textual elements in a document.
- Transcribe document content (e.g. to HTML), preserving layouts and formatting, for use in downstream applications.

## Passing PDF data inline

Best suited for smaller documents or temporary processing.

### Python

```python
from google import genai
from google.genai import types
import httpx

client = genai.Client()

doc_url = "https://discovery.ucl.ac.uk/id/eprint/10089234/1/343019_3_art_0_py4t4l_convrt.pdf"

# Retrieve and encode the PDF byte
doc_data = httpx.get(doc_url).content

prompt = "Summarize this document"
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[
        types.Part.from_bytes(
            data=doc_data,
            mime_type='application/pdf',
        ),
        prompt
    ]
)

print(response.text)
```

### From local file

```python
from google import genai
from google.genai import types
import pathlib

client = genai.Client()

filepath = pathlib.Path('file.pdf')

prompt = "Summarize this document"
response = client.models.generate_content(
  model="gemini-3-flash-preview",
  contents=[
      types.Part.from_bytes(
        data=filepath.read_bytes(),
        mime_type='application/pdf',
      ),
      prompt])
print(response.text)
```

## Uploading PDFs using the Files API

Recommended for larger files or when you intend to reuse a document across
multiple requests. Improves request latency and reduces bandwidth usage.

> **Note:** The Files API is available at no cost in all regions where the Gemini API is available. Uploaded files are stored for 48 hours.

### Large PDFs from URLs

```python
from google import genai
from google.genai import types
import io
import httpx

client = genai.Client()

long_context_pdf_path = "https://www.nasa.gov/wp-content/uploads/static/history/alsj/a17/A17_FlightPlan.pdf"

# Retrieve and upload the PDF using the File API
doc_io = io.BytesIO(httpx.get(long_context_pdf_path).content)

sample_doc = client.files.upload(
  file=doc_io,
  config=dict(
    mime_type='application/pdf')
)

prompt = "Summarize this document"

response = client.models.generate_content(
  model="gemini-3-flash-preview",
  contents=[sample_doc, prompt])
print(response.text)
```

### Large PDFs stored locally

```python
from google import genai
from google.genai import types
import pathlib

client = genai.Client()

file_path = pathlib.Path('large_file.pdf')

sample_file = client.files.upload(
    file=file_path,
)

prompt="Summarize this document"

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[sample_file, "Summarize this document"])
print(response.text)
```

## Passing multiple PDFs

The Gemini API can process multiple PDF documents (up to 1000 pages) in a single
request.

```python
from google import genai
import io
import httpx

client = genai.Client()

doc_url_1 = "https://arxiv.org/pdf/2312.11805"
doc_url_2 = "https://arxiv.org/pdf/2403.05530"

doc_data_1 = io.BytesIO(httpx.get(doc_url_1).content)
doc_data_2 = io.BytesIO(httpx.get(doc_url_2).content)

sample_pdf_1 = client.files.upload(
  file=doc_data_1,
  config=dict(mime_type='application/pdf')
)
sample_pdf_2 = client.files.upload(
  file=doc_data_2,
  config=dict(mime_type='application/pdf')
)

prompt = "What is the difference between each of the main benchmarks between these two papers? Output these in a table."

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[sample_pdf_1, sample_pdf_2, prompt]
)

print(response.text)
```

## Technical details

- PDF files up to 50MB or 1000 pages
- Each document page is equivalent to 258 tokens
- Larger pages scaled down to max 3072 x 3072, smaller pages scaled up to 768 x 768

### Gemini 3 models

Gemini 3 introduces granular control over multimodal vision processing with the
`media_resolution` parameter (low, medium, or high per individual media part).

1. **Native text inclusion:** Text natively embedded in the PDF is extracted and provided to the model.
2. **Billing & token reporting:**
   - You are **not charged** for tokens originating from the extracted **native text** in PDFs.
   - Tokens generated from processing PDF pages (as images) are counted under the `IMAGE` modality.

### Best practices

- Rotate pages to the correct orientation before uploading.
- Avoid blurry pages.
- If using a single page, place the text prompt after the page.
