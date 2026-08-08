# -*- coding: utf-8 -*-

from flask import Flask, render_template_string, abort, send_from_directory
import markdown
import os

app = Flask(__name__)

WIKI_ROOT = os.path.dirname(os.path.abspath(__file__))

NAV_ITEMS = [
    ('home', 'Home'),
    ('description', 'Description'),
    ('design/hardware', 'Hardware'),
    ('design/modeling', 'Modeling'),
    ('design/software', 'Software'),
    ('implementation', 'Implementation'),
    ('pre_iGEM_training', 'Pre-iGEM Training'),
    ('results', 'Results'),
    ('contribution', 'Contribution'),
    ('team', 'Team'),
    ('attributions', 'Attributions'),
]

LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{{ title }} - BrewXOS iGEM 2026</title>
  <link rel="stylesheet" href="/static/css/wiki.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown.min.css">
</head>
<body>
  <header class="wiki-header">
    <h1>BrewXOS</h1>
    <p class="subtitle">iGEM 2026 - Shanghai Hongwen School Pudong</p>
  </header>
  <nav class="wiki-nav">
    {% for slug, label in nav %}
      <a href="/{{ slug }}" class="{% if slug == active %}active{% endif %}">{{ label }}</a>
    {% endfor %}
  </nav>
  <main class="markdown-body">
    {{ content | safe }}
  </main>
  <footer class="wiki-footer">
    <p>BrewXOS - iGEM 2026 - Built with Flask + Markdown - Last updated 2026-08</p>
  </footer>
</body>
</html>
"""


def render_page(slug):
    md_path = os.path.join(WIKI_ROOT, 'wiki', slug + '.md')
    if not os.path.exists(md_path):
        abort(404)
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    html_content = markdown.markdown(
        md_content,
        extensions=['fenced_code', 'tables', 'toc', 'attr_list', 'def_list']
    )
    title = slug.split('/')[-1].replace('_', ' ').title()
    return render_template_string(
        LAYOUT, content=html_content, title=title, nav=NAV_ITEMS, active=slug
    )


@app.route('/')
def home():
    return render_page('home')


@app.route('/<path:slug>')
def page(slug):
    return render_page(slug)


@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.join(WIKI_ROOT, 'static'), filename)


if __name__ == '__main__':
    print("BrewXOS Wiki running at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
