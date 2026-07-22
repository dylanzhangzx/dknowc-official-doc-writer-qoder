# 深知写作助手（Qoder Public 版）

这是深知写作助手的 Qoder 分发版本。功能逻辑与主干完整版保持一致，但不内置深知搜索 API Key；首次调用本 Skill 时，无论当前任务是否需要搜索，都先由 Agent 通过 MaaS 注册接口完成手机号注册、验证码确认、API Key 获取和本地配置写入，用户只需提供手机号和收到的验证码。

## Qoder 安装

技能目录必须保持为 `dknowc-official-doc-writer/`，且 `SKILL.md` 位于该目录根部。

- Qoder IDE / CLI 用户级安装：复制整个目录到 `~/.qoder/skills/dknowc-official-doc-writer/`。
- Qoder IDE / CLI 项目级安装：复制整个目录到 `.qoder/skills/dknowc-official-doc-writer/`。
- Qoder CLI 运行中可执行 `/skills reload`，再用 `/skills` 检查是否加载。
- QoderWork：在 Skills 页面选择 Install Skill，上传 `SKILL.md` 及其配套目录；也可将整个目录置于 `~/.qoderwork/skills/`。

## 能力范围

- 深知可信搜索：通过 `scripts/dkag_search.py` 调用搜索接口获取政策、数据和案例素材。
- 公文写作流程：由 `SKILL.md` 进行任务路由，按任务复杂度选择直接生成、追问、搜索、审查或严格流水线。
- 搜索策略：`reference/search_policy.md` 保留深知搜索逻辑、素材四分类和来源限制。
- 任务路由：`reference/task_router.md` 定义简单任务、常规任务、复杂任务和高风险任务的处理方式。
- 质量审查：`reference/review_checklist.md` 定义公文内容、素材来源、文种专项和 Word 输出检查项。
- Word 排版：通过 `scripts/format_document.py` 生成普通格式 `.docx`。
- 表格排版：支持标准 Markdown 表格、宽表横向 A4、表题兜底和基础对齐规则。
- 素材来源说明：执行过搜索时，通过 `scripts/source_note_html.py` 生成独立 HTML 溯源页。
- 红头文件：通过 `scripts/template_generator.py` 代码化生成红头和表尾，不依赖 `templates/` 中的 Word 模板。
- PDF：当前 Qoder Public 版不支持自动生成 PDF；用户明确要求 PDF 时，交付 `.docx` 并建议用户使用本机 Word/WPS 另存或导出为 PDF。

## 依赖

```bash
pip3 install python-docx requests
```

还需要 Node.js 18+ 用于调用 MaaS 注册接口：

```bash
node --version
```

当前版本不内置 PDF 生成或转换依赖。正式公文主交付物为 `.docx`；如用户需要 PDF，应使用 Word/WPS 打开 `.docx` 后另存或导出。

## 首次启动初始化

Qoder Public 版的初始化与具体任务无关：只要调用本 Skill 且本地没有 `config.ini`，Agent 就应先引导用户完成注册配置，然后再继续处理原任务。简单通知、改写润色、只生成 Word 等场景也遵循该规则。

## 注册并配置深知搜索 API Key

Qoder Public 版默认使用：

- 接入点 `type=6`，即深知可信搜索。
- 渠道码 `5DBF147C-A4D0-4C3E-AB1A-6C6F5EA39B18`。
- 本地 `config.ini` 保存搜索 Key，由 Agent 自动创建，公开包不携带该文件。

第 1 步，发送短信验证码：

```bash
node scripts/register.mjs send --phone 13812345678
```

返回 `status=true` 后，暂停并请用户提供收到的 6 位验证码。

第 2 步，注册并获取 API Key：

```bash
node scripts/register.mjs register --phone 13812345678 --vcode 123456 --organ 个人 --name 用户
```

成功后，脚本会把 API Key 自动写入本 Skill 根目录下的 `config.ini`，不会在标准输出中返回完整 Key。用户不需要手动复制 Key，也不需要手动编辑配置文件。

如自动注册链路失败，可降级使用 Qoder Public 版当前注册链接手动注册：

```text
https://platform.dknowc.cn/auth/#/register?channel=5DBF147C-A4D0-4C3E-AB1A-6C6F5EA39B18&type=6
```

搜索接口固定为：

```text
https://open.dknowc.cn/dependable/search/
```

`config.ini` 只存在于用户本地安装后的 Skill 目录中，不得上传、打包或公开分享。发布包检查会阻止该文件进入公开包。

## 版本说明

当前 Qoder Public 版基于 `3.1.4`。

## 常用测试

语法检查：

```bash
python3 -m py_compile scripts/dkag_search.py scripts/merge_search_results.py scripts/format_document.py scripts/template_generator.py scripts/initialize.py scripts/check_release.py scripts/source_note_html.py
node --check scripts/register.mjs
```

普通 Word 生成：

```bash
python3 scripts/format_document.py official-docs/input/dknowc-test.md --output dknowc-test.docx
```

红头 Word 生成：

```bash
python3 scripts/template_generator.py 通知 --input dknowc-test.docx --org "XX单位" --doc-number "XX〔2026〕1号" --output dknowc-test-red.docx
```

搜索结果保存：

```bash
python3 scripts/dkag_search.py "人才服务政策" --area 某省 --clean --output result_gd.json
```

多次搜索合并：

```bash
python3 scripts/merge_search_results.py result_gd.json result_bj.json --output merged.json
```

素材来源说明 HTML：

```bash
python3 scripts/source_note_html.py official-docs/input/source-note.json --output source-note.html
```

## Public 版说明

- 本版本不内置 API Key。
- 用户可通过 Agent 调用 `scripts/register.mjs`，用手机号和验证码注册 MaaS 账号并获取深知可信搜索 API Key。
- 注册成功后，Agent 自动把 API Key 写入本地 `config.ini`，用户不需要查看或手动配置 Key。
- 深知搜索、素材分类、素材来源 HTML、Word 生成、红头 Word、异常处理等功能逻辑与主干完整版一致。
- 如搜索失败或提示 API Key 未配置，请重新执行注册流程或检查本地 `config.ini` 是否存在且有效。
- Qoder Public 版使用独立渠道码和专属注册链接。
- Qoder 社区发布方式：Fork `Qoder-AI/qoder-community`，在 `src/content/skills-zh/dknowc-official-doc-writer.md` 新增 Agent Skill 条目，按社区贡献指南提交 Pull Request。
- 本渠道已在 `../community/skills-zh/dknowc-official-doc-writer.md` 准备中文社区条目，并使用 `https://github.com/dylanzhangzx/dknowc-official-doc-writer-qoder` 作为公开安装源。
