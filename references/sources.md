# 参考记录

更新于2026-11-08：以下9篇文章均已通过现有浏览器tab绑定和playwright.domSnapshot读取完整正文，包含文章标题、慧耕耘作者标识、章节、图注和文末信息。第一篇另用只读evaluate核实正文4119字符，GEC篇3833字符。旧记录的状态超时不代表文章不可访问。已提取农民版和科研版部分内联样式，并结合4份PDF渲染核对视觉。网页部分图片naturalWidth=1，为懒加载占位，不能声称所有远程图片均已验证加载；完整图像观感主要由PDF支持。

| 链接标识 | 标题/主题 | 发布日期 | 状态 |
|---|---|---|---|
| sRzZGhzMBo6JPeReOYYXBQ | 硬核科普：水稻插得密一点，就能多收粮？ | 2026-11-01 | 全文、图注、样式已读 |
| imH0G924vRsJrUbK3iSAPA | 超强厄尔尼诺背景下，今年小麦怎么播？ | 2026-10-24 | 全文已读，气象事实仅作旧稿内容不作当前预报 |
| mid=2247492487 | 稻田里看不见的排放，怎样才能测清楚？ | 2026-10-15 | 全文已读 |
| 50uuELCh7kL2m1XLtPx8pg | 秋播倒计时，小麦窄行匀播为什么可能更高产？ | 2026-10-01 | 全文已读 |
| xMJ7uRpkzSrweAmJDDKYJw | GEC：复合气候极端事件与中国水稻生产/自给风险 | 2026-10-20 | 全文、部分样式已读；对应PDF732717217 |
| seCOyFREvUWJnu43Z722qA | PNAS：智慧农业技术经济潜力的全球5公里研究 | 2026-10-22 | 全文已读；对应PDF733445625 |
| CpxuFdJU506H6ek99VAr7Q | ISPRS：TMF多模态融合欧盟小麦估产 | 2026-10-10 | 全文已读；杂草模型段主题不一致，排除其内容 |
| 6TNKpIoVIQyHv5xZxmsIbQ | RSE：自适应Sentinel-1指标检测播种收获日期 | 2026-09-30 | 全文已读 |
| bZRid1y6sgfBEN9jI88T0A | AEE：长期秸秆还田、微生物及有机质 | 2026-09-24 | 全文已读；机翻图注与重复栏目不仿制 |

开发时用于视觉校准的用户提供PDF（未随仓库分发）：
- show_733445625_1794145644403.pdf：13页；PNAS科研版，已全文提取、查看栏目/知识卡/亮点页。
- show_732717217_1794145763153.pdf：单页长文；GEC科研版，已全文提取、分段渲染查看。
- show_734853825_1794145731645.pdf：单页长文；水稻导语后接小麦正文，只作视觉参考，不等同已发布水稻稿。
- show_737427759_1794145705604.pdf：单页长文；油菜—水稻轮作科普，已全文提取，查看导语、作物设计图、结果图与页尾。

样式实测与内容规则见hgy-style.md；成功读取路径见browser-reading.md。当前主题为独立实现的近似风格，不声称原模板或像素级复制。

农民版：
- https://mp.weixin.qq.com/s/sRzZGhzMBo6JPeReOYYXBQ
- https://mp.weixin.qq.com/s/imH0G924vRsJrUbK3iSAPA
- https://mp.weixin.qq.com/s?__biz=Mzk4ODIyMDM3NA==&mid=2247492487&idx=1&sn=799a6cb1b8fdc3191c24a132d8deb1f0&chksm=c4c448ba39ca2df18de1850eea61770c091e66f2dda96acb65fed6cda95018100ffa969bd1ed&scene=0&xtrack=1&subscene=90#rd
- https://mp.weixin.qq.com/s/50uuELCh7kL2m1XLtPx8pg

科研版：
- https://mp.weixin.qq.com/s/xMJ7uRpkzSrweAmJDDKYJw
- https://mp.weixin.qq.com/s/seCOyFREvUWJnu43Z722qA
- https://mp.weixin.qq.com/s/CpxuFdJU506H6ek99VAr7Q
- https://mp.weixin.qq.com/s/6TNKpIoVIQyHv5xZxmsIbQ
- https://mp.weixin.qq.com/s/bZRid1y6sgfBEN9jI88T0A

工程参考（已读取README、SKILL.md及通用组件文档）：https://github.com/isjiamu/gzh-design-skill ，作者甲木×摸鱼小李，仓库声明AGPL-3.0。吸收的思路：正文与预览分离、内联样式、语义组件、源与产物双检查。此技能中的Python和HTML组件独立编写，未复制上游源码或主题库；non-hgy为可选独立主题，不宣称等同上游6套主题。

秀米官网：https://xiumi.us/ （已读取，但未取得已登录的HTML导入实测）；官方对接文档入口：https://ent.xiumius.cn/ （访问未成功）。不把第三方教程作为对用户账号功能的确认。
