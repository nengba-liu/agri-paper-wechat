"""Extract source evidence; image objects are NOT automatically complete figures."""
import argparse, hashlib, json
from pathlib import Path


def extract(pdf, out, dpi=120):
    import fitz
    pdf, out = Path(pdf).resolve(), Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output must be empty; use a new version directory')
    out.mkdir(parents=True, exist_ok=True)
    (out/'pages').mkdir(); (out/'images').mkdir()
    report = {'source':str(pdf), 'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest(),
              'note':'Embedded objects may be partial figures. Inspect rendered pages and captions.', 'pages':[]}
    with fitz.open(pdf) as doc:
        if doc.needs_pass: raise ValueError('Encrypted PDF requires user-provided access')
        for i, page in enumerate(doc, 1):
            text = page.get_text(sort=True)
            (out/'pages'/f'{i:03}.txt').write_text(text, encoding='utf-8')
            page.get_pixmap(dpi=dpi, alpha=False).save(out/'pages'/f'{i:03}.png')
            item = {'page':i, 'text_chars':len(text.strip()), 'ocr_needed':len(text.strip())<60, 'images':[]}
            seen = set()
            for image in page.get_images(full=True):
                xref = image[0]
                if xref in seen: continue
                seen.add(xref)
                data = doc.extract_image(xref)
                name = f'p{i:03}_xref{xref}.{data["ext"]}'
                (out/'images'/name).write_bytes(data['image'])
                item['images'].append({'file':name,'width':data['width'],'height':data['height'],
                                       'rects':[list(r) for r in page.get_image_rects(xref)]})
            report['pages'].append(item)
    (out/'source-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pdf');p.add_argument('--out',required=True)
    p.add_argument('--dpi',type=int,default=120);a=p.parse_args()
    if not 72 <= a.dpi <= 600: p.error('dpi must be 72..600')
    r=extract(a.pdf,a.out,a.dpi)
    print(json.dumps({'pages':len(r['pages']),'ocr_pages':[x['page'] for x in r['pages'] if x['ocr_needed']]},ensure_ascii=False))
