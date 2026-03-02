import requests
import zipfile
import io
import os
import re

def extract_doc_id(url: str) -> str:
    """
    Extract the Google Doc ID from a standard sharing URL.
    """
    match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", url)
    if not match:
        raise ValueError("Could not extract document ID from URL.")
    return match.group(1)


def download_google_doc_as_zip(doc_url: str, output_folder: str):
    """
    Download a public Google Doc as zipped HTML and extract it.
    """
    doc_id = extract_doc_id(doc_url)

    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=zip"
    print(f"Downloading from: {export_url}")

    response = requests.get(export_url)
    if response.status_code != 200:
        raise Exception(f"Failed to download document. Status code: {response.status_code}")

    print("Download successful. Extracting...")

    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(output_folder)

    print(f"Extracted to: {os.path.abspath(output_folder)}")