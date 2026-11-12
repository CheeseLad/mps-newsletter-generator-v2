import os
import io
import re
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify, flash, redirect, url_for, send_from_directory
from generator import generate_newsletter_from_url, YEAR_CONFIGS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load local .env if present
env_file = os.path.join(BASE_DIR, ".env")
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

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)
app.secret_key = os.environ.get("SECRET_KEY", "mps-newsletter-generator-secret-key")


@app.route("/", methods=["GET", "POST"])
def index():
    error_message = None
    doc_url = ""
    year = "2026-2027"

    if request.method == "POST":
        doc_url = request.form.get("doc_url", "").strip()
        year = request.form.get("year", "2026-2027")

        if not doc_url:
            error_message = "Please enter a Google Doc URL."
            return render_template(
                "index.html",
                error_message=error_message,
                doc_url=doc_url,
                year=year,
                year_configs=YEAR_CONFIGS
            )

        try:
            # Zipline configuration is managed securely server-side
            zipline_url = os.environ.get("ZIPLINE_URL", "http://localhost:3000")
            zipline_token = os.environ.get("ZIPLINE_TOKEN", "")

            result = generate_newsletter_from_url(
                doc_url,
                year=year,
                template_dir=BASE_DIR,
                zipline_url=zipline_url,
                zipline_token=zipline_token
            )
            rendered_html = result["html"]
            subject = result["subject"]
            
            # Format clean filename based on subject or date
            safe_subject = re.sub(r'[^a-zA-Z0-9_\- ]+', '', subject).strip().replace(" ", "-")[:40]
            if not safe_subject:
                safe_subject = f"mps-newsletter-{datetime.now().strftime('%Y-%m-%d')}"
            filename = f"{safe_subject}.html"

            # Return as downloadable attachment
            mem_file = io.BytesIO()
            mem_file.write(rendered_html.encode("utf-8"))
            mem_file.seek(0)

            return send_file(
                mem_file,
                as_attachment=True,
                download_name=filename,
                mimetype="text/html; charset=utf-8"
            )

        except (ValueError, PermissionError, RuntimeError) as e:
            error_message = str(e)
        except Exception as e:
            error_message = f"An unexpected error occurred: {str(e)}"

    return render_template(
        "index.html",
        error_message=error_message,
        doc_url=doc_url,
        year=year,
        year_configs=YEAR_CONFIGS
    )


@app.route("/api/generate", methods=["POST"])
def api_generate():
    """API endpoint for async generate, preview, and download."""
    data = request.get_json(silent=True) or request.form
    doc_url = (data.get("doc_url") or "").strip()
    year = data.get("year", "2026-2027")
    overrides = data.get("overrides") if isinstance(data, dict) else None

    if not doc_url:
        return jsonify({"success": False, "error": "Please provide a Google Doc URL."}), 400

    try:
        # Zipline configuration is strictly managed server-side
        zipline_url = os.environ.get("ZIPLINE_URL", "http://localhost:3000")
        zipline_token = os.environ.get("ZIPLINE_TOKEN", "")

        result = generate_newsletter_from_url(
            doc_url,
            year=year,
            template_dir=BASE_DIR,
            zipline_url=zipline_url,
            zipline_token=zipline_token,
            overrides=overrides
        )
        subject = result["subject"]
        safe_subject = re.sub(r'[^a-zA-Z0-9_\- ]+', '', subject).strip().replace(" ", "-")[:40]
        if not safe_subject:
            safe_subject = f"mps-newsletter-{datetime.now().strftime('%Y-%m-%d')}"
        filename = f"{safe_subject}.html"

        return jsonify({
            "success": True,
            "html": result["html"],
            "subject": subject,
            "sections": result["sections_found"],
            "filename": filename
        })
    except (ValueError, PermissionError, RuntimeError) as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"An unexpected error occurred: {str(e)}"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()}), 200


@app.route("/assets/<path:filename>")
def serve_assets(filename):
    return send_from_directory(os.path.join(BASE_DIR, "assets"), filename)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

