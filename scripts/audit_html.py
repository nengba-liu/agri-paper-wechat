"""Static audit of the import fragment, not a platform compatibility certification."""
import argparse, json, re
from html.parser import HTMLParser
from pathlib import Path


class Audit(HTMLParser):
    def __init__(self):
        super().__init__(); self.errors=[]; self.warnings=[]; self.stack=[]; self.images=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag not in {'section','p','span','strong','em','img','a','br'}: self.errors.append('Unsupported tag: '+tag)
        for key in a:
            if key.startswith('on') or key in {'class','id'}: self.errors.append('Unsupported attribute: '+key)
        style=a.get('style','') or ''
        if re.search(r'position\s*:|float\s*:|display\s*:\s*grid|var\(|url\(|@media|@import',style,re.I):
            self.errors.append('Unsupported CSS: '+style)
        if tag=='a' and not (a.get('href') or '').startswith('https://'): self.errors.append('Link must use HTTPS')
        if tag=='img':
            self.images+=1
            src=a.get('src') or ''
            if src.startswith('data:image/'):
                self.warnings.append('Embedded image needs Xiumi import verification')
            elif not src.startswith('https://'): self.errors.append('Image not portable')
            if not a.get('alt'): self.errors.append('Image missing alt')
        if tag not in {'img','br'}: self.stack.append((tag,a))
    def handle_endtag(self,tag):
        if tag in {'img','br'}:return
        if not self.stack or self.stack[-1][0]!=tag: self.errors.append('Unbalanced tag: '+tag)
        else: self.stack.pop()
    def handle_data(self,data):
        if data.strip() and not any(t=='span' and 'leaf' in a for t,a in self.stack):
            self.errors.append('Text outside leaf span')


def audit(html):
    p=Audit();p.feed(html);p.close()
    if p.stack:p.errors.append('Unclosed tags')
    return {'errors':sorted(set(p.errors)),'warnings':sorted(set(p.warnings)),
            'images':p.images,'static_pass':not p.errors,'platform_verified':False}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('html');p.add_argument('--report');a=p.parse_args()
    r=audit(Path(a.html).read_text(encoding='utf-8'));s=json.dumps(r,ensure_ascii=False,indent=2)
    print(s)
    if a.report:Path(a.report).write_text(s,encoding='utf-8')
    raise SystemExit(bool(r['errors']))
