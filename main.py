from jinja2 import Environment, FileSystemLoader
from datetime import datetime
from bs4 import BeautifulSoup
from utils import download_google_doc_as_zip
import re
import os

env = Environment(loader=FileSystemLoader("."))
template = env.get_template("template.html")

doc_url = "https://docs.google.com/document/d/1eBwbjuPo0egnXPZXPpUGIhLrIkX4nmrkksercEUeZ7E/edit?usp=sharing"
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

image_mappings = {
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
    "pro": "",
    "treasurer": "",
    "sponsorship": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/7dbec0d8-26a5-389c-41dd-8cfbf5acf780.png",
    "webmaster": "https://mcusercontent.com/a6300fadb6d053a90ae600e49/images/e8762186-4454-ec31-ae62-241689058a44.png",
    "first-year-rep": ""
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
                collected.append(next_text)

        results.setdefault(current_role, []).append("\n\n".join(collected))

sections = []

sections.append({
    "title": "SECRETARY",
    "image": image_mappings["secretary"],
    "content": """Hey {{ .Subscriber.FirstName }}! Hope you had a wonderful weekend and are looking forward to St. Patrick's Day! Thanks everyone for coming to Broadcraft last week, I really enjoyed teaching you all about the ins and outs of OBS!<br><br>
    
        Did you love Seek n Stream? Well you're in luck as it's time for Seek n Stream round 2, this time with an FM twist!<br><br>

        🐱 Cat of the Week 🐱<br><br>

        <img src='https://i.imgur.com/lRRgHGY.gif' style='width: 300px'></img><br><br>

        POV: You listening out for clues on DCUfm at Radio Relay on Thursday!<br><br>

        See you on the flippity flop,<br>
        Jake 📩""",
})

for section in results:
    if not section.startswith("EMAIL") and len(results[section][0].strip()) != 0:
        section_image = image_mappings.get(section.replace(" ", "-").lower(), "")
        content = results[section][0].replace("\n", "<br>")
        #if section == "CHAIRPERSON":
        #    content = content.replace("https://www.dcu.ie/dcu-community/dcu-events/2026/feb/school-communications-alumni-perspectives-navigating-careers", " <a href='https://www.dcu.ie/dcu-community/dcu-events/2026/feb/school-communications-alumni-perspectives-navigating-careers'>https://www.dcu.ie/dcu-community/dcu-events/2026/feb/school-communications-alumni-perspectives-navigating-careers</a>")
        if section == "SPONSORSHIP":
            content = content.replace("Solas - Seo Linn", " <a href='https://open.spotify.com/track/45FlzGlQrfRXtY0ofXXbfp?si=LEjDqtqbRCKa1J6f-dhGIA'>Solas - Seo Linn</a> ")

        #if section == "THE COLLEGE VIEW":
        #    content += "<br><br><img src='https://i.imgur.com/0GO4IEt.png' style='width: 300px'></img>"

        if section == "FM MANAGERS":
             content = content.replace("https://forms.gle/i4UXSu8v5zkmXfcY7", " <a href='https://forms.gle/i4UXSu8v5zkmXfcY7'>https://forms.gle/i4UXSu8v5zkmXfcY7</a> ")

        sections.append({
            "title": section,
            "image": section_image,
            "content": content
        })
    

context = {
    "email_subject": results.get("EMAIL SUBJECT", ["MPS Weekly Newsletter"])[0],
    "header_image": image_mappings["logo"],
    "email_start": "You've got mail! The MPS Weekly Email has hit your inbox! ",
    "sections": sections,
    "UnsubscribeURL": "{{ UnsubscribeURL }}",
    "TrackView": "{{ TrackView }}",
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

rendered_html = template.render(context)

output_file = "output.html"

with open(output_file, "w", encoding="utf-8") as f:
    print(f"Writing output to: {output_file}")
    f.write(rendered_html)