# FastData

基于 NodeGraphQt 的桌面端节点工作流工具，用于图片批处理与异步 AI 生图。把"图生图 / 文生图 / 格式转换 / 尺寸调整 / Prompt 批量生成"等流程组织成"节点 + 连线"，在画布上完成配置与运行。

- 界面：PySide6 + NodeGraphQt，默认深色主题
- 图片处理：Pillow
- 异步生图：aiohttp（GrsAI nano-banana / gpt-image-2 接口）
- 配置与工作流：本地 JSON
- Python：3.11，使用 `uv` 管理环境

## 环境配置（uv）

需要先安装 [uv](https://docs.astral.sh/uv/)。

github: https://github.com/astral-sh/uv

windows使用powershell安装uv
```
# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

uv安装完成后可以用,下面的命令来检查有没有安装成功，出现类似uv 0.11.23 (3cdf50e09 2026-06-19 x86_64-pc-windows-msvc)说明安装成功
```
uv --version
```

uv安装完成后，使用git clone，或者直接下载压缩包解压，并进入文件夹执行以下命令即可安装并运行。
```bash
# 1. 同步依赖（会自动创建 .venv 并按 uv.lock 锁定版本）
uv sync

# 2. 启动应用
uv run python app.py
```

`pyproject.toml` 固定 `requires-python = ">=3.11,<3.12"`，`.python-version` 指定为 `3.11`。如果系统没有合适的解释器，`uv sync` 会自动下载并安装。

验证环境（不启动界面）：

```bash
uv run python -m compileall app.py fastdata
```

## 首次使用

1. 启动后点击工具栏 **Settings**，填写：
   - **API Key**（GrsAI 平台密钥，密码框输入，仅保存在本地）
   - **Base URL**（默认 `https://grsai.dakka.com.cn`）
   - **Concurrency**（并发数，默认 5）
   - **Poll Interval**（轮询间隔秒数，默认 2）
   - **Max Retries**（最大轮询次数，默认 300）
2. 从左侧节点库拖拽节点到画布（或双击节点名添加）。
3. 在右侧 **Properties** 面板编辑节点参数与路径。
4. 连线：输入节点的输出端口连到处理节点的输入端口；处理节点的 `output_folder` 必须连到 `Output Folder` 节点。
5. 选中链路末端的处理节点，点击工具栏 **Run** 执行（执行该节点及其上游依赖）。
6. **Save** / **Open** 保存或加载工作流 JSON 到 `workflows/`。

配置文件位于 `config/config.json`（已加入 `.gitignore`，不会提交）。API Key 在日志中只以脱敏形式出现。

## 节点说明

**Input**
- **Path Input**：提供文件夹路径（图片输入、参考图、目标图等）
- **Prompt Input**：输入 / 保存一段 Prompt 文本，可在画布上直接编辑
- **Output Folder**：提供输出目录，所有写文件的处理节点都通过端口接收

**Generate**（调用 GrsAI 异步接口，支持停止）
- **img2img-banana**：图生图，默认模型 `nano-banana-2`，支持 `aspect_ratio`、`image_size`、`only_missing`
- **img2img-gpt**：图生图，默认模型 `gpt-image-2`，分辨率由 `aspect_ratio`（比例或像素值）控制
- **Text2Img**：文生图，按 `count` 批量生成

**Image**（本地 Pillow 处理）
- **Image To PNG**：转 RGB PNG
- **Image To JPG**：转 RGB JPG，可设置 `quality`
- **Resize To Reference**：把「源图片」按同名「参考图」的尺寸等比缩放并居中裁剪后输出。参考图只提供尺寸、不会被修改；源图片才是被处理并输出的图片
- **Resize Image**：自定义宽高缩放，支持 `stretch` / `fit` / `fill_crop` 模式与 `png` / `jpg` / `keep` 输出格式

**Prompt**
- **Prompt Batch Generate**：将一段 Prompt 批量保存为 txt 文件

## 执行模型

- **Run** 执行当前选中处理节点及其上游可执行依赖（Run To Selected）。输入节点与 `Output Folder` 节点只提供参数，不作为可执行节点运行。
- 长耗时任务在后台 worker 线程执行，不阻塞 UI；生图任务可用工具栏 **Stop** 中断。
- 顶部工具栏右侧显示紧凑任务进度（`Idle` / `Running 1/3` / `Done` / `Failed`），日志区折叠后仍可见。
- 节点本体显示 idle / running / success / error 状态，错误信息写入底部日志并以弹窗提示。

## 常用工作流示例

```
图生图：    Path Input ─┐
            Prompt Input ─┼─▶ img2img-banana ──▶ generated_images
            Output Folder ┘

文生图：    Prompt Input ─┐
            Output Folder ─┴─▶ Text2Img ──▶ generated_images

PNG 转换：  Path Input ─┐
            Output Folder ─┴─▶ Image To PNG

尺寸匹配：  Path Input (reference, 仅取尺寸) ─┐
            Path Input (source, 被处理并输出) ─┼─▶ Resize To Reference
            Output Folder                     ─┘
```

## 项目结构

```
fastdata/
├── app.py                # 入口
├── pyproject.toml        # 依赖声明
├── uv.lock               # 依赖锁
├── fastdata/
│   ├── config.py         # 配置读写
│   ├── core/             # 业务逻辑（生成、转换、缩放、Prompt 写入）
│   ├── nodes/            # 节点定义
│   └── ui/               # 主窗口、画布、属性面板、worker、主题
├── config/               # config.json（gitignored）
├── workflows/            # 工作流 JSON
└── data/                 # 默认输入/输出目录（gitignored）
```
