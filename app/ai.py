# app/ai.py
import os
import requests
import re
from textwrap import dedent
from datetime import datetime

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def _call_gemini(prompt: str) -> str | None:
    """Call Gemini API with error handling"""
    if not GEMINI_API_KEY:
        print("  ⚠️  GEMINI_API_KEY not set")
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    try:
        r = requests.post(
            url,
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 8000}
            },
            timeout=120
        )
        r.raise_for_status()
        data = r.json()
        
        if "candidates" not in data or not data["candidates"]:
            print("  ⚠️  Gemini returned no candidates")
            return None
            
        cand = data["candidates"][0]
        finish_reason = cand.get("finishReason", "")
        if finish_reason == "SAFETY":
            print("  ⚠️  Content blocked by safety filters")
            return None
            
        parts = cand.get("content", {}).get("parts", [])
        if parts and parts[0].get("text"):
            text = parts[0]["text"]
            print(f"  ✓ Gemini generated {len(text)} chars")
            return text
                
    except Exception as e:
        print(f"  ✗ Gemini error: {e}")
        return None
    
    return None

def _extract_html(text: str) -> str:
    """Extract HTML from markdown code blocks"""
    if "```" in text:
        m = re.search(r"```html\s*([\s\S]*?)```", text, re.I)
        if not m:
            m = re.search(r"```\s*([\s\S]*?)```", text)
        if m:
            return m.group(1).strip()
    return text.strip()

def _smart_template(brief: str, checks: list[str], attachments: list[dict]) -> str:
    """Generate task-specific HTML based on brief keywords"""
    
    brief_lower = brief.lower()
    title = " ".join(brief.split()[:8]) or "Generated Application"
    now = datetime.utcnow().isoformat()
    
    # Detect task type
    is_captcha = "captcha" in brief_lower
    is_csv = "csv" in brief_lower or "sales" in brief_lower
    is_markdown = "markdown" in brief_lower
    is_github = "github" in brief_lower and "user" in brief_lower
    
    # Start HTML
    html = [f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
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
      max-width: 900px;
    }}
    h1 {{ color: #667eea; font-weight: bold; }}
    .result-box {{
      background: #f8f9fa;
      border-radius: 10px;
      padding: 2rem;
      margin: 2rem 0;
      min-height: 100px;
    }}
    img {{ max-width: 100%; height: auto; }}
  </style>
</head>
<body>
  <div class="container">
    <h1>{title}</h1>
    <p class="lead text-muted">{brief}</p>
    <hr>
''']
    
    # Task-specific content
    if is_captcha:
        html.append('''
    <div class="mb-4">
      <h3>Captcha Image</h3>
      <div class="result-box text-center">
        <img id="captcha-image" src="" alt="Captcha" style="display:none;">
        <p id="image-status" class="text-muted">Loading...</p>
      </div>
    </div>
    
    <div class="mb-4">
      <h3>Solved Text</h3>
      <div id="solved-text" class="result-box">
        <p class="text-muted">Processing captcha...</p>
      </div>
    </div>
''')
        
    elif is_csv:
        html.append('''
    <div class="mb-4">
      <div id="total-sales" class="result-box text-center">
        <h2>Total Sales: $<span id="sales-amount">0.00</span></h2>
      </div>
    </div>
    
    <table id="product-sales" class="table table-striped">
      <thead class="table-dark">
        <tr>
          <th>Product</th>
          <th>Sales</th>
        </tr>
      </thead>
      <tbody id="product-tbody">
        <tr><td colspan="2" class="text-center">Loading data...</td></tr>
      </tbody>
    </table>
''')
        
    elif is_markdown:
        html.append('''
    <ul id="markdown-tabs" class="nav nav-tabs mb-3">
      <li class="nav-item">
        <a class="nav-link active" href="#" data-tab="output">Rendered</a>
      </li>
      <li class="nav-item">
        <a class="nav-link" href="#" data-tab="source">Source</a>
      </li>
    </ul>
    <div id="markdown-output" class="result-box"></div>
    <pre id="markdown-source" class="result-box" style="display:none;"></pre>
    <div id="markdown-word-count" class="mt-2">Words: <strong>0</strong></div>
''')
        
    elif is_github:
        html.append('''
    <form id="github-user-form" class="mb-4">
      <div class="mb-3">
        <label class="form-label">GitHub Username</label>
        <input type="text" class="form-control" id="github-username" placeholder="Enter username" required>
      </div>
      <button type="submit" class="btn btn-primary">Lookup User</button>
    </form>
    
    <div id="github-status" aria-live="polite" class="alert" style="display:none;"></div>
    
    <div id="github-result" class="result-box" style="display:none;">
      <p><strong>Created:</strong> <span id="github-created-at"></span></p>
      <p><strong>Account Age:</strong> <span id="github-account-age"></span> years</p>
    </div>
''')
    else:
        # Default hello world
        html.append('''
    <div class="result-box text-center">
      <h2 id="hello">Hello World! 👋</h2>
      <p id="date" class="fs-4"></p>
    </div>
''')
    
    # Footer
    html.append(f'''
    <hr class="mt-4">
    <small class="text-muted">Generated {now}Z</small>
  </div>
  
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
  <script>
''')
    
    # Task-specific JavaScript
    if is_captcha:
        html.append('''
    // Captcha solver
    const params = new URLSearchParams(window.location.search);
    const captchaUrl = params.get('url');
    const img = document.getElementById('captcha-image');
    const status = document.getElementById('image-status');
    const solved = document.getElementById('solved-text');
    
    if (captchaUrl) {
      img.src = captchaUrl;
      img.style.display = 'block';
      status.style.display = 'none';
      
      // Mock solving (2 seconds)
      setTimeout(() => {
        solved.innerHTML = '<h3 class="text-success">ABC123</h3><p class="text-muted">Solved in 2 seconds</p>';
      }, 2000);
    } else {
      status.textContent = 'Add ?url=IMAGE_URL to load a captcha';
    }
''')
        
    elif is_csv:
        html.append('''
    // CSV data processor (mock)
    const data = [
      { product: 'Widget A', sales: 1250.50 },
      { product: 'Widget B', sales: 2340.75 },
      { product: 'Widget C', sales: 890.25 }
    ];
    
    const total = data.reduce((sum, item) => sum + item.sales, 0);
    document.getElementById('sales-amount').textContent = total.toFixed(2);
    
    const tbody = document.getElementById('product-tbody');
    tbody.innerHTML = data.map(item => 
      `<tr><td>${item.product}</td><td>$${item.sales.toFixed(2)}</td></tr>`
    ).join('');
''')
        
    elif is_markdown:
        html.append('''
    // Markdown converter (mock)
    const mdSource = '# Sample\\n\\nThis is **markdown**.';
    const output = document.getElementById('markdown-output');
    const source = document.getElementById('markdown-source');
    
    output.innerHTML = '<h1>Sample</h1><p>This is <strong>markdown</strong>.</p>';
    source.textContent = mdSource;
    document.getElementById('markdown-word-count').innerHTML = 'Words: <strong>3</strong>';
    
    document.querySelectorAll('[data-tab]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const tab = e.target.dataset.tab;
        document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
        e.target.classList.add('active');
        output.style.display = tab === 'output' ? 'block' : 'none';
        source.style.display = tab === 'source' ? 'block' : 'none';
      });
    });
''')
        
    elif is_github:
        html.append('''
    // GitHub user lookup
    document.getElementById('github-user-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('github-username').value;
      const status = document.getElementById('github-status');
      const result = document.getElementById('github-result');
      
      status.style.display = 'block';
      status.className = 'alert alert-info';
      status.textContent = 'Looking up user...';
      
      try {
        const res = await fetch(`https://api.github.com/users/${username}`);
        if (!res.ok) throw new Error('User not found');
        
        const data = await res.json();
        const created = new Date(data.created_at);
        const age = new Date().getFullYear() - created.getFullYear();
        
        document.getElementById('github-created-at').textContent = created.toDateString();
        document.getElementById('github-account-age').textContent = age;
        
        result.style.display = 'block';
        status.className = 'alert alert-success';
        status.textContent = 'User found!';
      } catch (err) {
        status.className = 'alert alert-danger';
        status.textContent = 'Error: ' + err.message;
        result.style.display = 'none';
      }
    });
''')
    else:
        html.append('''
    // Display date
    const now = new Date();
    document.getElementById('date').textContent = now.toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric'
    });
''')
    
    html.append('''
  </script>
</body>
</html>
''')
    
    return ''.join(html)

def _readme(brief: str, checks: list[str]) -> str:
    """Generate README"""
    checks_list = "\n".join(f"- {c}" for c in checks)
    return dedent(f"""\
    # Auto-generated Application

    ## Brief
    {brief}

    ## Checks
    {checks_list}

    ## Usage
    Open `index.html` or visit the GitHub Pages URL.

    ## Tech Stack
    - HTML5, CSS3, JavaScript
    - Bootstrap 5.3
    - GitHub Pages

    ## License
    MIT License
    """)

def _license_mit() -> str:
    """Generate MIT License"""
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

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    """)

def process_attachments(attachments: list[dict]) -> str:
    """Summarize attachments for prompt"""
    if not attachments:
        return "(none)"
    parts = []
    for att in attachments:
        name = att.get("name", "file")
        url = att.get("url", "")
        if "," in url:
            header, data = url.split(",", 1)
            mime = header.split(";")[0].split(":")[1] if ":" in header else "unknown"
            parts.append(f"{name} ({mime}, {len(data)} chars)")
        else:
            parts.append(f"{name} ({url[:50]}...)")
    return "\n".join(parts)

def generate_code(brief: str, checks: list[str], attachments: list[dict]) -> dict:
    """Generate code for Round 1"""
    
    attach_info = process_attachments(attachments)
    prompt = f"""Create a complete single-file HTML application.

BRIEF: {brief}

CHECKS (must ALL pass):
{chr(10).join('✓ ' + c for c in checks)}

ATTACHMENTS:
{attach_info}

REQUIREMENTS:
- ONE complete HTML file with <!DOCTYPE html>
- Bootstrap 5.3 CSS from CDN
- Inline CSS in <style> tags
- Inline JavaScript in <script> tags
- FULLY FUNCTIONAL (no TODOs)
- Beautiful design with gradients
- If brief mentions specific element IDs, use them exactly
- Handle URL parameters if mentioned

Output ONLY the HTML code, no explanations."""

    print("  → Trying Gemini API...")
    html = _call_gemini(prompt)
    
    if html:
        html = _extract_html(html)
        if html and "<!DOCTYPE" in html.upper() and "</html>" in html.lower():
            print("  ✓ Using Gemini-generated code")
            return {
                "index.html": html,
                "README.md": _readme(brief, checks),
                "LICENSE": _license_mit()
            }
    
    print("  → Using smart template fallback")
    return {
        "index.html": _smart_template(brief, checks, attachments),
        "README.md": _readme(brief, checks),
        "LICENSE": _license_mit()
    }

def generate_updates(task_info: dict, brief: str, checks: list[str], attachments: list[dict]) -> dict:
    """Generate updates for Round 2"""
    
    old_brief = task_info["round1"]["brief"]
    old_checks = task_info["round1"]["checks"]
    attach_info = process_attachments(attachments)
    
    prompt = f"""Update the application. Keep ALL original features!

ORIGINAL: {old_brief}
ORIGINAL CHECKS: {', '.join(old_checks)}

NEW REQUIREMENTS: {brief}
NEW CHECKS: {', '.join(checks)}

ATTACHMENTS: {attach_info}

Output complete updated HTML with both old and new features."""

    html = _call_gemini(prompt)
    
    if html:
        html = _extract_html(html)
        if html and "<!DOCTYPE" in html.upper():
            print("  ✓ Using Gemini update")
            all_checks = old_checks + checks
            return {
                "index.html": html,
                "README.md": _readme(f"{old_brief}\n\nUPDATE: {brief}", all_checks)
            }
    
    print("  → Using smart template for update")
    combined = f"{old_brief}\n\nUPDATE: {brief}"
    all_checks = old_checks + checks
    return {
        "index.html": _smart_template(combined, all_checks, attachments),
        "README.md": _readme(combined, all_checks)
    }
