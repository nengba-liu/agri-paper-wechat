"""Build portable preview, inline import HTML and asset package from reviewed content."""
import argparse, base64, html, json, mimetypes, re, shutil, zipfile
from pathlib import Path
from urllib.parse import urlparse
from audit_html import audit

THEMES={
 'hgy':{'accent':'#146B55','pale':'#EEF5EF','ink':'#203D32','gold':'#B38A3C','radius':'12px'},
 'non-hgy':{'accent':'#5E6549','pale':'#F4F3EE','ink':'#252622','gold':'#8C7960','radius':'2px'}
}


def safe_file(root,relative):
    p=(root/relative).resolve()
    if not p.is_relative_to(root.resolve()): raise ValueError('Asset escapes job directory: '+relative)
    if not p.is_file(): raise FileNotFoundError(p)
    return p


def text(s):
    # Only the documented emphasis notation is accepted; input HTML remains literal.
    parts=re.split(r'(\*\*.*?\*\*|==.*?==)',str(s))
    return ''.join('<strong style="font-weight:700;">'+leaf(p[2:-2])+'</strong>' if p.startswith('**') and p.endswith('**') else '<span style="text-decoration:underline;text-decoration-style:dashed;">'+leaf(p[2:-2])+'</span>' if p.startswith('==') and p.endswith('==') else leaf(p) for p in parts if p)


def leaf(s):return '<span leaf="">'+html.escape(str(s))+'</span>'
def section(s,body):return '<section style="'+s+'">'+body+'</section>'
def para(s,style=''):return '<p style="margin:0 0 18px;line-height:1.9;'+style+'">'+text(s)+'</p>'


def validate(d,root,mapping):
    if d.get('audience') not in ('farmers','researchers'):raise ValueError('Invalid audience')
    for k in ('title','lead','takeaways','sections','references','assets','cover','overview'):
        if not d.get(k):raise ValueError('Missing '+k)
    assets={}
    for a in d['assets']:
        ident=a['id']
        if not re.fullmatch(r'[A-Za-z0-9_-]+',ident):raise ValueError('Unsafe asset id')
        if ident in assets:raise ValueError('Duplicate asset id')
        p=safe_file(root,a['path'])
        if p.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):raise ValueError('Use PNG/JPEG/WebP assets')
        if not a.get('caption'):raise ValueError('Missing caption')
        assets[ident]=(a,p)
    for k in ('cover','overview'):
        if d[k] not in assets:raise ValueError('Missing '+k+' asset')
    if d['cover']==d['overview']:raise ValueError('Cover and overview must be separate assets')
    for k in ('paper_preview','brand_footer'):
        if d.get(k) and d[k] not in assets:raise ValueError('Unknown '+k+' asset')
    layout=d.get('layout',{})
    if layout.get('overview_position','intro') not in ('intro','manual'):raise ValueError('Invalid overview position')
    if layout.get('overview_position')=='manual' and not any(b.get('type')=='image' and b.get('asset')==d['overview'] for s in d['sections'] for b in s.get('blocks',[])):raise ValueError('Manual overview must appear in sections')
    for sec in d['sections']:
        if not sec.get('title') or not sec.get('blocks'):raise ValueError('Empty section')
        for b in sec['blocks']:
            if b.get('type') not in ('p','image','callout','stats','list'):raise ValueError('Unknown block')
            if b['type']=='image' and b['asset'] not in assets:raise ValueError('Unknown image')
    for k,v in mapping.items():
        if k not in assets:raise ValueError('Unknown mapped asset')
        u=urlparse(v)
        if u.scheme!='https' or not u.hostname or u.username or u.password:raise ValueError('Image URL must be public HTTPS without credentials')
    for r in d['references']:
        if r.get('url') and not r['url'].startswith('https://'):raise ValueError('Reference URL must use HTTPS')
    for a in d.get('attachments',[]):safe_file(root,a)
    return assets


def render(d,t,sources):
    if t.get('calibrated_hgy'):
        from hgy_render import render as hgy_render
        return hgy_render(d,sources)
    captions=[];md=['# '+d['title'],'',d.get('deck','')];used=[]
    def figure(ident,cover=False):
        a=next(x for x in d['assets'] if x['id']==ident);used.append(ident)
        alt=a.get('alt') or a['caption'];src=html.escape(sources[ident],quote=True)
        img='<img src="'+src+'" alt="'+html.escape(alt,quote=True)+'" style="display:block;width:100%;height:auto;border-radius:'+t['radius']+';"/>'
        md.extend(['',f'![{alt}](images/{ident}{Path(a["path"]).suffix.lower()})',a['caption']])
        if not cover:
            captions.append(a['caption'])
            img+=para(a['caption'],'font-size:13px;color:#667169;margin-top:10px;margin-bottom:0;')
        return section('margin:24px 0;',img)
    out=[para('田间观察 · 科学种田' if d['audience']=='farmers' else '农业研究 · 论文解读',f'font-size:12px;letter-spacing:2px;color:{t["accent"]};')]
    out.append(para(d['title'],f'font-size:27px;line-height:1.5;font-weight:700;color:{t["ink"]};'))
    if d.get('deck'):out.append(para(d['deck'],'font-size:15px;color:#6B746D;'))
    out.append(figure(d['cover'],True))
    for s in d['lead']:out.append(para(s));md.extend(['',s])
    summary=para('一眼看懂' if d['audience']=='farmers' else '研究要点',f'font-size:16px;font-weight:700;color:{t["accent"]};')
    for i,s in enumerate(d['takeaways'],1):summary+=para(f'{i:02d}  {s}','font-size:15px;margin-bottom:10px;')
    out.append(section(f'padding:20px;background:{t["pale"]};border-left:4px solid {t["accent"]};border-radius:{t["radius"]};margin:24px 0;',summary))
    md.extend(['','## 一眼看懂']+['- '+s for s in d['takeaways']])
    out.append(figure(d['overview']))
    for n,sec in enumerate(d['sections'],1):
        heading=para(f'{n:02d}',f'font-size:13px;letter-spacing:3px;color:{t["gold"]};margin-bottom:5px;')+para(sec['title'],f'font-size:22px;font-weight:700;line-height:1.5;color:{t["accent"]};margin-bottom:12px;')
        out.append(section('margin:40px 0 22px;border-bottom:1px solid #DCE3DB;',heading))
        md.extend(['','## '+sec['title']])
        for b in sec['blocks']:
            kind=b['type']
            if kind=='p':out.append(para(b['text']));md.extend(['',b['text']])
            elif kind=='image':out.append(figure(b['asset']))
            elif kind=='callout':
                out.append(section(f'padding:18px 20px;background:{t["pale"]};border-radius:{t["radius"]};margin:24px 0;',para(b.get('label','提示'),f'font-weight:700;color:{t["accent"]};margin-bottom:8px;')+para(b['text'],'font-size:15px;margin-bottom:0;')))
                md.extend(['','> '+b.get('label','提示')+'：'+b['text']])
            elif kind=='list':
                for j,s in enumerate(b['items'],1):out.append(para(f'{j}. {s}'));md.extend(['',f'{j}. {s}'])
            elif kind=='stats':
                cards=''
                for stat in b['items']:
                    cards+=section('padding:14px 0;border-bottom:1px solid #DCE3DB;',para(stat['value'],f'font-size:30px;font-weight:700;color:{t["accent"]};line-height:1.2;margin-bottom:6px;')+para(stat['label'],'font-size:14px;margin-bottom:0;'))
                    md.extend(['',stat['value']+'｜'+stat['label']])
                out.append(section('margin:24px 0;padding:0 20px;',cards))
    if d.get('closing'):out.append(section(f'margin:36px 0;padding:22px 0;border-top:2px solid {t["accent"]};',para(d['closing'],'font-weight:700;margin-bottom:0;')));md.extend(['',d['closing']])
    ref=para('论文与图源','font-size:14px;font-weight:700;')
    md.extend(['','## 论文与图源'])
    for r in d['references']:
        label=text(r['text'])
        if r.get('url'):label='<a href="'+html.escape(r['url'],quote=True)+'" style="color:'+t['accent']+';text-decoration:underline;">'+label+'</a>'
        ref+='<p style="font-size:12px;line-height:1.8;word-break:break-all;">'+label+'</p>'
        md.append(r['text']+' '+r.get('url',''))
    if d.get('disclosure'):ref+=para(d['disclosure'],'font-size:12px;');md.extend(['',d['disclosure']])
    out.append(section('margin:28px 0 0;padding-top:20px;border-top:1px solid #DCE3DB;color:#6B746D;',ref))
    body=section('max-width:680px;margin:0 auto;padding:24px 18px;background:#FFFFFF;font-family:system-ui,-apple-system,BlinkMacSystemFont,Microsoft YaHei,sans-serif;font-size:17px;color:#303A34;word-wrap:break-word;box-sizing:border-box;', ''.join(out))
    return body,'\n'.join(md),'\n\n'.join(captions),used


PREVIEW='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>__TITLE__</title></head><body style="margin:0;background:#EDF0EB;"><nav style="padding:12px;text-align:center;font:14px sans-serif;"><button onclick="copyArticle()">复制图文正文</button>　<span id="copy-status">图片能否保留请在秀米导入后检查</span></nav><main id="article">__BODY__</main><script>async function copyArticle(){const a=document.getElementById('article');const s=document.getElementById('copy-status');try{await navigator.clipboard.write([new ClipboardItem({'text/html':new Blob([a.innerHTML],{type:'text/html'}),'text/plain':new Blob([a.innerText],{type:'text/plain'})})]);s.textContent='已复制正文，请粘贴后检查图片';}catch(e){const r=document.createRange();r.selectNodeContents(a);const sel=window.getSelection();sel.removeAllRanges();sel.addRange(r);s.textContent='已选中正文，请按Ctrl+C复制';}}</script></body></html>'''


def build(article,out,theme=None,mapping=None,long_image=False,long_backend='pymupdf'):
    article=Path(article).resolve();root=article.parent;out=Path(out).resolve()
    d=json.loads(article.read_text(encoding='utf-8-sig'));mapping=mapping or {}
    selected=theme or d.get('theme','hgy')
    if selected not in THEMES:raise ValueError('Unknown theme')
    assets=validate(d,root,mapping)
    if out==root or root.is_relative_to(out):raise ValueError('Output must not contain the input job')
    if out.exists() and any(out.iterdir()):raise ValueError('Output must be empty; use a new version')
    z=out.parent/(out.name+'.zip')
    if z.exists():raise FileExistsError('Refusing to overwrite '+str(z))
    t=dict(THEMES[selected])
    if selected=='hgy':t['calibrated_hgy']=True
    embedded={k:'data:'+mimetypes.guess_type(p.name)[0]+';base64,'+base64.b64encode(p.read_bytes()).decode() for k,(a,p) in assets.items()}
    body,md,captions,used=render(d,t,embedded)
    imported,_,_,_=render(d,t,{**embedded,**mapping})
    report=audit(imported)
    if report['errors']:raise ValueError(report['errors'])
    out.mkdir(parents=True,exist_ok=True);(out/'images').mkdir()
    assetmap=[]
    for ident,(a,p) in assets.items():
        rel='images/'+ident+p.suffix.lower();shutil.copy2(p,out/rel)
        assetmap.append({'id':ident,'local':rel,'url':mapping.get(ident),'caption':a['caption'],'kind':a.get('kind','unspecified')})
    canonical=dict(d);canonical['theme']=selected;canonical['assets']=[{**a,'path':'images/'+k+p.suffix.lower()} for k,(a,p) in assets.items()]
    for attachment in d.get('attachments',[]):
        target=out/attachment;target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():raise ValueError('Attachment collides with generated asset')
        shutil.copy2(safe_file(root,attachment),target)
    report.update(theme=selected,audience=d['audience'],missing_remote_images=sorted(set(used)-set(mapping)),
                  import_status='candidate_embedded' if set(used)-set(mapping) else 'https_mapped_unverified',
                  visual_review='not_run',scientific_review='agent_required')
    files={'秀米导入.html':imported,'预览_单文件.html':PREVIEW.replace('__TITLE__',html.escape(d['title'])).replace('__BODY__',body),
           '正文.md':md,'中文图注.txt':captions,'article.json':json.dumps(canonical,ensure_ascii=False,indent=2),
           'asset-map.json':json.dumps(assetmap,ensure_ascii=False,indent=2),'检查报告.json':json.dumps(report,ensure_ascii=False,indent=2),
           '导入说明.txt':'预览_单文件.html可独立打开。秀米导入.html为内联正文。\n当前状态：'+report['import_status']+'。尚未在秀米实机验证。\n若图片被过滤，上传images内素材，按asset-map.json替换；或取得HTTPS地址后以--image-map重建。\n静态检查不证明科学准确性或平台兼容性；发布前检查中文、图注和手机显示。'}
    for name,content in files.items():(out/name).write_text(content,encoding='utf-8')
    if long_image:
        if long_backend=='pymupdf':
            from render_long_image import render as render_long
            report['long_image']=render_long(out/'预览_单文件.html',out/'long-image')
        elif long_backend=='browser':
            import subprocess
            subprocess.run(['node',str(Path(__file__).with_name('render_long_image.cjs')),
                            '--input',str(out/'预览_单文件.html'),'--out',str(out/'long-image')],check=True)
            report['long_image']=json.loads((out/'long-image'/'render-report.json').read_text(encoding='utf-8'))
        else:raise ValueError('Unknown long-image backend')
        (out/'检查报告.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:
        for p in out.rglob('*'):
            if p.is_file():f.write(p,p.relative_to(out.parent))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('article');p.add_argument('--out',required=True)
    p.add_argument('--theme',choices=THEMES);p.add_argument('--image-map')
    p.add_argument('--long-image',action='store_true');p.add_argument('--long-backend',choices=['pymupdf','browser'],default='pymupdf');a=p.parse_args()
    mapping=json.loads(Path(a.image_map).read_text(encoding='utf-8-sig')) if a.image_map else None
    print(json.dumps(build(a.article,a.out,a.theme,mapping,a.long_image,a.long_backend),ensure_ascii=False,indent=2))
