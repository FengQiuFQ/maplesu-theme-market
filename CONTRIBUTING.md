# 投稿与维护主题

主题索引与 `.fpt` 沿用 FinaSU 格式。Fork 本仓库，用 PR 维护自己的条目；不熟悉 Git 的作者也可以使用主题投稿 Issue。

## 准备主题

准备 `.fpt`、PNG/JPEG/WebP 预览、稳定主题 ID、版本、作者和说明。为图片、字体、图标及其他资源提供原作链接与实际许可。使用自己有权分享的资源，不将主题工具的许可直接套用于第三方素材。

在仓库根目录执行，将文件名、ID、来源和许可换成真实值：

```shell
python -m pip install -r requirements.txt
python tools/theme_market.py add --id author.example --package example.fpt --preview preview.png --origin https://github.com/author/example-theme --license CC-BY-4.0
python tools/theme_market.py check
```

在 `maintainers.json` 的 `entries` 中登记相同 ID：`maintainers` 为 GitHub 账号数组，`origin` 为原作链接，`license` 为实际许可，`evidence` 为按版本保存的仓库内来源文件路径。未完成核对时用 `status: pending`，核对完毕后由维护者设为 `ready`。

```shell
python tools/check_maintainers.py
python -m unittest discover -s tools -p "test_*.py" -v
```

## 更新与交接

保持 ID，修改包内 `meta_version` 后重新导入。相同版本不更换包字节；更正内容也使用新版本。工具按 ID/版本/哈希保留旧文件，投稿时不删除原作者与许可。

PR 附上明暗模式、Material/Miuix 的真实预览、验证版本、资源变化和维护登记。维护权交接附上原作者或现任维护者确认；维护账号可以有多位，仓库级合并与发布仍由维护者审核。

## 发布前

`python tools/check_maintainers.py --release` 要求每项来源核对已完成。FPT 的加密常量是格式兼容参数，不代表作者认证；下载摘要校验与资源版权分别处理。发布见 [PUBLISH.md](PUBLISH.md)，版权或下架问题见 [COPYRIGHT.md](COPYRIGHT.md)。
