#!/usr/bin/env python3
import os
import re
import shutil
import subprocess
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_DIR = os.path.join(ROOT, 'posts', 'html')
MD_DIR = os.path.join(ROOT, 'posts', 'md')
INDEX_PATH = os.path.join(ROOT, 'posts', 'index.html')

def collect_posts():
    if not os.path.isdir(HTML_DIR):
        return []
    items = []
    for name in sorted(os.listdir(HTML_DIR)):
        if name.lower().endswith('.html'):
            items.append(name)
    return items

def ensure_dirs():
    os.makedirs(HTML_DIR, exist_ok=True)

def md_to_html_body(md: str) -> str:
    out = []
    in_code = False
    in_list = False
    para = []

    def flush_para():
        if para:
            text = ' '.join(para).strip()
            text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
            out.append(f"<p>{text}</p>")
            para.clear()

    def flush_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in md.splitlines():
        line = raw.rstrip('\n')
        if line.strip().startswith('```'):
            flush_para()
            flush_list()
            if not in_code:
                out.append('<pre><code>')
                in_code = True
            else:
                out.append('</code></pre>')
                in_code = False
            continue
        if in_code:
            out.append(re.sub(r'&', '&amp;', re.sub(r'<', '&lt;', line)))
            continue

        m = re.match(r'^(#{1,6})\s+(.*)$', line)
        if m:
            flush_para()
            flush_list()
            level = len(m.group(1))
            text = m.group(2).strip()
            out.append(f"<h{level}>{text}</h{level}>")
            continue

        if re.match(r'^\s*[-*]\s+.+', line):
            if not in_list:
                flush_para()
                out.append('<ul>')
                in_list = True
            item = re.sub(r'^\s*[-*]\s+', '', line)
            item = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', item)
            out.append(f"  <li>{item}</li>")
            continue
        else:
            if in_list and line.strip() == '':
                flush_list()

        if line.strip() == '':
            flush_para()
        else:
            para.append(line)

    flush_para()
    flush_list()
    if in_code:
        out.append('</code></pre>')
    return "\n".join(out)

def md_to_html_with_pandoc(md_path: str) -> str:
    """Use pandoc to convert markdown to an HTML fragment (no full page)."""
    pandoc = shutil.which('pandoc')
    if not pandoc:
        return None
    try:
        res = subprocess.run(
            [pandoc, '-f', 'markdown', '-t', 'html5', md_path],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8'
        )
        return res.stdout
    except Exception:
        return None

def compile_md_posts():
    if not os.path.isdir(MD_DIR):
        return []
    written = []
    for name in sorted(os.listdir(MD_DIR)):
        if not name.lower().endswith('.md'):
            continue
        base = os.path.splitext(name)[0]
        src = os.path.join(MD_DIR, name)
        dst = os.path.join(HTML_DIR, base + '.html')
        with open(src, 'r', encoding='utf-8') as f:
            md_text = f.read()
        # Prefer pandoc if available for better Markdown fidelity
        frag = md_to_html_with_pandoc(src)
        if frag is None:
            frag = md_to_html_body(md_text)
        body = frag
        html = f"""<!doctype html>
<html>
<head>
<meta charset='UTF-8'><meta name='viewport' content='width=device-width initial-scale=1'>
<meta http-equiv=\"content-language\" content=\"en\">
<title>{base}</title>
<link href='https://fonts.loli.net/css?family=Open+Sans:400italic,700italic,700,400&subset=latin,latin-ext' rel='stylesheet' type='text/css' />
<link rel=\"stylesheet\" href=\"../../assets/styles.css\">
</head>
<body class='typora-export'>
<div id='write' class='is-mac'>
  <nav class=\"nav-bar\">
    <a href=\"../../index.html\" class=\"nav-link\">Profile</a>
    <a href=\"../index.html\" class=\"nav-link\">Posts</a>
  </nav>

{body}

</div>
</body>
</html>\n"""
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(html)
        written.append(dst)
    return written

def render(posts):
    last_update = datetime.now().strftime('%b %Y')
    li = "\n".join(
        f"    <li><a href=\"./html/{name}\">{name}</a></li>" for name in posts
    ) or "    <!-- No posts found in posts/html -->"
    return f"""<!doctype html>
<html>
<head>
<meta charset='UTF-8'><meta name='viewport' content='width=device-width initial-scale=1'>
<meta http-equiv=\"content-language\" content=\"en\">
<title>Posts</title>
<link href='https://fonts.loli.net/css?family=Open+Sans:400italic,700italic,700,400&subset=latin,latin-ext' rel='stylesheet' type='text/css' />
<link rel=\"stylesheet\" href=\"../assets/styles.css\">
</head>
<body class='typora-export'>
<div id='write' class='is-mac'>
  <nav class=\"nav-bar\">
    <a href=\"../index.html\" class=\"nav-link\">Profile</a>
    <a href=\"./index.html\" class=\"nav-link\">Posts</a>
  </nav>

  <h3>Posts</h3>
  <ul>
{li}
  </ul>

  <footer>Last update: {last_update}</footer>
</div>
</body>
</html>\n"""

def main():
    ensure_dirs()
    compiled = compile_md_posts()
    posts = collect_posts()
    html = render(posts)
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Compiled {len(compiled)} markdown file(s). Wrote {INDEX_PATH} with {len(posts)} entr(ies)")

if __name__ == '__main__':
    main()
