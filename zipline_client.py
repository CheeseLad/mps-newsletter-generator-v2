import os
import re
import json
import base64
import mimetypes
from urllib.parse import urlparse
import requests

DEFAULT_ZIPLINE_URL = "http://localhost:3000"


def get_zipline_config(zipline_url: str = None, zipline_token: str = None) -> tuple[str, str]:
    """
    Resolve Zipline URL and Token from explicit arguments, environment variables, or defaults.
    """
    url = (zipline_url or os.environ.get("ZIPLINE_URL") or os.environ.get("ZIPLINE_HOST") or DEFAULT_ZIPLINE_URL).strip().rstrip("/")
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"http://{url}"

    token = zipline_token if zipline_token is not None else os.environ.get("ZIPLINE_TOKEN", os.environ.get("ZIPLINE_API_KEY", ""))
    token = token.strip()
    return url, token


def parse_zipline_response(response_text: str, zipline_url: str) -> str:
    """
    Extract the direct image URL from a Zipline upload response.
    Supports:
      - Zipline v3: {"files": ["https://host/u/xyz.png"]}
      - Zipline v4: {"files": [{"url": "https://host/u/xyz.png"}]}
      - Direct object: {"url": "https://host/u/xyz.png"}
      - Plain text URL response
      - Relative URLs (prepends zipline_url)
    """
    url = ""
    try:
        data = json.loads(response_text)
        if isinstance(data, dict):
            if "files" in data and isinstance(data["files"], list) and len(data["files"]) > 0:
                first = data["files"][0]
                if isinstance(first, str):
                    url = first
                elif isinstance(first, dict):
                    url = first.get("url") or first.get("rawUrl") or first.get("directUrl") or ""
            elif "url" in data and isinstance(data["url"], str):
                url = data["url"]
            elif "data" in data and isinstance(data["data"], dict) and "url" in data["data"]:
                url = data["data"]["url"]
        elif isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], str):
                url = data[0]
            elif isinstance(data[0], dict):
                url = data[0].get("url", "")
    except Exception:
        url = response_text.strip()

    if not url:
        raise ValueError(f"Could not extract image URL from Zipline response: {response_text[:200]}")

    # If Zipline returned a relative path (e.g. /u/abc.png), prepend the base host
    if url.startswith("/"):
        url = f"{zipline_url.rstrip('/')}{url}"

    return url


def upload_to_zipline(
    image_bytes: bytes,
    filename: str = "image.png",
    zipline_url: str = None,
    zipline_token: str = None,
    timeout: int = 30
) -> str:
    """
    Upload image bytes to a Zipline instance and return the hosted public URL.
    """
    if not image_bytes:
        raise ValueError("Cannot upload empty image data to Zipline.")

    host_url, token = get_zipline_config(zipline_url, zipline_token)

    # Detect MIME type
    content_type, _ = mimetypes.guess_type(filename)
    if not content_type:
        if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            content_type = "image/png"
            if not filename.endswith(".png"):
                filename += ".png"
        elif image_bytes.startswith(b"\xff\xd8\xff"):
            content_type = "image/jpeg"
            if not (filename.endswith(".jpg") or filename.endswith(".jpeg")):
                filename += ".jpg"
        elif image_bytes.startswith(b"GIF8"):
            content_type = "image/gif"
            if not filename.endswith(".gif"):
                filename += ".gif"
        elif image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:16]:
            content_type = "image/webp"
            if not filename.endswith(".webp"):
                filename += ".webp"
        else:
            content_type = "application/octet-stream"

    upload_endpoint = f"{host_url}/api/upload"

    headers = {
        "x-zipline-format": "random"
    }
    if token:
        headers["Authorization"] = token

    files = {
        "file": (filename, image_bytes, content_type)
    }

    try:
        response = requests.post(
            upload_endpoint,
            headers=headers,
            files=files,
            timeout=timeout
        )
    except requests.RequestException as e:
        raise RuntimeError(
            f"Could not connect to Zipline instance at '{host_url}'. "
            f"Please ensure your local Zipline instance is running. (Error: {e})"
        )

    if response.status_code not in (200, 201):
        err_msg = response.text[:300]
        try:
            err_json = response.json()
            if isinstance(err_json, dict):
                err_msg = err_json.get("error") or err_json.get("message") or err_msg
        except Exception:
            pass
        raise RuntimeError(f"Zipline upload failed (HTTP {response.status_code}): {err_msg}")

    return parse_zipline_response(response.text, host_url)


class ZiplineImageProcessor:
    """
    Handles image extraction, caching, and uploading to Zipline for newsletter sections.
    """
    def __init__(
        self,
        images_data: dict = None,
        zipline_url: str = None,
        zipline_token: str = None
    ):
        self.images_data = images_data or {}
        self.zipline_url, self.zipline_token = get_zipline_config(zipline_url, zipline_token)
        self.cache: dict[str, str] = {}

    def process_image_src(self, src: str) -> str:
        """
        Takes an image src (archive path, base64 data, or URL) and uploads to Zipline.
        Returns the hosted Zipline URL.
        """
        if not src:
            return ""

        if src in self.cache:
            return self.cache[src]

        img_bytes = None
        clean_src = src.replace("\\", "/")
        filename = os.path.basename(clean_src) or "image.png"

        # 1. Lookup in images extracted from Google Doc zip archive
        if clean_src in self.images_data:
            img_bytes = self.images_data[clean_src]
        elif filename in self.images_data:
            img_bytes = self.images_data[filename]
        elif src in self.images_data:
            img_bytes = self.images_data[src]
        else:
            for k, v in self.images_data.items():
                if k.endswith(filename) or filename.endswith(k):
                    img_bytes = v
                    break

        # 2. Base64 Data URI
        if not img_bytes and src.startswith("data:image/"):
            try:
                header, b64_str = src.split(",", 1)
                img_bytes = base64.b64decode(b64_str)
                mime = header.split(";")[0].replace("data:", "")
                ext = mime.split("/")[-1]
                if ext == "jpeg":
                    ext = "jpg"
                filename = f"image.{ext}"
            except Exception as e:
                raise ValueError(f"Failed to decode base64 image: {e}")

        # 3. External HTTP(S) URL
        if not img_bytes and (src.startswith("http://") or src.startswith("https://")):
            # If already hosted on the target Zipline instance, reuse it
            parsed_zipline = urlparse(self.zipline_url)
            parsed_src = urlparse(src)
            if parsed_zipline.netloc and parsed_zipline.netloc.lower() == parsed_src.netloc.lower():
                self.cache[src] = src
                return src

            # Download external image and re-host on Zipline
            try:
                resp = requests.get(src, timeout=15)
                if resp.status_code == 200:
                    img_bytes = resp.content
                    if "." in filename:
                        filename = filename
                    else:
                        filename = "image.png"
                else:
                    self.cache[src] = src
                    return src
            except Exception:
                # If network fetch fails, fallback to original URL
                self.cache[src] = src
                return src

        if not img_bytes:
            raise ValueError(f"Image source '{src}' was not found in the Google Doc archive.")

        hosted_url = upload_to_zipline(
            image_bytes=img_bytes,
            filename=filename,
            zipline_url=self.zipline_url,
            zipline_token=self.zipline_token
        )

        self.cache[src] = hosted_url
        return hosted_url

