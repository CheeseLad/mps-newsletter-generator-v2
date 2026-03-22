import re
import os
import json
from bs4 import BeautifulSoup
from utils import download_google_doc_as_zip
from email_docs import email_docs

sections = [
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
]

role_pattern = re.compile(
    r"^\s*—\s*(" + "|".join(map(re.escape, sections)) + r")\b"
)

results = {}

for email in email_docs:
    doc_url = email_docs[email]
    if doc_url:
        print(f"Processing {email} from {doc_url}")
        email_results = {}
    
        output_folder = f".\\tmp_awards\\{email.replace(' ', '_')}"

        os.makedirs(output_folder, exist_ok=True)

        if not os.listdir(output_folder):
            print(f"Downloading and extracting {email} to {output_folder}")
            download_google_doc_as_zip(doc_url, output_folder)

        for filename in os.listdir(output_folder):
            if filename.endswith(".html"):
                html_path = os.path.join(output_folder, filename)
                break

        with open(html_path, "r", encoding="utf-8") as f:
            print(f"Reading HTML from: {html_path}")
            html = f.read()
        soup = BeautifulSoup(html, "html.parser")

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

                email_results.setdefault(current_role, []).append("\n\n".join(collected))

        sections = []

        for section in email_results:
            content = email_results[section][0]

            sections.append({
                   "title": section,
                "content": content
            })
            print(f"  Found section: {section} with content length: {len(content.strip())}")
        results[email] = sections

with open("email_awards.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)

print("\n--- Email Awards ---")
section_counts = {}
for email, sections in results.items():
    print(f"{email}: {len(sections)} sections")
    for section in sections:
        section_counts[section['title']] = section_counts.get(section['title'], 0)
        if len(section['content'].strip()) > 0:
            if section['title'] == "FIRST YEAR REP" and len(section['content'].strip()) == 91:
                pass
            elif section['title'] == "TCV MEMBERS SECTION" and len(section['content'].strip()) == 91:
                pass
            else:
                section_counts[section['title']] += 1

print("\nTotal Emails: ", len(results))

print("\nSection Counts:")
for section, count in section_counts.items():
    print(f"  {section}: {count}")