# 深知写作助手（Qoder Public 版）

这是深知写作助手的 Qoder 分发版本，以 ClawHub Public `3.0.25` 为功能基准，但独立维护和打包。本版本不内置深知搜索 API Key；首次使用前需要用户自行通过 Qoder 渠道注册链接获取并配置 API Key。

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
- 红头文件：通过 `scripts/template_generator.py` 代码化生成红头和表尾，不依赖 `templates/` 中的 Word 模板。

## 依赖

```bash
pip3 install python-docx requests
```

## 配置深知搜索 API Key

1. 访问深知平台注册入口（暂沿用 ClawHub Public 版本）：

```text
https://platform.dknowc.cn/auth/#/register?channel=2787E171-B0E5-4328-9946-47AC52434D1F&type=6
```

2. 注册并登录深知平台
3. 获取深知可信搜索 API Key
4. 将 `config.ini.example` 复制为 `config.ini`
5. 填入你的 API Key：

```ini
[dkag]
api_key=your_api_key_here
```

搜索接口固定为：

```text
https://open.dknowc.cn/dependable/search/
```

不要把包含真实 API Key 的 `config.ini` 上传或公开分享。

## 版本说明

当前 Qoder Public 版版本为 `3.0.25`，功能和内容基准为 ClawHub Public `3.0.25`。

## 常用测试

语法检查：

```bash
python3 -m py_compile scripts/dkag_search.py scripts/merge_search_results.py scripts/format_document.py scripts/template_generator.py
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

## Public 版说明与社区提交待办

- 本版本不内置 API Key。
- 用户通过 Qoder 渠道注册链接获取 API Key。
- 深知搜索、素材分类、Word 生成、异常处理等功能逻辑与自用版一致。
- 如搜索失败或提示 API Key 未配置，请先检查 `config.ini` 是否存在且 `api_key` 是否有效。
- TODO：正式 Qoder 渠道注册链接确定后，将当前暂用的 ClawHub Public 注册链接替换为该链接。
- Qoder 社区发布方式：Fork `Qoder-AI/qoder-community`，在 `src/content/skills-zh/dknowc-official-doc-writer.md` 新增 Agent Skill 条目，按社区贡献指南提交 Pull Request。
- 本渠道已在 `../community/skills-zh/dknowc-official-doc-writer.md` 准备中文社区条目，并使用 `https://github.com/dylanzhangzx/dknowc-official-doc-writer-qoder` 作为公开安装源。
- TODO：提交 Qoder 社区 PR 前，在 fork 后的 `qoder-community` 仓库执行 `npm run build`。
