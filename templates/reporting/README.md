# Reporting 模板目录说明

当前目录与 `core/services/reporting/` 的领域结构保持一致：

- `domains/`：按照业务域划分的模板资源。
  - `domains/exif/`：EXIF 报告模板及片段。
  - `domains/map/`：MAP 多维度报告模板。
  - `domains/map/3cb/`：MAP 报告的 3CB 专用模板与脚本。
- `shared/`：跨领域复用的模板。
  - `shared/partials/`：遗留可复用片段。
  - `shared/error.html`：统一错误页。
- `base.html`：新引擎通用基模板，供 `extends` 使用。
- `README.md`：当前说明文件。

新增模板时，请优先放入 `domains/<domain>/` 或 `shared/` 对应子目录，并同步更新代码中的默认模板路径与别名映射。
