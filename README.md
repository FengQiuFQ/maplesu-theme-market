<div align="center">

# MapleSU Themes

**为日常使用，留一点自己的风格。**

FinaSU-compatible · FPT · Community maintained

[投稿与维护](CONTRIBUTING.md) · [发布](PUBLISH.md) · [版权问题](COPYRIGHT.md) · [Telegram](https://t.me/KernelMapleSU)

</div>

## 一个开放的主题源

本仓库维护 MapleSU 主题、预览、来源与静态索引。主题作者通过 Fork / PR 共同维护条目，保留原作者和作品许可。主题格式与导入体验主要参考 [FinaSU](https://github.com/LyraVoid/FinaSU)，沿用 JSON 数组索引与 `.fpt` 容器。

MapleSU 支持 FinaSU、MapleSU 和自定义 HTTPS 主题源。首次运行默认选择 FinaSU，不因本仓库更新而变更用户已有选择。主题导入与模块执行分开。

## 开始维护

| 想做什么 | 入口 |
| --- | --- |
| 投稿新主题、发布更新、交接维护 | [贡献指南](CONTRIBUTING.md) |
| 查看作者与来源核对状态 | [maintainers.json](maintainers.json) · `provenance/` |
| 导出静态站点与配置镜像 | [发布指南](PUBLISH.md) |
| 报告版权、署名或删除问题 | [版权说明](COPYRIGHT.md) · Issue |

```shell
python -m pip install -r requirements.txt
python tools/theme_market.py check
python tools/check_maintainers.py
python -m unittest discover -s tools -p "test_*.py"
```

当前目录含 Default 和 Comic 两个初始主题。Comic 的现有插画来源仍待核清，维护登记中标为待审阅；公开发行检查会阻止未完成来源核对的条目。

## 索引与完整性

条目保留 ID、名称、作者、版本、说明、预览、下载大小与 SHA-256。导入工具验证 FPT、ZIP 路径、资源数量和包元信息，旧包按版本与哈希留存。发布后的主备源由同一静态树生成。

部署目标为 GitHub Pages 和本仓库 raw 镜像，实际状态以发布工作流和下载验证为准。FPT 的协议常量不作为作者身份认证；资源许可另外核对。

## 许可与致谢

感谢 FinaSU 的主题生态、主题作者和维护者。本仓库原创工具与维护文档采用 [GPL-3.0-or-later](LICENSE)；投稿包和资源采用各自许可，见 [NOTICE](NOTICE)、来源记录和 [COPYRIGHT.md](COPYRIGHT.md)。
