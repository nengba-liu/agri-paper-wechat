const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs/promises');
const os=require('node:os');
const path=require('node:path');
const {render,options}=require('./render_long_image.cjs');
const png='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1sAAAAASUVORK5CYII=';
async function fixture(t,body){const dir=await fs.mkdtemp(path.join(os.tmpdir(),'agri-render-'));t.after(()=>fs.rm(dir,{recursive:true,force:true}));const input=path.join(dir,'article.html');await fs.writeFile(input,'<!doctype html><meta charset="utf-8"><body><main id="article">'+body+'</main></body>');return{input,out:path.join(dir,'out'),width:375,scale:1,segmentHeight:300,maxPixels:120000000,browser:process.env.AGRI_TEST_BROWSER};}
test('validates dimensions',()=>{assert.throws(()=>options(['--input','a','--out','b','--width','NaN']));assert.throws(()=>options(['--input','a','--out','b','--scale','0']));});
test('Chinese text and embedded images render into full PNG and continuous segments',async t=>{
  const o=await fixture(t,'<p>水稻试验｜中文图注</p><img src="data:image/png;base64,'+png+'"><div style="height:1200px">结论与证据</div><p>文章结束</p>');const r=await render(o);assert.equal(r.images,1);assert.equal(r.fullImage,'article-long.png');assert.ok(r.segments.length>3);assert.equal(r.segments.reduce((s,x)=>s+x.cssHeight,0),r.pixelHeight);assert.ok((await fs.stat(path.join(o.out,r.fullImage))).size>1000);await assert.rejects(()=>render(o),/not empty/);
});
test('missing image fails instead of exporting a blank placeholder',async t=>{const o=await fixture(t,'<p>测试</p><img src="data:image/png;base64,broken">');await assert.rejects(()=>render(o),/Broken/);});
test('overflow fails',async t=>{const o=await fixture(t,'<p style="width:1500px">过宽内容</p>');await assert.rejects(()=>render(o),/overflow/);});
test('oversized full image falls back to complete segments',async t=>{const o=await fixture(t,'<p>长文</p><div style="height:3000px"></div>');o.maxPixels=1000000;const r=await render(o);assert.equal(r.fullImage,null);assert.ok(r.segments.length>9);});
