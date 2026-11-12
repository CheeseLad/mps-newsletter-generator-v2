#!/usr/bin/env python3
"""
MPS Newsletter Generator
CLI entry point and helper runner.
For web UI, run `python app.py` or `docker compose up`.
"""

import sys
import os
import argparse
from generator import generate_newsletter_from_url

# Load .env if present
env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_file):
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v

DEFAULT_DOC_URL = "https://docs.google.com/document/d/11uTgoWKpr1yEVslZfo3zmMGJFqaHGRg7oaGuQMULCi0/edit?usp=sharing"

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("--serve", "serve", "-s"):
        import app
        port = int(os.environ.get("PORT", 5000))
        print(f"Starting MPS Newsletter Web App on http://localhost:{port}...")
        app.app.run(host="0.0.0.0", port=port, debug=True)
        return

    parser = argparse.ArgumentParser(description="MPS Newsletter Generator")
    parser.add_argument("doc_url", nargs="?", default=DEFAULT_DOC_URL, help="Google Doc URL")
    parser.add_argument("year", nargs="?", default="2026-2027", help="Academic year (2026-2027 or 2025-2026)")
    parser.add_argument("--zipline-url", default=os.environ.get("ZIPLINE_URL", "http://localhost:3000"), help="Zipline instance URL")
    parser.add_argument("--zipline-token", default=os.environ.get("ZIPLINE_TOKEN", ""), help="Zipline API token")

    args = parser.parse_args()

    print(f"Downloading and generating newsletter from: {args.doc_url}")
    print(f"Academic Year / Theme: {args.year}")
    print(f"Zipline Host: {args.zipline_url}")

    try:
        result = generate_newsletter_from_url(
            args.doc_url,
            year=args.year,
            template_dir=".",
            zipline_url=args.zipline_url,
            zipline_token=args.zipline_token
        )
        output_file = "output.html"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["html"])

        print(f"\n[SUCCESS] Generated newsletter with subject: '{result['subject']}'")
        print(f"Sections included ({len(result['sections_found'])}): {', '.join(result['sections_found'])}")
        print(f"Saved to: {os.path.abspath(output_file)}")

    except Exception as e:
        print(f"\n[ERROR] Failed to generate newsletter: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
