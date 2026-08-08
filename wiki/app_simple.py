# -*- coding: utf-8 -*-
"""BrewXOS Wiki - Super simple debug version"""
from flask import Flask, send_file, abort
import os

app = Flask(__name__)
WIKI_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route('/')
def home():
    return send_file(os.path.join(WIKI_DIR, 'home.md'), mimetype='text/markdown')


@app.route('/<page>')
def page(page):
    # Remove .md if user typed it
    if page.endswith('.md'):
        page = page[:-3]
    md_path = os.path.join(WIKI_DIR, page + '.md')
    if not os.path.exists(md_path):
        return f"404 - File not found: {md_path}<br><br>Try: /, /description, /team, /attributions, /design/hardware", 404
    return send_file(md_path, mimetype='text/markdown')


if __name__ == '__main__':
    print("=" * 60)
    print("BrewXOS Wiki (debug version) at http://localhost:5000")
    print("=" * 60)
    print("Available pages:")
    for f in os.listdir(WIKI_DIR):
        if f.endswith('.md'):
            print(f"  /{f[:-3]}")
    for root, dirs, files in os.walk(WIKI_DIR):
        for f in files:
            if f.endswith('.md'):
                rel = os.path.relpath(os.path.join(root, f), WIKI_DIR)[:-3]
                print(f"  /{rel.replace(os.sep, '/')}")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
