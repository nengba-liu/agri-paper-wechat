# 整篇长图

默认交付整篇PNG、顺序分段PNG和render-report.json。先完成证据核对、图像与正文审查，再导出长图；不要让长图掩盖正文中的科学错误。

## 默认：离线Python

`python scripts/build_article.py article.json --out 发布目录 --long-image`

已有文件：`python scripts/render_long_image.py --input 预览_单文件.html --out 长图目录`

参数：`--width 430`、`--scale 2`、`--segment-height 2400`。默认输出860像素宽，分段最多4800像素高。仅接受构建器生成的含main#article和嵌入图片的单文件HTML；不读取网络或任意本地图片路径。

PyMuPDF会重排HTML，仅支持部分CSS；长图与浏览器预览不是像素级一致。中文字体由渲染器回退。必须查看输出，若字体或图片异常则修复后交付。

整篇默认预算120M像素且高度不超过60000像素；超出时full_image为null，但segments仍覆盖全文。连续切片可在图文中间切开，不得称为智能分页。宽度支持320—1600，倍率1—3，分段高度300—6000。

## 可选：浏览器渲染

`npm install`，`npx playwright install chromium`，再用 `--long-backend browser`。

独立调用：`node scripts/render_long_image.cjs --input 预览_单文件.html --out 长图目录 --width 430 --scale 2`。也可显式选 `--browser msedge` 或 `chrome`，必须允许本机启动该浏览器。无权启动时明确失败，不能把未执行写成通过。

使用独立无登录状态的浏览器上下文，禁用网页脚本并阻断外部网络请求；仅保留嵌入图片。等待字体和图片解码，检查坏图及横向溢出，隐藏预览复制工具栏。默认Chromium，不自动使用用户浏览器配置。

## 验收

1. 核对标题、首尾完整，最后一段及论文来源未截断。
2. 查看首、中、尾分段，确认中文完整、图片等比、正文清晰。
3. 按报告核对每段首尾坐标连续，总高度一致。
4. 确认缺图检测无报错；代码检测不能替代人工看图。
5. ZIP包含最终长图和报告。长图生成不意味着秀米导入成功或公众号已发布。

报告分别记录backend/pixel dimensions/segments等字段，两种后端字段略有不同，以各自JSON为准。若需改变视觉布局，修改article.json/主题并重新构建，不直接修改统计图的数据标注。
