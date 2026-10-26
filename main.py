from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString
from urllib.parse import urlparse, parse_qs
import copy
from utils import download_google_doc_as_zip
import re
import os

env = Environment(loader=FileSystemLoader("."))
template = env.get_template("template.html")

doc_url = "https://docs.google.com/document/d/11uTgoWKpr1yEVslZfo3zmMGJFqaHGRg7oaGuQMULCi0/edit?usp=sharing"
output_folder = ".\\tmp"

delete = False

if delete:
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

    os.rmdir(output_folder)

os.makedirs(output_folder, exist_ok=True)
download_google_doc_as_zip(doc_url, output_folder)

for filename in os.listdir(output_folder):
    if filename.endswith(".html"):
        html_path = os.path.join(output_folder, filename)
        break

with open(html_path, "r", encoding="utf-8") as f:
    print(f"Reading HTML from: {html_path}")
    html = f.read()
soup = BeautifulSoup(html, "html.parser")

"""image_mappings = {
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
}"""

### 2026-2027
image_mappings = {
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
    "tcv-members-section": "",
    "pro": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/1ad165f5-24b0-f171-6582-89d6206e0d7c.jpg",
    "treasurer": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/6466b48d-61f4-d955-2eee-45e5d305abcd.jpg",
    "sponsorship": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/1b3e7d6f-7b0c-a1f8-58c1-0c12d56c5007.jpg",
    "webmaster": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/05eecf5c-0fee-3f07-d263-a07ead959152.jpg",
    "first-year-rep": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/40816cf7-dd4d-1212-6691-3bef2a4e5913.jpg"
}


sections = [
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

def clean_google_url(url):
    if not url:
        return ""
    parsed = urlparse(url)
    if "google." in parsed.netloc and parsed.path == "/url":
        qs = parse_qs(parsed.query)
        if "q" in qs:
            return qs["q"][0]
    return url


def linkify_text(soup_ctx, text_node):
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


def extract_paragraph_html(soup_ctx, p_elem):
    p = copy.copy(p_elem)

    # 1. Clean existing <a> tags (unwrap Google redirects, remove Docs styles)
    for a in p.find_all("a"):
        clean_url = clean_google_url(a.get("href", ""))
        a.attrs = {"href": clean_url}
        for inner in a.find_all(True):
            inner.unwrap()

    # 2. Unwrap non-link / non-br formatting tags from Google Docs (like span, font)
    for tag in p.find_all(True):
        if tag.name not in ["a", "br"]:
            tag.unwrap()

    # 3. Auto-link any plain URLs not inside an <a> tag
    text_nodes = [s for s in p.strings if s.parent.name != "a"]
    for s in text_nodes:
        linkify_text(soup_ctx, s)

    return p.decode_contents().strip()


role_pattern = re.compile(
    r"^\s*—\s*(" + "|".join(map(re.escape, sections)) + r")\b"
)

results = {}

for p in soup.find_all("p"):
    text = p.get_text(strip=True)

    match = role_pattern.match(text)
    if match:
        current_role = match.group(1)
        collected = []

        for element in p.find_all_next("p"):
            next_text = element.get_text(strip=True)

            if role_pattern.match(next_text):
                break

            if next_text:
                if current_role == "EMAIL SUBJECT":
                    collected.append(next_text)
                else:
                    collected.append(extract_paragraph_html(soup, element))

        results.setdefault(current_role, []).append("\n\n".join(collected))

sections = []

sections.append({
    "title": "SECRETARY",
    "image": image_mappings["secretary"],
    "content": """Hey {{ .Subscriber.FirstName }}! Hope you had a wonderful Easter weekend! I can't believe it's time for the last MPS newsletter of 25/26, where has the time gone? <br><br>

        Just wanted to say thanks to each and every one of you for making my experience in MPS so special. It's been a great 4 years of MPS and 3 years on committee,  I've met so many awesome people and have learned so much throughout the years. I'm so glad I discovered MPS during the clubs and socs fair back in first year, can't imagine my college experience without it! Love you all 🫶 🫶<br><br>

        For anyone who hasn't checked out the DCUtv 24/7 Broadcast I launched as part of Swap Week, you can find it here: <a href='https://www.twitch.tv/dcumps'>https://www.twitch.tv/dcumps</a> <br> I'll be closing it at the AGM so tune in before it's gone! <br><br>

        🐱 THE FINAL Cat of the Week 🐱<br><br>

        <img src='https://i.imgur.com/zxMewpB.gif' style='width: 300px'></img><br><br>

        POV: You giving your speeches at the AGM on Tuesday!<br><br>

        See you on the flippity flop,<br>
        Jake 📩""",
})

for section in results:
    if not section.startswith("EMAIL") and len(results[section][0].strip()) != 0:
        section_image = image_mappings.get(section.replace(" ", "-").lower(), "")
        content = results[section][0].replace("\n", "<br>")
        #if section == "CHAIRPERSON":
        #    content = content.replace("https://www.dcu.ie/dcu-community/dcu-events/2026/feb/school-communications-alumni-perspectives-navigating-careers", " <a href='https://www.dcu.ie/dcu-community/dcu-events/2026/feb/school-communications-alumni-perspectives-navigating-careers'>https://www.dcu.ie/dcu-community/dcu-events/2026/feb/school-communications-alumni-perspectives-navigating-careers</a>")
        if section == "CHAIRPERSON":
            content = content.replace("I shall see you all at the AGM for the grand finale…", "I shall see you all at the AGM for the grand finale…<br><br><img src='https://i.imgur.com/ioDZylj.png' style='width: 300px'></img>")

        #if section == "THE COLLEGE VIEW":
        #    content += "<br><br><img src='https://i.imgur.com/0GO4IEt.png' style='width: 300px'></img>"




        #if section == "TV MANAGERS":
        #     content = content.replace("https://www.twitch.tv/dcumps", " <a href='https://www.twitch.tv/dcumps'>https://www.twitch.tv/dcumps</a> ")

        sections.append({
            "title": section,
            "image": section_image,
            "content": content
        })
    

context_2025_2026 = {
    "email_subject": results.get("EMAIL SUBJECT", ["MPS Weekly Newsletter"])[0],
    "header_image": image_mappings["logo"],
    "email_start": results.get("EMAIL START")[0],
    "email_end": "Jake Farrell",
    "email_end_role": "DCU Media Production Society Secretary 25/26",
    "copyright_year": datetime.now().year,
    "sections": sections,
    "section_border_color": "#f7b4f1",
    "section_border_colour": "#f7b4f1",
    "section_background_color": "#49408d",
    "section_background_colour": "#49408d",
    "UnsubscribeURL": "{{ UnsubscribeURL }}",
    "TrackView": "{{ TrackView }}",
    "MessageURL": "{{ MessageURL }}",
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

context_2026_2027 = {
    "email_subject": results.get("EMAIL SUBJECT", ["MPS Weekly Newsletter"])[0],
    "header_image": image_mappings["logo"],
    "email_start": results.get("EMAIL START")[0],
    "email_end": "Seren Hassett Hilliard",
    "email_end_role": "DCU Media Production Society Secretary 26/27",
    "copyright_year": datetime.now().year,
    "sections": sections,
    "section_border_color": "#0D4C8F",
    "section_border_colour": "#0D4C8F",
    "section_background_color": "#7EA3E2",
    "section_background_colour": "#7EA3E2",
    "UnsubscribeURL": "{{ UnsubscribeURL }}",
    "TrackView": "{{ TrackView }}",
    "MessageURL": "{{ MessageURL }}",
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

rendered_html = template.render(context_2026_2027)

output_file = "output.html"

with open(output_file, "w", encoding="utf-8") as f:
    print(f"Writing output to: {output_file}")
    f.write(rendered_html)