from jinja2 import Environment, FileSystemLoader
from datetime import datetime

env = Environment(loader=FileSystemLoader("."))
template = env.get_template("template.html")

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

from bs4 import BeautifulSoup
import re

with open("doc.html", "r", encoding="utf-8") as f:
    html = f.read()
soup = BeautifulSoup(html, "html.parser")

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
    "content": """Hey y’all! Hope you had a wonderful weekend and are enjoying the start of reading week! Can't believe it's only a few days to Berlin! 👀<br><br>

        🇩🇪 Berlin Countdown - 4 days! 🇩🇪<br><br>

        🐱 Cat of the Week 🐱<br><br>

        <img src='https://i.imgur.com/CHieRtj.gif' style='width: 300px'></img><br><br>

        POV: You flying on the plane to Berlin on Thursday!<br><br>

        See you on the flippity flop,<br>
        Jake 📩""",
})

for section in results:
    if not section.startswith("EMAIL") and len(results[section][0].strip()) != 0:
        section_image = image_mappings.get(section.replace(" ", "-").lower(), "")
        content = results[section][0].replace("\n", "<br>")
        if section == "SPONSORSHIP":
            content = content.replace("The Kiss of Venus - Paul McCartney and Dominic Fike", " <a href='https://open.spotify.com/track/28kOGtTZzbfQ8fMmTwjRFq?si=FcipfIegQbK8pZnPBVspSg'>The Kiss of Venus - Paul McCartney and Dominic Fike</a>")

        if section == "THE COLLEGE VIEW":
            content += "<br><br><img src='https://i.imgur.com/0GO4IEt.png' style='width: 300px'></img>"

        sections.append({
            "title": section,
            "image": section_image,
            "content": content
        })
    

context = {
    "email_subject": "SEMESTER 2 WEEK 7",
    "header_image": image_mappings["logo"],
    "email_start": "You've got mail! The MPS Weekly Email has hit your inbox! ",
    "sections": sections,
    "UnsubscribeURL": "{{ UnsubscribeURL }}",
    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

rendered_html = template.render(context)

with open("output.html", "w", encoding="utf-8") as f:
    f.write(rendered_html)