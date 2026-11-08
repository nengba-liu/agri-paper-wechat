"""Checks real offline rendering, segment continuity and failure behavior."""
import json
import tempfile
import unittest
from pathlib import Path
import fitz
from render_long_image import render


class LongImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.root = Path(self.temp.name)
        self.source = self.root/'article.html'
    def tearDown(self):
        self.temp.cleanup()
    def write(self, body):
        self.source.write_text('<main id="article">'+body+'</main>', encoding='utf-8')
    def test_real_render_and_segments(self):
        self.write('<p>水稻的科学证据，不能等同生产处方。</p>'*100)
        r=render(self.source,self.root/'out',segment_height=300)
        self.assertGreater(len(r['segments']),1)
        self.assertEqual(r['segments'][0]['top'],0)
        for a,b in zip(r['segments'],r['segments'][1:]):
            self.assertEqual(a['bottom'],b['top'])
        self.assertEqual(r['segments'][-1]['bottom'],r['height'])
        pix=fitz.Pixmap(str(self.root/'out'/r['full_image']))
        self.assertEqual((pix.width,pix.height),(r['width'],r['height']))
        with self.assertRaises(ValueError):render(self.source,self.root/'out')
    def test_oversize_segments_only(self):
        self.write('<p>科学种田</p>'*30)
        r=render(self.source,self.root/'out',max_pixels=1)
        self.assertIsNone(r['full_image']);self.assertTrue(r['segments'])
    def test_missing_remote_and_broken_images(self):
        for i,src in enumerate(['https://example.org/image.png','file:///private.png','data:image/png;base64,YmFk']):
            self.write(f'<img src="{src}">')
            with self.assertRaises(Exception):render(self.source,self.root/str(i))
    def test_dimensions_and_no_article(self):
        self.write('<p>test</p>')
        with self.assertRaises(ValueError):render(self.source,self.root/'out',width=10)
        self.source.write_text('<h1>no article</h1>',encoding='utf-8')
        with self.assertRaises(ValueError):render(self.source,self.root/'out')


if __name__=='__main__':unittest.main()
