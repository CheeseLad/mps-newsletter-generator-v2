from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urlparse, parse_qs
import copy
import json
import re
import os
from utils import fetch_google_doc_html, fetch_google_doc_data
from zipline_client import ZiplineImageProcessor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
CONFIG_FILE = os.environ.get("CONFIG_FILE", DEFAULT_CONFIG_FILE)

BLANK_IMAGE_MAPPINGS = {
    "logo": "",
    "secretary": "",
    "chairperson": "",
    "vice-chair": "",
    "events": "",
    "tv-managers": "",
    "tv-members-section": "",
    "fm-managers": "",
    "fm-members-section": "",
    "the-college-view": "",
    "tcv-members-section": "",
    "pro": "",
    "treasurer": "",
    "sponsorship": "",
    "webmaster": "",
    "first-year-rep": ""
}

BLANK_YEAR_ENTRY = {
    "label": "",
    "email_start": "",
    "email_end_message": "",
    "email_end": "",
    "email_end_role": "",
    "section_border_color": "",
    "section_background_color": "",
    "image_mappings": BLANK_IMAGE_MAPPINGS,
}


def _build_blank_config() -> dict:
    return {
        "2026-2027": copy.deepcopy(BLANK_YEAR_ENTRY),
        "2025-2026": copy.deepcopy(BLANK_YEAR_ENTRY),
    }


def _normalize_year_entry(entry: dict) -> dict:
    normalized = copy.deepcopy(BLANK_YEAR_ENTRY)
    if not isinstance(entry, dict):
        return normalized
    for key in (
        "label",
        "email_start",
        "email_end_message",
        "email_end",
        "email_end_role",
        "section_border_color",
        "section_background_color",
    ):
        if key in entry and entry[key] is not None:
            normalized[key] = str(entry[key])
    if "image_mappings" in entry and isinstance(entry["image_mappings"], dict):
        for img_key in normalized["image_mappings"]:
            if img_key in entry["image_mappings"] and entry["image_mappings"][img_key] is not None:
                normalized["image_mappings"][img_key] = str(entry["image_mappings"][img_key]).strip()
    return normalized


def load_year_configs(config_path: str = None) -> dict:
    """
    Load year & theme configurations from JSON file.
    If the JSON file does not exist, seed from bundled config.json if present,
    or generate a blank config.json file on disk and return it.
    """
    path = config_path or CONFIG_FILE
    if not os.path.exists(path):
        initial_cfg = _build_blank_config()
        if path != DEFAULT_CONFIG_FILE and os.path.exists(DEFAULT_CONFIG_FILE):
            try:
                with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
                    raw_seed = json.load(f)
                if isinstance(raw_seed, dict) and raw_seed:
                    initial_cfg = {str(yr): _normalize_year_entry(val) for yr, val in raw_seed.items()}
            except Exception:
                pass
        try:
            parent_dir = os.path.dirname(os.path.abspath(path))
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(initial_cfg, f, indent=2)
        except OSError:
            pass
        return initial_cfg

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict) or not raw:
            return _build_blank_config()
        return {str(yr): _normalize_year_entry(val) for yr, val in raw.items()}
    except Exception:
        return _build_blank_config()


def update_year_config(year: str, year_data: dict, config_path: str = None) -> dict:
    """Update a specific year's configuration and persist it to config.json."""
    path = config_path or CONFIG_FILE
    configs = load_year_configs(path)
    existing = configs.get(year, copy.deepcopy(BLANK_YEAR_ENTRY))
    merged = copy.deepcopy(existing)

    if isinstance(year_data, dict):
        for key in (
            "label",
            "email_start",
            "email_end_message",
            "email_end",
            "email_end_role",
            "section_border_color",
            "section_background_color",
        ):
            if key in year_data and year_data[key] is not None:
                merged[key] = str(year_data[key])
        if "image_mappings" in year_data and isinstance(year_data["image_mappings"], dict):
            for img_key in merged["image_mappings"]:
                if img_key in year_data["image_mappings"] and year_data["image_mappings"][img_key] is not None:
                    merged["image_mappings"][img_key] = str(year_data["image_mappings"][img_key]).strip()

    configs[year] = _normalize_year_entry(merged)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(configs, f, indent=2)
    return configs


def get_year_config(year: str = "2026-2027", overrides: dict = None, config_path: str = None) -> dict:
    """Return a copy of the configuration for the given year merged with any session overrides."""
    configs = load_year_configs(config_path)
    if year in configs:
        cfg = copy.deepcopy(configs[year])
    elif configs:
        first_key = next(iter(configs))
        cfg = copy.deepcopy(configs[first_key])
    else:
        cfg = copy.deepcopy(BLANK_YEAR_ENTRY)

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

