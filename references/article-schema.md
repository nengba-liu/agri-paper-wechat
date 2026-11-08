# article.json

每个读者版本一份JSON。相对路径以JSON所在目录为根，不允许越界；先把素材复制进该目录。正文为纯文字，可用 **重点** 和 ==虚线强调== 标记；hgy使用绿色虚线，非hgy使用正文色虚线。不接受任意HTML。封面与概况图是必需资产，不能以占位符通过验收。

```json
{
  "title":"水稻增产，功夫在上一季？",
  "audience":"farmers",
  "theme":"hgy",
  "deck":"油菜—水稻轮作中的跨季管理",
  "lead":["这里写通俗导语。"],
  "takeaways":["前茬管理会影响后茬。","结果存在年际差异。"],
  "assets":[
    {"id":"cover","path":"images/cover.png","caption":"封面概念插画。","kind":"illustration"},
    {"id":"overview","path":"images/overview.png","caption":"全文概况图。虚线为可能机制。","kind":"illustration"},
    {"id":"yield","path":"images/yield.png","caption":"图1｜产量。统计范围、误差、n和来源。","kind":"redraw"}
  ],
  "cover":"cover",
  "overview":"overview",
  "sections":[
    {"title":"先看数据","blocks":[
      {"type":"p","text":"与同年对照相比，**增产幅度存在差异**。"},
      {"type":"image","asset":"yield"},
      {"type":"callout","label":"如何理解","text":"不要把单点试验写成通用处方。"},
      {"type":"stats","items":[{"value":"6.4%","label":"2024年平均增产"},{"value":"14.1%","label":"2025年平均增产"}]},
      {"type":"list","items":["核对田块条件。","先留出对照。"]}
    ]}
  ],
  "closing":"一段面向本读者的收束。",
  "references":[{"text":"Li et al. Field Crops Research 351 (2027): 110773.","url":"https://doi.org/10.1016/j.fcr.2026.110773"}],
  "disclosure":"插画由AI辅助制作；数据图据原文重绘。",
  "attachments":["evidence.csv","data/yield.csv","data/plot.py"]
}
```

audience只接受farmers/researchers；theme接受hgy/non-hgy。blocks只接受p/image/callout/stats/list。图注不藏在图片里，始终作为可编辑正文保留。takeaways建议2—3条。stats每卡一组同口径指标，不混淆年度、单位与分母。核心section原则上有image块；实践小结可用图解或清单。

image-map.json为 `{"cover":"https://已授权素材域名/...png","overview":"https://...", "yield":"https://..."}`，键对应asset id，不是磁盘路径。不伪造URL、不自动上传。所有assets须保留本地文件以保证单文件预览独立可用。

命令：
```
python scripts/extract_pdf.py paper.pdf --out job/source
python scripts/build_article.py job/farmers/article.json --out job/发布/农民版 --theme hgy
python scripts/build_article.py job/researchers/article.json --out job/发布/科研版 --theme non-hgy
python scripts/audit_html.py job/发布/农民版/秀米导入.html
```

每个输出目录必须为空或不存在，防止覆盖。需要更新请换版本目录。脚本生成同名ZIP在目录旁。若增加人工QA记录，应重新打包，并确认ZIP包含最新记录。

## hgy校准版可选字段

```json
{
  "series":"硬核科普系列",
  "layout":{"show_title":true,"show_cover":false,"show_takeaways":false,"overview_position":"intro"},
  "paper_info":[{"label":"文章标题","value":"原文核实的英文题名"},{"label":"中文标题","value":"准确中文题名"},{"label":"发表期刊","value":"期刊名"},{"label":"在线日期","value":"核实后的日期"}],
  "credits":[{"role":"资料整理","name":"本次确认的姓名"}]
}
```

上述占位内容只说明结构，不能进入交付。`paper_info`仅科研版渲染为文章信息；新增科研稿应提供核实字段。`paper_preview`与`brand_footer`可指向assets中的id，分别是论文题头图与本次确认的品牌尾图；未提供就省略，不伪造二维码。credits可省略，不自动继承旧审核人。

封面始终打包，hgy默认不重复插入正文。`overview_position="manual"`要求sections中实际包含overview的image块，以便放在研究方法等适当位置；否则构建报错。`show_title=false`用于平台已单列标题的正文片段。知识卡用section `{"title":"知识卡片","role":"knowledge","blocks":[...]}`生成双线框；科研版takeaways在文末生成蓝框文章亮点。图像asset可额外设置caption_title作为独立图题，caption仍为完整说明。p块可设置`indent:false`用于短引导句。
