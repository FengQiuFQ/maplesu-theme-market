# 主题源发布

本仓库维护 FPT 主题、预览、JSON 数组索引与来源记录。投稿通过 Fork/PR 或 Issue 提交。`stage` 只导出静态站点，远程部署结果通过下载与应用导入验收确认。

## 本地检查与导出

以下命令在主题仓库根目录执行；输出目录须为此前不存在的新目录：

```shell
python -m pip install -r requirements.txt
python -m unittest discover -s tools -p "test_*.py" -v
python tools/theme_market.py check
python tools/check_maintainers.py
python tools/theme_market.py stage --out ../theme-pages-staging
```

输出包含 `index.json`、`.nojekyll`、`catalog.json`、索引引用的主题包及预览。`catalog.json` 的 `published=false` 表示本地暂存结果。索引采用与 FinaSU 兼容的 JSON 数组，站点资源使用绝对 HTTPS 地址。

## 维护版本与来源

投稿见 [CONTRIBUTING.md](CONTRIBUTING.md)。通过 `add` 维护稳定 ID；内容变化时更新 `meta_version`，同一版本的字节保持不变，旧包保留。主题、预览、作者、资源来源和 `maintainers.json` 一起审阅。

发行前执行：

```shell
python tools/check_maintainers.py --release
```

待确认条目会阻止发行检查通过。当前 Comic 插画仍待来源复核，完成实际资源许可登记后再更新其状态。

## GitHub Pages 与备用源

独立仓库为 `FengQiuFQ/maplesu-theme-market`。启用 GitHub Pages 的 GitHub Actions 发布方式；合并到 `main` 后，Pages 工作流在包结构、维护登记和测试全部通过后上传暂存树并部署。

完整维护仓库保留工具、依赖、来源、维护登记和协作模板。raw 备用源使用仓库根目录的 `index.json`、`packages/`、`previews/`；它们与 Pages 导出保持同一内容与摘要。

| 入口 | 地址 |
| --- | --- |
| 主索引 | `https://fengqiufq.github.io/maplesu-theme-market/index.json` |
| 备用索引 | `https://raw.githubusercontent.com/FengQiuFQ/maplesu-theme-market/main/index.json` |

部署后核对两端索引 SHA-256，下载引用的包并校验 `download_sha256`。再在应用中走预览、下载、本地库、导入确认、应用、导出再导入流程，分别记录站点和应用验收。

修改域名或仓库名时，同步调整 `theme_market.py` 中的主备根地址与应用 `ThemeStoreSource.kt` 的内置端点。自定义源的接入方式见主仓库主题指南。

资源版权与移除请求通过 [COPYRIGHT.md](COPYRIGHT.md) 及专用 Issue 处理。
