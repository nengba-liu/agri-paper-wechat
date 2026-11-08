"""Hui Geng Yun layouts calibrated against user references, 2026-11-08."""
import html
import re
from pathlib import Path

GREEN = '#1F9275'
MINT = '#53BAA4'

def leaf(value):
    return '<span leaf="">' + html.escape(str(value)) + '</span>'

def rich(value):
    parts = re.split(r'(\*\*.*?\*\*|==.*?==)', str(value))
    result = []
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            result.append('<strong style="font-weight:700;">' + leaf(part[2:-2]) + '</strong>')
        elif part.startswith('==') and part.endswith('=='):
            result.append('<span style="text-decoration:underline;text-decoration-style:dashed;text-decoration-color:' + GREEN + ';text-underline-offset:4px;">' + leaf(part[2:-2]) + '</span>')
        else:
            result.append(leaf(part))
    return ''.join(result)

def box(style, content):
    return '<section style="' + style + '">' + content + '</section>'

def p(value, style='', indent=False):
    return '<p style="margin:0 0 12px;line-height:1.8;word-break:normal;overflow-wrap:anywhere;' + ('text-indent:2em;' if indent else '') + style + '">' + rich(value) + '</p>'

def heading(title, n=None, research=False):
    if research:
        # Native inline elements preserve editable text; no copied template/SVG.
        return box('margin:38px 0 20px;border-bottom:1px solid ' + MINT + ';padding:0 0 6px;',
                   '<p style="margin:0;font-size:19px;line-height:1.65;font-weight:700;color:#3E3E3E;">'
                   '<span style="display:inline-block;background:#DDF2EB;padding:9px 13px 4px;">' + leaf(title) + '</span>'
                   '<span style="display:inline-block;margin-left:12px;font-size:16px;letter-spacing:1px;color:' + MINT + ';">' + leaf('//////') + '</span></p>')
    number = '<span style="display:inline-block;vertical-align:middle;min-width:32px;height:32px;line-height:32px;text-align:center;border:3px solid ' + GREEN + ';border-radius:50%;margin-right:10px;font-size:16px;">' + leaf(f'{n:02d}') + '</span>'
    return box('margin:34px 0 20px;', '<p style="margin:0;color:' + GREEN + ';font-size:18px;font-weight:700;line-height:1.8;">' + number + rich(title) + '</p>')

def render(d, sources):
    research = d['audience'] == 'researchers'
    layout = d.get('layout', {})
    captions, used = [], []
    md = ['# ' + d['title'], '', d.get('deck', '')]
    out = []

    def figure(ident, cover=False):
        a = next(x for x in d['assets'] if x['id'] == ident)
        used.append(ident)
        alt = a.get('alt') or a['caption']
        image = '<img src="' + html.escape(sources[ident], quote=True) + '" alt="' + html.escape(alt, quote=True) + '" style="display:block;width:100%;height:auto;max-width:100%;"/>'
        md.extend(['', f'![{alt}](images/{ident}{Path(a["path"]).suffix.lower()})', a['caption']])
        if not cover:
            captions.append(a['caption'])
            if a.get('caption_title'):
                image += p(a['caption_title'], 'font-size:14px;color:#656565;text-align:center;margin:10px 0 4px;')
            image += p(a['caption'], 'font-size:13px;line-height:1.75;color:#777777;text-align:justify;margin:9px 0 0;')
        return box('margin:22px 0;', image)

    if layout.get('show_title', True):
        out.append(p(d['title'], 'font-size:25px;line-height:1.5;font-weight:700;color:#264A3E;margin-bottom:15px;'))
    if d.get('deck'):
        out.append(p(d['deck'], 'font-size:13px;color:#777777;margin-bottom:24px;'))
    if layout.get('show_cover', False):
        out.append(figure(d['cover'], True))
    if d.get('paper_preview'):
        out.append(figure(d['paper_preview']))
    if research and d.get('paper_info'):
        out.append(heading('文章信息', research=True))
        for item in d['paper_info']:
            out.append(p('**' + item['label'] + '：**' + item['value'], 'margin-bottom:3px;'))
            md.extend(['', item['label'] + '：' + item['value']])
    lead = ''.join(p(s, indent=True) for s in d['lead'])
    md.extend([''] + d['lead'])
    if research:
        out.append(lead)
    else:
        out.append(box('padding:18px 16px 8px;background:#F5F8E9;border-radius:10px;margin:20px 0;',
                       p(d.get('series', '硬核科普'), 'color:#527F38;font-size:14px;font-weight:700;margin-bottom:10px;') + lead))
    if layout.get('show_takeaways', False):
        out.append(box('border-left:3px solid ' + GREEN + ';padding:8px 16px;margin:20px 0;', ''.join(p(s) for s in d['takeaways'])))
        md.extend(['', '## 导读'] + ['- ' + s for s in d['takeaways']])
    if layout.get('overview_position', 'intro') == 'intro':
        out.append(figure(d['overview']))
    for n, sec in enumerate(d['sections'], 1):
        out.append(heading(sec['title'], n, research))
        md.extend(['', '## ' + sec['title']])
        rendered = []
        for b in sec['blocks']:
            kind = b['type']
            if kind == 'p':
                rendered.append(p(b['text'], indent=b.get('indent', True)))
                md.extend(['', b['text']])
            elif kind == 'image':
                rendered.append(figure(b['asset']))
            elif kind == 'list':
                for i, s in enumerate(b['items'], 1):
                    rendered.append(p(f'{i}. {s}'))
                    md.extend(['', f'{i}. {s}'])
            elif kind == 'callout':
                rendered.append(box('background:#F5F8EF;border-left:3px solid ' + GREEN + ';padding:15px 16px 3px;margin:22px 0;', p('**' + b.get('label', '读图提示') + '**', 'color:' + GREEN + ';') + p(b['text'])))
                md.extend(['', '> ' + b.get('label', '读图提示') + '：' + b['text']])
            elif kind == 'stats':
                for item in b['items']:
                    rendered.append(box('border-bottom:1px solid #DDEAE3;padding:12px 0;', p(item['value'], 'font-size:26px;font-weight:700;color:' + GREEN + ';margin-bottom:3px;') + p(item['label'], 'font-size:14px;margin:0;')))
                    md.extend(['', item['value'] + '｜' + item['label']])
        content = ''.join(rendered)
        if sec.get('role') == 'knowledge' or sec['title'] == '知识卡片':
            content = box('border:4px double #353535;padding:17px 14px 4px;', content)
        out.append(content)
    if d.get('closing'):
        out.append(box('margin:30px 0;padding:20px 16px 8px;background:#F5F8E9;', p(d['closing'], indent=True)))
        md.extend(['', d['closing']])
    if research:
        highlights = p('文章亮点', 'font-size:22px;color:#338AC7;text-align:center;font-weight:700;')
        highlights += ''.join(p(f'{i}. {s}') for i, s in enumerate(d['takeaways'], 1))
        out.append(box('margin:30px 0;border:1px solid #338AC7;padding:18px 14px 5px;', highlights))
        md.extend(['', '## 文章亮点'] + ['- ' + s for s in d['takeaways']])
    ref = ''
    md.extend(['', '## 论文与图源'])
    for r in d['references']:
        label = rich(r['text'])
        if r.get('url'):
            label = '<a href="' + html.escape(r['url'], quote=True) + '" style="color:#467C6A;text-decoration:underline;">' + label + '</a>'
        ref += '<p style="font-size:12px;line-height:1.8;overflow-wrap:anywhere;margin:12px 0;">' + label + '</p>'
        md.append(r['text'] + ' ' + r.get('url', ''))
    out.append(box('margin-top:28px;padding-top:16px;border-top:1px solid #DCE5DF;', ref))
    out.append(p('——  END  ——', 'text-align:center;color:#417348;font-weight:700;letter-spacing:2px;margin:28px 0;'))
    if d.get('brand_footer'):
        out.append(figure(d['brand_footer'], True))
    if d.get('disclosure'):
        out.append(p(d['disclosure'], 'font-size:12px;color:#888888;'))
        md.extend(['', d['disclosure']])
    for credit in d.get('credits', []):
        out.append(p(credit['role'] + ' | ' + credit['name'], 'font-size:12px;color:#888888;text-align:center;margin:5px 0;'))
        md.extend(['', credit['role'] + ' | ' + credit['name']])
    body = box('max-width:640px;margin:0 auto;padding:24px 20px;background:#FFFFFF;font-family:system-ui,-apple-system,BlinkMacSystemFont,Microsoft YaHei,sans-serif;font-size:16px;letter-spacing:0.5px;color:#3E3E3E;text-align:justify;word-wrap:break-word;box-sizing:border-box;', ''.join(out))
    return body, '\n'.join(md), '\n\n'.join(captions), used
