import requests
import zipfile
import io
import os
import re

def extract_doc_id(url: str) -> str:
    """
    Extract the Google Doc ID from a standard sharing URL or raw ID.
    Supports URLs like:
      - https://docs.google.com/document/d/11uTgoWKpr1yEVslZfo3zmMGJFqaHGRg7oaGuQMULCi0/edit?usp=sharing
      - https://docs.google.com/document/d/11uTgoWKpr1yEVslZfo3zmMGJFqaHGRg7oaGuQMULCi0/edit
      - https://docs.google.com/document/d/11uTgoWKpr1yEVslZfo3zmMGJFqaHGRg7oaGuQMULCi0
      - Or direct document ID
    """
    url = url.strip()
    match = re.search(r"/document/d/([a-zA-Z0-9-_]+)", url)
    if match:
        return match.group(1)
    
    # If the user passed just the ID directly
    if re.fullmatch(r"[a-zA-Z0-9-_]{20,}", url):
        return url
        
    raise ValueError("Could not extract Google Document ID from the provided URL. Please provide a valid Google Docs link.")


def fetch_google_doc_data(doc_url: str) -> tuple[str, dict[str, bytes]]:
    """
    Download a public Google Doc as zipped HTML in-memory and return:
      - The extracted HTML content (str)
      - A mapping of image filenames to image bytes (dict[str, bytes])
    Raises clear errors if doc is private or unreachable.
    """
    doc_id = extract_doc_id(doc_url)
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=zip"

    try:
        response = requests.get(export_url, timeout=30)
    except requests.RequestException as e:
        raise RuntimeError(f"Network error while connecting to Google Docs: {e}")

    if response.status_code == 404:
        raise ValueError("Google Document not found. Please verify the link is correct.")
    elif response.status_code in (401, 403):
        raise PermissionError("Access denied. Please ensure the Google Doc sharing setting is set to 'Anyone with the link can view'.")
    elif response.status_code != 200:
        raise RuntimeError(f"Failed to download document from Google Docs (HTTP {response.status_code}). Ensure anyone with the link can view.")

    # Check if Google returned an HTML login page instead of a zip file
    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type and b"accounts.google.com" in response.content[:1000]:
        raise PermissionError("The Google Doc is private. Please update sharing permissions to 'Anyone with the link can view'.")

    try:
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            html_files = [f for f in z.namelist() if f.endswith(".html")]
            if not html_files:
                raise ValueError("No HTML content found inside the exported Google Doc archive.")

            with z.open(html_files[0]) as f:
                html_content = f.read().decode("utf-8")

            images_data = {}
            for name in z.namelist():
                if not name.endswith(".html") and not name.endswith("/"):
                    data = z.read(name)
                    images_data[name] = data
                    base = os.path.basename(name)
                    if base and base != name:
                        images_data[base] = data

            return html_content, images_data
    except zipfile.BadZipFile:
        raise RuntimeError("Received invalid archive from Google Docs. Ensure the document is public ('Anyone with the link can view').")


def fetch_google_doc_html(doc_url: str) -> str:
    """
    Download a public Google Doc as zipped HTML in-memory and return the extracted HTML content.
    Raises clear errors if doc is private or unreachable.
    """
    html_content, _ = fetch_google_doc_data(doc_url)
    return html_content


def download_google_doc_as_zip(doc_url: str, output_folder: str):
    """
    Legacy helper: Download a public Google Doc as zipped HTML and extract it to disk.
    """
    doc_id = extract_doc_id(doc_url)
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=zip"
    response = requests.get(export_url, timeout=30)
    if response.status_code != 200:
        raise Exception(f"Failed to download document. Status code: {response.status_code}")

    os.makedirs(output_folder, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(output_folder)
