# app/ai.py
import os
import requests
from textwrap import dedent
from datetime import datetime

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def _call_gemini(prompt: str) -> str | None:
    if not GEMINI_API_KEY:
        return None
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    try:
        r = requests.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.4, "maxOutputTokens": 4000}
            },
            timeout=60
        )
        r.raise_for_status()
        data = r.json()
        cand = data.get("candidates", [{}])[0]
        parts = cand.get("content", {}).get("parts", [])
        if parts:
            text = parts[0].get("text", "")
            return text
    except Exception:
        return None
    return None

def _extract_html(maybe_md: str) -> str:
    if "```" in maybe_md:
        import re
        m = re.search(r"```html\s*([\s\S]*?)```", maybe_md, re.I)
        if not m:
            m = re.search(r"```\s*([\s\S]*?)```", maybe_md)
        if m:
            return m.group(1)
    return maybe_md

def _template_index(brief: str, checks: list[str]) -> str:
    title = " ".join(brief.split()[:6]) or "Generated App"
    now = datetime.utcnow().isoformat()
    return dedent(f"""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>{title}</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"/>
      <style>body{{padding:2rem}}</style>
    </head>
    <body>
      <main class="container">
        <h1 class="mb-3">{title}</h1>
        <p class="text-muted">{brief}</p>
        <div id="app"></div>
        <hr/>
        <small class="text-muted">Generated {now}Z</small>
      </main>
      <script>
      // Add your task-specific JS here based on the brief/checks
      console.log("Checks:", {checks});
      // Example: if brief mentions Hello World:
      if ({'"hello world"' in brief.lower()}) {{
          const d = new Date();
          document.title = "{title}";
          document.getElementById("app").innerHTML =
            "<h2>Hello World</h2><p>Today: " + d.toISOString().split('T')[0] + "</p>";
      }}
      </script>
    </body>
    </html>
    """)

def _readme(brief: str, checks: list[str]) -> str:
    lines = "\n".join(f"- {c}" for c in checks)
    return dedent(f"""\
    # Auto-generated App

    **Brief:** {brief}

    ## Features / Checks
    {lines}

    ## Usage
    Open `index.html` in a browser, or visit the GitHub Pages link.

    ## Tech
    - Pure HTML/CSS/JS (Bootstrap via CDN)
    - Hosted on GitHub Pages

    ## License
    MIT
    """)

def _license_mit() -> str:
    year = datetime.utcnow().year
    return dedent(f"""\
    MIT License

    Copyright (c) {year}

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to do so, subject to the
    following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
    """)

def process_attachments(attachments: list[dict]) -> str:
    """Return a short summary string of attachments for prompting (optional)."""
    if not attachments:
        return ""
    out = []
    for att in attachments:
        try:
            name = att.get("name", "file")
            url = att.get("url", "")
            header, data = url.split(",", 1)
            mime = header.split(";")[0].split(":")[1] if ":" in header else "unknown"
            # Keep short preview if base64
            if "base64" in header:
                # avoid decoding huge data; just show note
                preview = f"(base64 {mime}, length {len(data)} chars)"
            else:
                preview = data[:300]
            out.append(f"{name} - {preview}")
        except Exception:
            out.append(f"{att.get('name','file')} - (unreadable)")
    return "\n".join(out)

def generate_code(brief: str, checks: list[str], attachments: list[dict]) -> dict:
    # Try LLM
    attach_note = process_attachments(attachments)
    prompt = f"""You are an expert web developer. Create a COMPLETE single-file HTML app that satisfies:

BRIEF:
{brief}

CHECKS (must pass):
{chr(10).join('- ' + c for c in checks)}

ATTACHMENTS (summary):
{attach_note}

Rules:
- Output ONE valid HTML document starting with <!DOCTYPE html>.
- Inline CSS in <style>, inline JS in <script>.
- Use Bootstrap 5 via CDN.
- No placeholders. Make it actually work for the brief.
- Add brief comments.
"""
    html = _call_gemini(prompt)
    if html:
        html = _extract_html(html)
    if not html or "<!DOCTYPE" not in html:
        html = _template_index(brief, checks)
    return {
        "index.html": html.strip(),
        "README.md": _readme(brief, checks),
        "LICENSE": _license_mit()
    }

def generate_updates(task_info: dict, brief: str, checks: list[str], attachments: list[dict]) -> dict:
    # Similar to generate_code but framed as update
    base_brief = task_info["round1"]["brief"]
    combined = base_brief + "\n\nUPDATE:\n" + brief
    attach_note = process_attachments(attachments)
    prompt = f"""Update the existing app to satisfy the new requirements.

ORIGINAL BRIEF:
{base_brief}

NEW BRIEF:
{brief}

NEW CHECKS:
{chr(10).join('- ' + c for c in checks)}

ATTACHMENTS:
{attach_note}

Rules:
- Keep existing functionality working.
- Provide a single, complete updated index.html (inline CSS/JS, Bootstrap 5).
"""
    html = _call_gemini(prompt)
    if html:
        html = _extract_html(html)
    if not html or "<!DOCTYPE" not in html:
        html = _template_index(combined, checks)
    return {
        "index.html": html.strip(),
        "README.md": _readme(combined, checks)
    }
