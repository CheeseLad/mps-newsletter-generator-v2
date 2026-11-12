from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urlparse, parse_qs
import copy
import re
import os
from utils import fetch_google_doc_html, fetch_google_doc_data
from zipline_client import ZiplineImageProcessor

# Default Image Mappings for 2026-2027
IMAGE_MAPPINGS_2026_2027 = {
    "logo": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/74b4d2c7-4ad7-82f8-8f41-b279d552422a.png",
    "secretary": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/aadc7fc8-d98d-d950-2e47-b56fd1e65270.jpg",
    "chairperson": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/19a7b1c4-a27e-3072-786c-237b706f01bb.jpg",
    "vice-chair": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/9bc7bbfd-659a-25f9-c73c-1851f95cd28b.jpg",
    "events": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/0cc4c6f1-2bef-a941-bf51-5caddaaf6d24.png",
    "tv-managers": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/5be7da8a-9fd2-e145-2ab7-ee8fcc554219.jpg",
    "tv-members-section": "",
    "fm-managers": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/e89e3b5d-0bf1-64ef-4db5-ae20c3cf15a9.jpg",
    "fm-members-section": "",
    "the-college-view": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/fdc09314-3205-726d-438c-5cdd050adefe.jpg",
    "tcv-members-section": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/4422b919-1021-6951-5cb4-50497847e15e.jpg",
    "pro": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/1ad165f5-24b0-f171-6582-89d6206e0d7c.jpg",
    "treasurer": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/6466b48d-61f4-d955-2eee-45e5d305abcd.jpg",
    "sponsorship": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/1b3e7d6f-7b0c-a1f8-58c1-0c12d56c5007.jpg",
    "webmaster": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/05eecf5c-0fee-3f07-d263-a07ead959152.jpg",
    "first-year-rep": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/40816cf7-dd4d-1212-6691-3bef2a4e5913.jpg"
}

# Image Mappings for 2025-2026
IMAGE_MAPPINGS_2025_2026 = {
    "logo": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/74b4d2c7-4ad7-82f8-8f41-b279d552422a.png",
    "secretary": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/8d4bd131-a7d3-d418-91f2-8870248968fc.png",
    "chairperson": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/8b690a41-5bd9-fe79-65d1-25060d854f40.png",
    "vice-chair": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/bfd4fed4-5662-134a-c074-43c1d895558f.png",
    "events": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/836740bd-8bba-e71f-4abd-6b6f269f3c40.png",
    "tv-managers": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/576c2d9d-6e8f-de62-d8bf-e581c70bf805.png",
    "tv-members-section": "",
    "fm-managers": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/2f72cbe2-9106-4372-3ccd-6e7276ec8a6b.png",
    "fm-members-section": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/6020c12c-6a7e-e4bd-1840-158a508d26b8.png",
    "the-college-view": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/8d6a0545-1ec7-c4fc-f53e-38e365fab219.png",
    "tcv-members-section": "",
    "pro": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/b5f2b6bd-6ba8-908b-31ee-cf6e4222c2da.png",
    "treasurer": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/562e070c-25e7-deec-ba02-1c28334344da.png",
    "sponsorship": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/7dbec0d8-26a5-389c-41dd-8cfbf5acf780.png",
    "webmaster": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/e8762186-4454-ec31-ae62-241689058a44.png",
    "first-year-rep": ""
}

# Default Year & Theme Configurations
YEAR_CONFIGS = {
    "2026-2027": {
        "email_start": "You just got the weekly MPS email!",
        "email_end_message": "Have an amazing week <3",
        "email_end": "Seren Hassett Hilliard",
        "email_end_role": "DCU Media Production Society Secretary 26/27",
        "section_border_color": "#0D4C8F",
        "section_background_color": "#7EA3E2",
        "image_mappings": IMAGE_MAPPINGS_2026_2027,
    },
    "2025-2026": {
        "email_start": "You've got mail! The MPS Weekly Email has hit your inbox!",
        "email_end_message": "Have a great week!",
        "email_end": "Jake Farrell",
        "email_end_role": "DCU Media Production Society Secretary 25/26",
        "section_border_color": "#f7b4f1",
        "section_background_color": "#49408d",
        "image_mappings": IMAGE_MAPPINGS_2025_2026,
    },
}


def get_year_config(year: str = "2026-2027", overrides: dict = None) -> dict:
    """Return a copy of the configuration for the given year merged with any session overrides."""
    base_key = "2025-2026" if year == "2025-2026" else "2026-2027"
    cfg = copy.deepcopy(YEAR_CONFIGS[base_key])
    if overrides and isinstance(overrides, dict):
        for key in (
            "email_start",
            "email_end_message",
            "email_end",
            "email_end_role",
            "section_border_color",
            "section_background_color",
        ):
            if key in overrides and overrides[key] is not None:
                cfg[key] = str(overrides[key])
        if "image_mappings" in overrides and isinstance(overrides["image_mappings"], dict):
            for img_key, img_val in overrides["image_mappings"].items():
                if img_key in cfg["image_mappings"] and img_val is not None:
                    cfg["image_mappings"][img_key] = str(img_val).strip()
    return cfg


# Recognized Section Headers
KNOWN_SECTIONS = [
    "EMAIL SUBJECT",
    "EMAIL START",
    "SECRETARY",
    "CHAIRPERSON",
    "VICE-CHAIR",
    "EVENTS",
    "TV MANAGERS",
    "TV MEMBERS SECTION",
    "FM MANAGERS",
    "FM MEMBERS SECTION",
    "THE COLLEGE VIEW",
    "TCV MEMBERS SECTION",
    "PRO",
    "TREASURER",
    "SPONSORSHIP",
    "WEBMASTER",
    "FIRST YEAR REP",
    "EMAIL END"
]

def clean_google_url(url: str) -> str:
    """Unwrap Google redirection links."""
    if not url:
        return ""
    parsed = urlparse(url)
    if "google." in parsed.netloc and parsed.path == "/url":
        qs = parse_qs(parsed.query)
        if "q" in qs:
            return qs["q"][0]
    return url


def linkify_text(soup_ctx: BeautifulSoup, text_node: NavigableString):
    """Automatically convert plain URLs into clickable <a> tags."""
    if text_node.find_parent("a"):
        return
    text = str(text_node)
    pattern = re.compile(r'(https?://[^\s<>"]+)')
    matches = list(pattern.finditer(text))
    if not matches:
        return

    new_elements = []
    last_idx = 0
    for match in matches:
        start, end = match.span()
        url = match.group(1)
        trailing_punct = ""
        while url and url[-1] in ".,!?:;":
            trailing_punct = url[-1] + trailing_punct
            url = url[:-1]
        if url.endswith(")") and "(" not in url:
            trailing_punct = ")" + trailing_punct
            url = url[:-1]

        if start > last_idx:
            new_elements.append(NavigableString(text[last_idx:start]))

        a_tag = soup_ctx.new_tag("a", href=url)
        a_tag.string = url
        new_elements.append(a_tag)

        if trailing_punct:
            new_elements.append(NavigableString(trailing_punct))

        last_idx = end

    if last_idx < len(text):
        new_elements.append(NavigableString(text[last_idx:]))

    for elem in reversed(new_elements):
        text_node.insert_after(elem)
    text_node.extract()


def extract_paragraph_html(soup_ctx: BeautifulSoup, p_elem, image_processor: ZiplineImageProcessor = None) -> str:
    """Clean Google Docs styling from paragraph, preserving hyperlinks, formatting, and images."""
    p = copy.copy(p_elem)

    # 1. Process <img> tags and replace them with placeholder tokens
    image_placeholders = {}
    for i, img in enumerate(p.find_all("img")):
        src = (img.get("src") or "").strip()
        hosted_url = None
        if image_processor:
            try:
                hosted_url = image_processor.process_image_src(src)
            except Exception as e:
                raise RuntimeError(f"Error hosting embedded image '{src}': {e}")
        elif src:
            hosted_url = src

        if hosted_url:
            token = f"__MPS_IMAGE_TOKEN_{i}_{id(img)}__"
            # Format image tag exactly as requested
            image_placeholders[token] = f"<img src='{hosted_url}' style='width: 300px'></img>"
            img.replace_with(soup_ctx.new_string(token))
        else:
            img.decompose()

    # 2. Clean existing <a> tags (unwrap Google redirects, remove Docs styles)
    for a in p.find_all("a"):
        clean_url = clean_google_url(a.get("href", ""))
        a.attrs = {"href": clean_url}
        for inner in a.find_all(True):
            inner.unwrap()

    # 3. Unwrap non-link / non-br formatting tags from Google Docs (like span, font)
    for tag in p.find_all(True):
        if tag.name not in ["a", "br"]:
            tag.unwrap()

    # 4. Auto-link any plain URLs not inside an <a> tag
    text_nodes = [s for s in p.strings if s.parent.name != "a"]
    for s in text_nodes:
        linkify_text(soup_ctx, s)

    result = p.decode_contents().strip()

    # 5. Restore image tags from tokens
    for token, img_tag in image_placeholders.items():
        result = result.replace(token, img_tag)

    return result


def format_section_content(content_text: str) -> str:
    """
    Format section body:
    - Replaces newlines with <br>
    - Ensures images have <br><br> preceding them: <br><br><img src='...' style='width: 300px'></img>
    - Cleans up excessive consecutive line breaks
    """
    if not content_text:
        return ""

    formatted = content_text.replace("\n", "<br>")

    # Normalize multiple breaks before <img to exactly <br><br>
    formatted = re.sub(r'(?:<br\s*/?>\s*)+<img', r'<br><br><img', formatted)

    # If <img is preceded by non-break text (e.g. inline image), insert <br><br>
    formatted = re.sub(r'([^>\s])\s*<img', r'\1<br><br><img', formatted)

    # Strip any leading <br> tags at the very start of the section
    formatted = re.sub(r'^(?:<br\s*/?>\s*)+', '', formatted)

    return formatted.strip()


def parse_doc_html(
    html_content: str,
    images_data: dict = None,
    zipline_url: str = None,
    zipline_token: str = None
) -> dict:
    """
    Parse exported Google Doc HTML and extract sections based on role headers.
    Headers are recognized with format: — SECTION NAME (em dash, en dash, or hyphen).
    Images are extracted and uploaded to Zipline.
    """
    image_processor = ZiplineImageProcessor(
        images_data=images_data,
        zipline_url=zipline_url,
        zipline_token=zipline_token
    )

    soup = BeautifulSoup(html_content, "html.parser")
    role_pattern = re.compile(
        r"^\s*[-—–]+\s*(" + "|".join(map(re.escape, KNOWN_SECTIONS)) + r")\b",
        re.IGNORECASE
    )

    results = {}

    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        match = role_pattern.match(text)
        if match:
            matched_name = match.group(1).strip()
            # Standardize case to match KNOWN_SECTIONS
            current_role = next((s for s in KNOWN_SECTIONS if s.lower() == matched_name.lower()), matched_name.upper())
            collected = []

            for element in p.find_all_next("p"):
                next_text = element.get_text(strip=True)
                has_img = bool(element.find("img"))

                if role_pattern.match(next_text):
                    break

                if next_text or has_img:
                    if current_role == "EMAIL SUBJECT":
                        collected.append(next_text)
                    else:
                        collected.append(extract_paragraph_html(soup, element, image_processor=image_processor))

            results.setdefault(current_role, []).append("\n\n".join(collected))

    return results


def generate_newsletter_from_html(
    raw_html: str,
    year: str = "2026-2027",
    template_dir: str = ".",
    images_data: dict = None,
    zipline_url: str = None,
    zipline_token: str = None,
    overrides: dict = None
) -> dict:
    """
    Generate the complete newsletter HTML from raw Google Doc HTML.
    Returns a dict with 'subject', 'html', and 'sections_found'.
    """
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("template.html")

    results = parse_doc_html(
        raw_html,
        images_data=images_data,
        zipline_url=zipline_url,
        zipline_token=zipline_token
    )

    # Determine year configuration (merged with any user overrides)
    cfg = get_year_config(year, overrides=overrides)
    image_mappings = cfg["image_mappings"]
    email_start = cfg["email_start"]
    email_end_message = cfg["email_end_message"]
    email_end = cfg["email_end"]
    email_end_role = cfg["email_end_role"]
    section_border_color = cfg["section_border_color"]
    section_background_color = cfg["section_background_color"]

    sections = []

    # If SECRETARY is present in results, add it first
    if "SECRETARY" in results and results["SECRETARY"][0].strip():
        sec_content = format_section_content(results["SECRETARY"][0])
        sections.append({
            "title": "SECRETARY",
            "image": image_mappings.get("secretary", ""),
            "content": sec_content
        })

    # Add all other content sections in the order they were parsed
    for section, contents in results.items():
        if section.startswith("EMAIL") or section == "SECRETARY":
            continue
        
        content_text = contents[0].strip() if contents else ""
        if not content_text:
            continue

        section_image = image_mappings.get(section.replace(" ", "-").lower(), "")
        formatted_content = format_section_content(content_text)

        sections.append({
            "title": section,
            "image": section_image,
            "content": formatted_content
        })

    email_subject = results.get("EMAIL SUBJECT", ["MPS Weekly Newsletter"])[0]

    context = {
        "email_subject": email_subject,
        "header_image": image_mappings.get("logo", ""),
        "email_start": email_start,
        "email_end_message": email_end_message,
        "email_end": email_end,
        "email_end_role": email_end_role,
        "copyright_year": datetime.now().year,
        "sections": sections,
        "section_border_color": section_border_color,
        "section_border_colour": section_border_color,
        "section_background_color": section_background_color,
        "section_background_colour": section_background_color,
        "UnsubscribeURL": "{{ UnsubscribeURL }}",
        "TrackView": "{{ TrackView }}",
        "MessageURL": "{{ MessageURL }}",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    rendered_html = template.render(context)

    return {
        "subject": email_subject,
        "html": rendered_html,
        "sections_found": [s["title"] for s in sections],
        "context": context
    }


def generate_newsletter_from_url(
    doc_url: str,
    year: str = "2026-2027",
    template_dir: str = ".",
    zipline_url: str = None,
    zipline_token: str = None,
    overrides: dict = None
) -> dict:
    """Download Google Doc HTML and images from URL and generate newsletter."""
    raw_html, images_data = fetch_google_doc_data(doc_url)
    return generate_newsletter_from_html(
        raw_html,
        year=year,
        template_dir=template_dir,
        images_data=images_data,
        zipline_url=zipline_url,
        zipline_token=zipline_token,
        overrides=overrides
    )

