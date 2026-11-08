# 微信参考读取

2026-11-08用户提供的路径已验证成功；先读当前浏览器文档，不假定各环境API相同。

1. 保留browser绑定，先tabs.list()查目标URL。支持时用tabs.get(真实ID)获取已有页，再playwright.domSnapshot()；避免重复使用自动AX读取的创建/选择入口。
2. DOM确认正文后，只读evaluate提取#activity-name、#publish_time、#js_name、#js_content的innerText/outerHTML及其img的data-src/src/alt。不改DOM、不读隐藏应用状态。
3. 核对标题、作者、开头、章节及文末来源/署名。标题加载成功不等于全文读取成功。
4. 图像分记“有URL”“实际加载”“目视核对”。naturalWidth=1常为微信懒加载占位，complete=true仍不能视为图片成功；正常滚动后核对或使用用户PDF。不改写src强制加载。
5. 超时先列现有tabs，不反复创建/刷新。若环境重置，重读文档/清单；数字browser ID可能改变，可使用文档支持的稳定类型入口。
6. 登录、验证码、下架提示和工具明确停止是不同阻碍，分别报告，不绕过。一条通道超时不能推断微信文章不可访问。PDF可独立参考，但不伪称网页已读。

已验证路径：`browser.tabs.list()` → `browser.tabs.get(真实ID)` → `tab.playwright.domSnapshot()` → `tab.playwright.evaluate(只读正文/样式提取)`。
