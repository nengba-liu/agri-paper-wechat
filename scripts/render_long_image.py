"""Offline long-image export. Uses MuPDF's HTML layout (not browser-exact CSS)."""
import argparse
import base64
import json
import math
import re
import tempfile
from html.parser import HTMLParser
from pathlib import Path

import fitz


class ArticleHTML(HTMLParser):
    """Keep the article only, embed images locally, and discard active content."""
    def __init__(self, root):
        super().__init__(convert_charrefs=False)
        self.root = root
        self.output = []
        self.depth = 0
        self.images = 0
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'main' and attrs.get('id') == 'article':
            self.depth = 1
            return
        if not self.depth:
            return
        if tag in ('script', 'style', 'iframe'):
            self.skip += 1
            return
        if self.skip:
            return
        if tag == 'img':
            src = attrs.get('src', '')
            if not re.match(r'^data:image/(png|jpeg|jpg|webp);base64,', src):
                raise ValueError('Long-image export requires embedded raster images')
            raw = base64.b64decode(src.split(',', 1)[1], validate=True)
            pix = fitz.Pixmap(raw)  # Validate image bytes before layout.
            if pix.width * pix.height > 100_000_000:
                raise ValueError('Input image exceeds pixel budget')
            name = f'image-{self.images:03d}.png'
            pix.save(str(self.root / name))
            self.images += 1
            self.output.append(f'<img src="{name}" style="width:100%"/>')
            return
        tag = 'div' if tag in ('section', 'main', 'figure') else tag
        if tag not in ('div', 'p', 'span', 'strong', 'b', 'em', 'i', 'a', 'br', 'h1', 'h2', 'h3', 'ul', 'ol', 'li'):
            return
        from html import escape
        style = attrs.get('style', '')
        # MuPDF uses a smaller CSS subset; use a portable Chinese font stack.
        style = re.sub(r'font-family:[^;]+;?', '', style)
        self.output.append(f'<{tag} style="{escape(style, quote=True)}">')

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if not self.depth:
            return
        if tag in ('script', 'style', 'iframe'):
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag == 'main':
            self.depth = 0
            return
        tag = 'div' if tag in ('section', 'figure') else tag
        if tag in ('div', 'p', 'span', 'strong', 'b', 'em', 'i', 'a', 'h1', 'h2', 'h3', 'ul', 'ol', 'li'):
            self.output.append(f'</{tag}>')

    def handle_data(self, data):
        if self.depth and not self.skip:
            from html import escape
            self.output.append(escape(data))

    def handle_entityref(self, name):
        if self.depth and not self.skip:
            self.output.append('&' + name + ';')

    def handle_charref(self, name):
        if self.depth and not self.skip:
            self.output.append('&#' + name + ';')


def render(input_file, out, width=430, scale=2, segment_height=2400, max_pixels=120_000_000):
    if not 320 <= width <= 1600 or not 1 <= scale <= 3 or not 300 <= segment_height <= 6000:
        raise ValueError('Unsupported image dimensions')
    out = Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output must be empty')
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.agri-long-', dir=out.parent) as tmp:
        parser = ArticleHTML(Path(tmp))
        parser.feed(Path(input_file).read_text(encoding='utf-8-sig'))
        if not parser.output:
            raise ValueError('Missing main#article; use the generated single-file preview')
        css = 'body {margin:0;font-family:sans-serif;} p {orphans:1;widows:1;} img {width:100%;} a {color:#196b54;}'
        story = fitz.Story(''.join(parser.output), user_css=css, archive=fitz.Archive(tmp))
        more, filled = story.place(fitz.Rect(0, 0, width, 300000))
        if more:
            raise ValueError('Article exceeds maximum layout height')
        height = math.ceil(filled[3]) + 2
        pdf = Path(tmp) / 'layout.pdf'
        writer = fitz.DocumentWriter(str(pdf))
        device = writer.begin_page(fitz.Rect(0, 0, width, height))
        story.draw(device)
        writer.end_page()
        writer.close()
        del device, writer
        out.mkdir(parents=True, exist_ok=True)
        with fitz.open(pdf) as doc:
            page = doc[0]
            report = {'backend':'pymupdf', 'width':width * scale, 'height':height * scale,
                      'images':parser.images, 'full_image':None, 'segments':[],
                      'layout_note':'Offline reflow; some CSS differs from the browser HTML.',
                      'platform_verified':False}
            if width * height * scale ** 2 <= max_pixels and height * scale <= 60000:
                page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False).save(str(out/'article-long.png'))
                report['full_image'] = 'article-long.png'
            for i, y in enumerate(range(0, height, segment_height), 1):
                bottom = min(y + segment_height, height)
                name = f'article-part-{i:02d}.png'
                page.get_pixmap(matrix=fitz.Matrix(scale, scale), clip=fitz.Rect(0, y, width, bottom), alpha=False).save(str(out/name))
                report['segments'].append({'file':name, 'top':y*scale, 'bottom':bottom*scale})
        (out/'render-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--width', type=int, default=430)
    p.add_argument('--scale', type=int, default=2)
    p.add_argument('--segment-height', type=int, default=2400)
    args = p.parse_args()
    print(json.dumps(render(args.input, args.out, args.width, args.scale, args.segment_height), ensure_ascii=False, indent=2))
