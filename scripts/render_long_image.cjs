#!/usr/bin/env node
/** Render locally generated article HTML into a PNG and numbered segments.
 * No user browser profile, cookies, or network requests are used.
 */
const fs = require('node:fs/promises');
const path = require('node:path');
const { chromium } = require('playwright');

function options(argv) {
  const o = { width: 430, scale: 2, segmentHeight: 2400, maxPixels: 120000000 };
  const keys = {'--input':'input','--out':'out','--width':'width','--scale':'scale','--segment-height':'segmentHeight','--browser':'browser','--max-pixels':'maxPixels'};
  for (let i=0;i<argv.length;i++) {
    if (argv[i]==='--help') {o.help=true;continue;}
    const k=keys[argv[i]];if(!k || !argv[i+1])throw Error('Unknown or incomplete argument: '+argv[i]);
    o[k]=['width','scale','segmentHeight','maxPixels'].includes(k)?Number(argv[++i]):argv[++i];
  }
  if(o.help)return o;
  if(!o.input||!o.out)throw Error('Provide --input generated.html --out new-output-directory');
  if(!Number.isInteger(o.width)||o.width<320||o.width>1600)throw Error('Width must be an integer from 320 to 1600');
  if(!Number.isFinite(o.scale)||o.scale<1||o.scale>3)throw Error('Scale must be from 1 to 3');
  if(!Number.isInteger(o.segmentHeight)||o.segmentHeight<300||o.segmentHeight>6000)throw Error('Segment height must be from 300 to 6000');
  if(!Number.isFinite(o.maxPixels)||o.maxPixels<1000000||o.maxPixels>200000000)throw Error('max-pixels must be from 1M to 200M');
  if(o.browser&&!['chrome','msedge','chromium'].includes(o.browser))throw Error('Browser must be chromium, chrome, or msedge');
  return o;
}

async function render(o) {
  const input=path.resolve(o.input), out=path.resolve(o.out);
  const html=await fs.readFile(input,'utf8');
  let entries;try{entries=await fs.readdir(out);}catch(e){if(e.code!=='ENOENT')throw e;entries=[];}
  if(entries.length)throw Error('Output is not empty; choose a new directory');
  // Use the embedded, portable HTML produced by build_article.py.
  // Never access arbitrary local or remote image URLs supplied in untrusted HTML.
  const browser=await chromium.launch({headless:true,...(o.browser&&o.browser!=='chromium'?{channel:o.browser}:{})});
  try {
    const context=await browser.newContext({viewport:{width:o.width,height:900},deviceScaleFactor:o.scale,javaScriptEnabled:false,serviceWorkers:'block'});
    await context.route('**/*',route=>route.abort());
    const page=await context.newPage();
    await page.setContent(html,{waitUntil:'load',timeout:30000});
    await page.addStyleTag({content:'html,body{margin:0!important;padding:0!important;background:white!important;}body>nav{display:none!important;}*{animation:none!important;transition:none!important;}'});
    const metrics=await page.evaluate(async()=>{
      await document.fonts.ready;
      const images=Array.from(document.images);
      await Promise.all(images.map(im=>im.decode().catch(()=>{})));
      const broken=images.map((im,i)=>({index:i,ok:im.complete&&im.naturalWidth>0})).filter(x=>!x.ok);
      const root=document.querySelector('#article')||document.body;
      const r=root.getBoundingClientRect();
      return {width:innerWidth,height:Math.ceil(Math.max(document.documentElement.scrollHeight,document.body.scrollHeight)),scrollWidth:document.documentElement.scrollWidth,images:images.length,broken,article:{x:r.x,y:r.y,width:r.width,height:r.height},textLength:root.innerText.length};
    });
    if(metrics.broken.length)throw Error('Broken or non-embedded images at indexes: '+metrics.broken.map(x=>x.index).join(','));
    if(metrics.scrollWidth>o.width+1)throw Error('Horizontal overflow: '+metrics.scrollWidth+' > '+o.width);
    if(!metrics.textLength)throw Error('Article has no readable text');
    if(metrics.height>300000)throw Error('Article exceeds 300000 CSS pixels; split the article first');
    await fs.mkdir(out,{recursive:true});
    const report={input:path.basename(input),viewportWidth:o.width,scale:o.scale,pixelWidth:Math.round(o.width*o.scale),pixelHeight:Math.round(metrics.height*o.scale),images:metrics.images,missingImages:0,horizontalOverflow:false,textLength:metrics.textLength,fullImage:null,segments:[],platformVerified:false};
    if(report.pixelWidth*report.pixelHeight<=o.maxPixels && report.pixelHeight<=60000){
      await page.screenshot({path:path.join(out,'article-long.png'),fullPage:true,animations:'disabled'});report.fullImage='article-long.png';
    }else{report.fullImageOmitted='Exceeds the full-image memory/height limit; all numbered segments are provided.';}
    for(let y=0,i=1;y<metrics.height;y+=o.segmentHeight,i++){
      const name='segment-'+String(i).padStart(2,'0')+'.png';
      const height=Math.min(o.segmentHeight,metrics.height-y);
      await page.screenshot({path:path.join(out,name),clip:{x:0,y,width:o.width,height},animations:'disabled'});
      report.segments.push({file:name,cssTop:y,cssHeight:height});
    }
    await fs.writeFile(path.join(out,'render-report.json'),JSON.stringify(report,null,2),'utf8');
    return report;
  } finally {await browser.close();}
}
if(require.main===module){
  (async()=>{
    const o=options(process.argv.slice(2));
    if(o.help){console.log('node scripts/render_long_image.cjs --input preview.html --out new-dir [--width 430] [--scale 2] [--segment-height 2400] [--browser msedge]');return;}
    console.log(JSON.stringify(await render(o),null,2));
  })().catch(e=>{console.error(e.message);process.exitCode=1;});
}
module.exports={render,options};
