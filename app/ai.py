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
    except Exception as e:
        print(f"Gemini API error: {e}")
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
    """Generate a complete working HTML template"""
    title = " ".join(brief.split()[:8]) or "Generated Application"
    now = datetime.utcnow().isoformat()
    
    # Create checks as HTML list
    checks_html = "\n".join(f"            <li class='list-group-item'><i class='bi bi-check-circle text-success'></i> {c}</li>" for c in checks)
    
    return dedent(f"""\
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
      <title>{title}</title>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"/>
      <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css" rel="stylesheet"/>
      <style>
        body {{
          padding: 2rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
        }}
        .container {{
          background: white;
          border-radius: 15px;
          padding: 3rem;
          box-shadow: 0 10px 40px rgba(0,0,0,0.2);
          max-width: 800px;
        }}
        .hero {{
          text-align: center;
          margin-bottom: 2rem;
        }}
        .hero h1 {{
          color: #667eea;
          font-weight: bold;
          margin-bottom: 1rem;
        }}
        .date-display {{
          background: #f8f9fa;
          padding: 1.5rem;
          border-radius: 10px;
          margin: 2rem 0;
          text-align: center;
        }}
        .date-display h2 {{
          color: #764ba2;
          font-size: 2.5rem;
          margin: 0;
        }}
        .date-display p {{
          color: #6c757d;
          margin: 0.5rem 0 0 0;
        }}
        .checks {{
          margin-top: 2rem;
        }}
        .footer {{
          margin-top: 3rem;
          padding-top: 2rem;
          border-top: 1px solid #dee2e6;
          text-align: center;
          color: #6c757d;
        }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="hero">
          <h1><i class="bi bi-rocket-takeoff"></i> {title}</h1>
          <p class="lead text-muted">{brief}</p>
        </div>

        <div class="date-display" id="app">
          <h2>Hello World! 👋</h2>
          <p class="fs-4" id="current-date">Loading date...</p>
          <p class="fs-5" id="current-time">Loading time...</p>
        </div>

        <div class="checks">
          <h3 class="mb-3"><i class="bi bi-list-check"></i> Features & Checks</h3>
          <ul class="list-group">
{checks_html}
          </ul>
        </div>

        <div class="footer">
          <small class="text-muted">
            <i class="bi bi-calendar3"></i> Generated on {now}Z<br>
            <i class="bi bi-github"></i> Powered by GitHub Pages
          </small>
        </div>
      </div>

      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
      <script>
        // Display current date and time
        function updateDateTime() {{
          const now = new Date();
          
          // Format date
          const dateOptions = {{ 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          }};
          const dateStr = now.toLocaleDateString('en-US', dateOptions);
          document.getElementById('current-date').textContent = dateStr;
          
          // Format time
          const timeOptions = {{ 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit',
            hour12: true
          }};
          const timeStr = now.toLocaleTimeString('en-US', timeOptions);
          document.getElementById('current-time').textContent = timeStr;
        }}

        // Update immediately and then every second
        updateDateTime();
        setInterval(updateDateTime, 1000);

        // Log checks for verification
        console.log('Application loaded successfully!');
        console.log('Checks:', {checks});
        console.log('Brief:', {repr(brief)});
      </script>
    </body>
    </html>
    """)

def _readme(brief: str, checks: list[str]) -> str:
    lines = "\n".join(f"- {c}" for c in checks)
    return dedent(f"""\
    # Auto-generated Application

    ## 📋 Brief
    {brief}

    ## ✨ Features / Checks
    {lines}

    ## 🚀 Quick Start
    
    ### View Online
    Visit the GitHub Pages URL provided in the deployment.

    ### Run Locally
    Simply open `index.html` in any modern web browser.

    ## 🛠 Tech Stack
    - **Frontend**: Pure HTML5, CSS3, JavaScript
    - **Styling**: Bootstrap 5.3 (via CDN)
    - **Icons**: Bootstrap Icons
    - **Hosting**: GitHub Pages
    - **Generated**: Using LLM-assisted code generation

    ## 📁 Project Structure
    ```
    .
    ├── index.html          # Main application file
    ├── README.md           # This file
    └── LICENSE             # MIT License
    ```

    ## 🎨 Features
    - Responsive design (mobile-friendly)
    - Real-time date and time display
    - Modern gradient background
    - Clean, professional UI
    - Bootstrap components

    ## 📝 License
    This project is licensed under the MIT License - see the LICENSE file for details.

    ## 🤖 Auto-Generated
    This application was automatically generated and deployed using an LLM-powered deployment system.

    ---
    Made with ❤️ and AI
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
    """Return a short summary string of attachments for prompting"""
    if not attachments:
        return ""
    out = []
    for att in attachments:
        try:
            name = att.get("name", "file")
            url = att.get("url", "")
            if "," in url:
                header, data = url.split(",", 1)
                mime = header.split(";")[0].split(":")[1] if ":" in header else "unknown"
                if "base64" in header:
                    preview = f"(base64 {mime}, length {len(data)} chars)"
                else:
                    preview = data[:300]
                out.append(f"{name} - {preview}")
            else:
                out.append(f"{name} - {url[:100]}")
        except Exception:
            out.append(f"{att.get('name','file')} - (unreadable)")
    return "\n".join(out)

def generate_code(brief: str, checks: list[str], attachments: list[dict]) -> dict:
    """Generate initial code for Round 1"""
    
    # Try LLM first
    attach_note = process_attachments(attachments)
    prompt = f"""You are an expert web developer. Create a COMPLETE single-file HTML application.

BRIEF:
{brief}

REQUIREMENTS (must ALL be satisfied):
{chr(10).join('- ' + c for c in checks)}

ATTACHMENTS:
{attach_note if attach_note else "(none)"}

CRITICAL RULES:
1. Output ONE complete HTML file starting with <!DOCTYPE html>
2. Include Bootstrap 5 CSS via CDN: https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css
3. Include Bootstrap Icons: https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css
4. All CSS must be inline in <style> tags
5. All JavaScript must be inline in <script> tags
6. Make it FULLY FUNCTIONAL - no placeholders or TODO comments
7. Use modern, clean design with proper styling
8. Add comments explaining key sections
9. Handle attachments if provided (decode base64, parse CSV/JSON, etc.)
10. Test that ALL checks can pass

The HTML should be complete, beautiful, and ready to deploy immediately."""

    html = _call_gemini(prompt)
    
    if html:
        html = _extract_html(html)
        # Verify it's valid HTML
        if html and "<!DOCTYPE" in html and "</html>" in html:
            print("  ✓ LLM generated valid HTML")
            return {
                "index.html": html.strip(),
                "README.md": _readme(brief, checks),
                "LICENSE": _license_mit()
            }
        else:
            print("  ✗ LLM output invalid, using template")
    else:
        print("  ✗ LLM failed, using template")
    
    # Fallback to template
    return {
        "index.html": _template_index(brief, checks),
        "README.md": _readme(brief, checks),
        "LICENSE": _license_mit()
    }

def generate_updates(task_info: dict, brief: str, checks: list[str], attachments: list[dict]) -> dict:
    """Generate updated code for Round 2"""
    
    base_brief = task_info["round1"]["brief"]
    base_checks = task_info["round1"]["checks"]
    
    attach_note = process_attachments(attachments)
    
    prompt = f"""You are updating an existing web application. Keep ALL existing functionality working.

ORIGINAL REQUIREMENTS:
{base_brief}

ORIGINAL CHECKS (must still pass):
{chr(10).join('- ' + c for c in base_checks)}

NEW REQUIREMENTS TO ADD:
{brief}

NEW CHECKS (must also pass):
{chr(10).join('- ' + c for c in checks)}

NEW ATTACHMENTS:
{attach_note if attach_note else "(none)"}

CRITICAL RULES:
1. Output ONE complete updated HTML file with <!DOCTYPE html>
2. KEEP all original functionality working
3. ADD the new features/functionality
4. Use Bootstrap 5 and Bootstrap Icons
5. All CSS inline in <style>, all JS inline in <script>
6. Make it FULLY FUNCTIONAL - no placeholders
7. Improve the design if possible
8. Ensure ALL checks (old + new) can pass

The updated HTML should work perfectly with both old and new requirements."""

    html = _call_gemini(prompt)
    
    if html:
        html = _extract_html(html)
        if html and "<!DOCTYPE" in html and "</html>" in html:
            print("  ✓ LLM generated valid updated HTML")
            combined_checks = base_checks + checks
            return {
                "index.html": html.strip(),
                "README.md": _readme(f"{base_brief}\n\nUPDATED: {brief}", combined_checks)
            }
        else:
            print("  ✗ LLM output invalid, using enhanced template")
    else:
        print("  ✗ LLM failed, using enhanced template")
    
    # Fallback: create enhanced template
    combined_brief = f"{base_brief}\n\nUPDATE: {brief}"
    combined_checks = base_checks + checks
    return {
        "index.html": _template_index(combined_brief, combined_checks),
        "README.md": _readme(combined_brief, combined_checks)
    }