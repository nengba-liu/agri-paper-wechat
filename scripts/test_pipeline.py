"""Behavioral checks for portability, validation and safe rendering (stdlib only)."""
import base64, json, uuid, unittest, zipfile
from pathlib import Path
from build_article import build
from audit_html import audit

PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1sAAAAASUVORK5CYII=')

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.root=Path.cwd()/'work'/'agri-skill-tests'/uuid.uuid4().hex
        self.job=self.root/'job';self.job.mkdir(parents=True)
        (self.job/'cover.png').write_bytes(PNG);(self.job/'overview.png').write_bytes(PNG)
        self.d={'title':'农业 & 科学 <测试>','audience':'farmers','lead':['试验 <script>alert(1)</script>'],
                'takeaways':['有差异'],'assets':[{'id':x,'path':x+'.png','caption':'图注'} for x in ['cover','overview']],
                'cover':'cover','overview':'overview','sections':[{'title':'结果','blocks':[{'type':'p','text':'**单位面积**不能写成单株。'}]}],
                'references':[{'text':'论文','url':'https://doi.org/10.1016/j.fcr.2026.110773'}]}
    def write(self):
        p=self.job/'article.json';p.write_text(json.dumps(self.d),encoding='utf-8');return p
    def test_themes_and_audiences(self):
        for audience in ['farmers','researchers']:
            for theme in ['hgy','non-hgy']:
                self.d['audience']=audience;out=self.root/(audience+theme)
                r=build(self.write(),out,theme)
                self.assertTrue(r['static_pass']);self.assertFalse(r['platform_verified'])
                content=(out/'预览_单文件.html').read_text(encoding='utf-8')
                self.assertIn('data:image/png;base64,',content)
                fragment=(out/'秀米导入.html').read_text(encoding='utf-8')
                self.assertNotIn('<script>',fragment);self.assertIn('&lt;script&gt;',fragment)
                self.assertEqual(r['images'],1 if theme=='hgy' else 2)
                with zipfile.ZipFile(str(out)+'.zip') as z:
                    self.assertIsNone(z.testzip());self.assertTrue(any(n.endswith('/images/cover.png') for n in z.namelist()))
    def test_missing_image_rejected(self):
        (self.job/'cover.png').unlink()
        with self.assertRaises(FileNotFoundError):build(self.write(),self.root/'out')
    def test_long_image_is_packaged_and_reported(self):
        out=self.root/'long-output'
        r=build(self.write(),out,long_image=True)
        self.assertEqual(r['long_image']['backend'],'pymupdf')
        with zipfile.ZipFile(str(out)+'.zip') as archive:
            self.assertTrue(any(n.endswith('/long-image/article-long.png') for n in archive.namelist()))
            report=json.loads(archive.read(out.name+'/检查报告.json'))
            self.assertEqual(report['long_image']['full_image'],'article-long.png')
    def test_path_traversal_rejected(self):
        (self.root/'outside.png').write_bytes(PNG);self.d['assets'][0]['path']='../outside.png'
        with self.assertRaises(ValueError):build(self.write(),self.root/'out')
    def test_image_mapping_status(self):
        mapping={x:'https://example.org/'+x+'.png' for x in ['cover','overview']}
        out=self.root/'out';r=build(self.write(),out,mapping=mapping)
        self.assertEqual(r['import_status'],'https_mapped_unverified');self.assertFalse(r['platform_verified'])
        self.assertNotIn('data:image',(out/'秀米导入.html').read_text(encoding='utf-8'))
        self.assertIn('data:image',(out/'预览_单文件.html').read_text(encoding='utf-8'))
    def test_bad_mapping_and_unknown_block(self):
        with self.assertRaises(ValueError):build(self.write(),self.root/'out',mapping={'cover':'javascript:alert(1)'})
        self.d['sections'][0]['blocks']=[{'type':'raw_html','html':'<script></script>'}]
        with self.assertRaises(ValueError):build(self.write(),self.root/'out')
    def test_audit_detects_platform_hazards(self):
        r=audit('<div onclick="alert(1)">bad<img src="file:///private.png"></div>')
        self.assertFalse(r['static_pass']);self.assertGreater(len(r['errors']),2)
    def test_manual_overview_and_optional_cover(self):
        self.d['layout']={'overview_position':'manual','show_cover':True}
        with self.assertRaises(ValueError):build(self.write(),self.root/'missing')
        self.d['sections'][0]['blocks'].append({'type':'image','asset':'overview'})
        r=build(self.write(),self.root/'manual')
        self.assertEqual(r['images'],2)
    def test_research_metadata_and_literal_emphasis(self):
        self.d['audience']='researchers'
        self.d['paper_info']=[{'label':'文章标题','value':'Test <paper> & evidence'}]
        self.d['sections'].append({'title':'知识卡片','role':'knowledge','blocks':[{'type':'p','text':'==<script>== **术语**'}]})
        out=self.root/'research';r=build(self.write(),out)
        fragment=(out/'秀米导入.html').read_text(encoding='utf-8')
        self.assertTrue(r['static_pass']);self.assertIn('Test &lt;paper&gt; &amp; evidence',fragment)
        self.assertNotIn('<script>',fragment)
        self.assertIn('知识卡片',(out/'正文.md').read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()
