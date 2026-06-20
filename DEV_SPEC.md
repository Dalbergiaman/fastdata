# DEV_SPEC

## 项目目标

本项目目标是将 `C:\Users\23774\Documents\0-WORK\CODING\asyncgen-image` 中已经验证过的图片处理与异步生图能力，重做为一个基于 NodeGraphQt 的桌面端节点工作流工具。

核心原则：

- 抛弃参考项目中的 Tkinter/sv-ttk 页面式 UI。
- 保留参考项目中已经可用的业务功能。
- 使用节点图作为主界面，让图片处理流程以“节点 + 连线”的方式组织。
- 第一版保持简洁和审美统一，不做复杂插件系统、云端同步、用户系统或高级资产管理。
- 所有开发以实际可运行、可验证为准；如果本文档与实际实现冲突，以实际实现为准，并同步修正文档。

目标用户是不熟悉命令行的内部用户。用户应能通过节点、参数面板、文件夹选择和运行按钮完成图片生成与批处理工作。

## 参考项目功能来源

参考项目路径：

```text
C:\Users\23774\Documents\0-WORK\CODING\asyncgen-image
```

需要保留的功能来自以下模块：

| 功能 | 参考模块 | 保留策略 |
| --- | --- | --- |
| 图生图 | `fastdata/generator.py` | 保留核心请求、异步并发、轮询、下载逻辑，改为节点执行 |
| 文生图 | 当前无实现 | 新增能力，复用同一 API 配置、异步执行、轮询和下载框架 |
| 图片转 PNG | `fastdata/convert_png.py` | 保留 Pillow RGB PNG 转换逻辑，输出目录由 Output Folder 节点提供 |
| 图片转 JPG | 当前无实现 | 新增 Pillow RGB JPG 转换逻辑，输出目录由 Output Folder 节点提供 |
| 按参考图尺寸匹配 | `fastdata/resize_match.py` | 保留同名图片匹配、等比缩放、居中裁剪逻辑 |
| 尺寸缩放 | `fastdata/resize_to_1024.py` | 以旧固定尺寸脚本为参考，不保留固定尺寸形态，改为用户自定义宽高、RGB、输出格式 |
| Prompt 批量生成 | `fastdata/prompt_writer.py` | 保留批量 txt 生成逻辑，输出目录由 Output Folder 节点提供 |
| 配置保存 | `fastdata/config.py` | 保留 JSON 本地配置思路，调整为新项目结构 |

明确不保留：

- `fastdata/gui.py` 的 Tkinter 页面布局。
- 左侧导航 + 右侧表单页的旧交互模式。
- `sv-ttk` 主题方案。
- 旧 UI 中与 Tkinter 强绑定的按钮、进度条、线程回调写法。

## 推荐技术路线

采用：

```text
Python 3.11 + uv/.venv + NodeGraphQt + PySide6 + Pillow + aiohttp + JSON 本地配置 + PyInstaller onedir 打包
```

固定依赖：

```text
NodeGraphQt
PySide6
Pillow
aiohttp
```

开发与运行环境：

- Python 版本固定为 3.11 系列。
- 使用 `uv` 管理解释器、虚拟环境和锁文件。
- 项目虚拟环境使用 `.venv`。
- Qt 绑定固定使用 `PySide6`，项目内不混用 PyQt/PySide 其他绑定。
- 节点图主界面使用 `NodeGraphQt`。
- 图片处理使用 `Pillow`。
- 异步网络请求使用 `aiohttp`。
- 本地配置和工作流使用 JSON 文件保存。
- Windows 分发使用 PyInstaller `onedir` 模式。

当前环境基线：

```text
Python 3.11
NodeGraphQt 0.6.44
PySide6
Pillow
aiohttp
```

验证命令优先使用：

```powershell
uv run python -m compileall app.py fastdata
```

如果 Codex 沙箱下 `uv run ...` 因 uv cache 或 trampoline 权限失败，应说明是沙箱权限问题，并按授权方式重跑，不误判为项目环境缺失。

## UI 总体设计

第一版主界面采用节点图工作台，而不是传统表单页。

```text
FastData NodeGraph
├── 顶部工具栏
│   ├── 新建工作流
│   ├── 打开工作流
│   ├── 保存工作流
│   ├── 运行
│   ├── 停止
│   └── 设置
├── 左侧节点库
│   ├── 输入
│   ├── Prompt
│   ├── 生成
│   ├── 图片处理
│   └── 输出
├── 中间 NodeGraphQt 画布
├── 右侧属性面板
└── 底部状态 / 日志区域
```

审美方向：

- 默认采用深色主题，延续 NodeGraphQt 原生节点编辑器气质。
- 节点颜色克制，按类别轻微区分即可，不使用高饱和大面积色块。
- 连线使用细线和柔和颜色，选中态清晰但不过分刺眼。
- 右侧属性面板保持表单清晰，不堆叠过多边框。
- 字体优先使用 `Microsoft YaHei UI`。
- Windows 下启动时启用 DPI awareness，避免高 DPI 模糊。

第一版不做浅色/深色主题切换。主题方向以深色、简洁、低噪音为准，通过 Qt stylesheet、NodeGraphQt viewer/background 设置和节点颜色配置统一观感。

### 节点尺寸与内容显示

NodeGraphQt 画布支持整体缩放，用户可以通过画布缩放查看更大或更小的节点视图。

普通业务节点默认不设计为用户在画布中拖拽边缘自由缩放。NodeGraphQt 普通节点会根据节点标题、端口文本和嵌入控件自动计算最小尺寸；Backdrop 节点内置拖拽缩放手柄，但业务处理节点第一版不依赖这种交互。

业务节点尺寸策略：

- 节点标题保持短名称，例如 `Img2Img`、`Image To PNG`、`Resize Image`。
- 节点本体只展示端口、少量关键状态和必要的短控件。
- 长 Prompt、长路径、完整错误信息、复杂参数放在右侧属性面板或底部日志区，不直接塞进节点本体。
- 节点端口名使用短标签，必要时通过 tooltip 显示完整说明。
- 如果节点内容超过默认宽度，优先扩大节点默认最小宽度或减少节点内嵌文本，不采用让文本硬挤或遮挡端口的做法。
- 如后续确实需要用户手动调整业务节点大小，再实现自定义节点图形项或节点尺寸属性；第一版不做普通业务节点的拖拽缩放。

## 节点设计

节点设计以“少而清楚”为原则。第一版不做复杂 DAG 调度，只支持明确的数据流和手动运行。

核心端口模型：

- 输入节点负责提供被处理对象或文本。
- 输出节点负责提供落盘目录。
- 处理节点不在参数里隐藏输出路径，而是通过 `output_folder` 输入端口接收输出目录。
- `Output Folder` 是输出目录供应节点，不是统一的最后保存节点。
- 处理节点负责把结果写入收到的 `output_folder`，并输出结果文件列表或结果引用。
- 第一版底层函数仍可使用 `input_dir`、`output_dir` 参数，但 UI 节点层面必须通过连线表达输出目录来源。

### 输入类节点

#### Path Input 节点

用途：选择一个文件夹路径，可作为图片输入、参考图输入、目标图输入或普通文件输入。

参数：

- `folder_path`
- `path_role`
- `include_extensions`

输出：

- `folder_path`
- `images`
- `files`

第一版可以先只稳定输出 `folder_path`，由下游节点自己扫描图片；后续再扩展 `images` 和 `files` 的强类型数据。

#### Prompt Input 节点

用途：输入或保存一段 Prompt 文本。

参数：

- `prompt_text`

输出：

- `prompt`

#### Output Folder 节点

用途：提供输出目录，并允许在系统文件管理器中打开。

参数：

- `folder_path`

输出：

- `output_folder`

第一版中所有需要写文件的处理节点，都应通过端口连接到 `Output Folder` 节点。

### Prompt 类节点

#### Prompt Batch Generate 节点

用途：将同一段 Prompt 批量保存为 txt 文件。

输入：

- `prompt`
- `output_folder`

参数：

- `count`
- `filename_prefix`

输出：

- `prompt_files`

对应参考功能：`prompt_writer.generate_prompt_files(...)`

### 生成类节点

#### Img2Img 节点

用途：调用 GrsAI nano-banana 接口进行异步图生图。

输入：

- `images` 或 `folder_path`
- `prompt`
- `output_folder`

参数：

- `api_key`
- `base_url`
- `model`
- `aspect_ratio`
- `image_size`
- `concurrency`
- `poll_interval`
- `max_retries`
- `only_missing`

输出：

- `generated_images`

对应参考功能：`generator.AsyncImg2Img`

#### Text2Img 节点

用途：根据 Prompt 调用 GrsAI 接口进行文生图。

输入：

- `prompt`
- `output_folder`

参数：

- `api_key`
- `base_url`
- `model`
- `aspect_ratio`
- `image_size`
- `count`
- `concurrency`
- `poll_interval`
- `max_retries`

输出：

- `generated_images`

对应参考功能：当前无实现，后续新增。

模型默认值：

```text
nano-banana-2
```

可选模型：

```text
nano-banana
nano-banana-fast
nano-banana-2
nano-banana-2-cl
nano-banana-2-4k-cl
nano-banana-pro
nano-banana-pro-cl
nano-banana-pro-vip
nano-banana-pro-4k-vip
```

比例选项：

```text
auto
1:1
16:9
9:16
4:3
3:4
3:2
2:3
5:4
4:5
21:9
1:4
4:1
1:8
8:1
```

分辨率选项：

```text
1K
2K
4K
```

### 图片处理类节点

#### Image To PNG 节点

用途：将输入目录图片转换为 RGB PNG。

输入：

- `images` 或 `folder_path`
- `output_folder`

参数：

- `overwrite`

输出：

- `png_images`

对应参考功能：`convert_png.convert_images_to_png(...)`

#### Image To JPG 节点

用途：将输入目录图片转换为 RGB JPG。

输入：

- `images` 或 `folder_path`
- `output_folder`

参数：

- `quality`
- `overwrite`

输出：

- `jpg_images`

对应参考功能：当前无实现，后续新增。

#### Resize Match 节点

用途：按同名参考图分辨率，将目标图等比缩放并居中裁剪。

输入：

- `reference_images` 或 `reference_folder_path`
- `target_images` 或 `target_folder_path`
- `output_folder`

参数：

- `overwrite`

输出：

- `matched_images`

对应参考功能：`resize_match.resize_folder_to_reference(...)`

处理方式第一版固定为：

```text
等比缩放 + 居中裁剪
```

#### Resize Image 节点

用途：按用户定义宽高缩放图片，并输出为指定格式。

输入：

- `images` 或 `folder_path`
- `output_folder`

参数：

- `width`
- `height`
- `output_format`
- `resize_mode`
- `overwrite`

输出：

- `resized_images`

`output_format` 第一版支持：

```text
png
jpg
keep
```

`resize_mode` 第一版支持：

```text
stretch
fit
fill_crop
```

对应参考功能：`resize_to_1024.resize_folder_to_1024_rgb_png(...)`，但需要从固定 1024 改造为自定义宽高。

## 默认工作流

第一版启动时应提供几个预设工作流模板，减少用户从空画布开始的压力。

### 图生图工作流

```text
Path Input    -> Img2Img
Prompt Input  -> Img2Img
Output Folder -> Img2Img
```

### 文生图工作流

```text
Prompt Input  -> Text2Img
Output Folder -> Text2Img
```

### PNG 转换工作流

```text
Path Input    -> Image To PNG
Output Folder -> Image To PNG
```

### JPG 转换工作流

```text
Path Input    -> Image To JPG
Output Folder -> Image To JPG
```

### 尺寸匹配工作流

```text
Path Input    -> Resize Match  # reference
Path Input    -> Resize Match  # target
Output Folder -> Resize Match
```

### 尺寸缩放工作流

```text
Path Input    -> Resize Image
Output Folder -> Resize Image
```

### Prompt 批量生成工作流

```text
Prompt Input  -> Prompt Batch Generate
Output Folder -> Prompt Batch Generate
```

## 执行模型

第一版采用保守执行模型：

- 用户点击工具栏“运行”后执行当前选中的处理节点，或执行当前工作流中被标记为主任务的处理节点。
- 暂不实现复杂自动调度、缓存失效、并行 DAG 执行。
- 每个业务节点内部可以使用现有函数的批处理能力。
- 长耗时任务必须放到后台线程或 Qt worker 中执行，不能阻塞 Qt 主线程。
- 图生图和文生图节点在 worker 中运行 asyncio 事件循环。
- 执行期间禁用当前节点的重复运行按钮，并允许停止图生图/文生图任务。

状态反馈：

- 节点本体显示运行中、成功、失败三种状态。
- 底部日志显示简短运行信息。
- 错误用对话框提示，同时写入底部日志。
- API Key 不得明文输出到日志。
- 错误信息不得包含完整 Authorization Header。

## 配置文件设计

配置文件保存在项目目录：

```text
config/config.json
```

配置文件可能包含 API Key，必须加入 `.gitignore`，不得提交。

推荐结构：

```json
{
  "api_key": "",
  "base_url": "https://grsai.dakka.com.cn",
  "model": "nano-banana-2",
  "aspect_ratio": "auto",
  "image_size": "2K",
  "concurrency": 5,
  "poll_interval": 2,
  "max_retries": 300,
  "prompt": "",
  "theme": "dark",
  "paths": {
    "generation_input": "data/image_generation/input_images",
    "generation_output": "data/image_generation/output_images",
    "convert_input": "data/png_conversion/input_images",
    "convert_output": "data/png_conversion/output_images",
    "resize_reference": "data/resize_match/reference_images",
    "resize_target": "data/resize_match/target_images",
    "resize_match_output": "data/resize_match/output_images",
    "resize_input": "data/resize/input_images",
    "resize_output": "data/resize/output_images",
    "prompt_output": "data/prompt_generation/output_prompts"
  }
}
```

API Key 安全原则：

- 不写死在代码中。
- 不提交到 Git。
- 配置面板使用密码输入框。
- 日志中只允许显示脱敏形式，例如 `sk-...abcd`。
- 允许后续增加环境变量读取，但第一版以本地配置为主。

## 推荐项目结构

```text
fastdata/
├── fastdata/
│   ├── __init__.py
│   ├── config.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   ├── convert_png.py
│   │   ├── resize_match.py
│   │   ├── resize_image.py
│   │   └── prompt_writer.py
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py
│   │   ├── graph.py
│   │   ├── theme.py
│   │   ├── workers.py
│   │   └── property_panel.py
│   └── nodes/
│       ├── __init__.py
│       ├── base.py
│       ├── input_nodes.py
│       ├── prompt_nodes.py
│       ├── generation_nodes.py
│       ├── image_nodes.py
│       └── output_nodes.py
├── config/
│   └── .gitkeep
├── data/
│   ├── image_generation/
│   ├── png_conversion/
│   ├── resize_match/
│   ├── resize/
│   └── prompt_generation/
├── workflows/
│   └── .gitkeep
├── app.py
├── pyproject.toml
├── README.md
└── DEV_SPEC.md
```

## MVP 范围

### MVP 必做

1. NodeGraphQt 主窗口。
2. 深色主题和基础节点视觉样式。
3. 节点库、画布、属性面板、底部状态区域。
4. 本地 JSON 配置读取与保存。
5. Path Input、Prompt Input、Output Folder、Img2Img、Text2Img、Image To PNG、Image To JPG、Resize Match、Resize Image、Prompt Batch Generate 节点。
6. 预设工作流模板。
7. 后台执行，避免 UI 卡死。
8. 图生图和文生图支持停止。
9. 工作流保存和打开。
10. PyInstaller onedir 打包。

### MVP 暂不做

1. 云端任务历史。
2. 用户登录。
3. 插件市场。
4. 多服务商抽象。
5. 自动更新。
6. 拖拽批量导入并复制文件。
7. 复杂 DAG 自动调度。
8. 节点执行缓存。
9. 多语言切换。
10. 数据库。

## 开发计划

### Phase 1：项目骨架与依赖验证

目标：确认 NodeGraphQt 能在当前 Python/Qt 环境中启动。

实现内容：

- 创建 `app.py`。
- 创建 `fastdata/ui/main_window.py`。
- 安装并验证 NodeGraphQt 与选定 Qt 绑定。
- 启动一个空 NodeGraphQt 画布。
- 设置窗口标题、默认尺寸、DPI awareness、基础字体。

验证标准：

- `uv run python app.py` 能打开空画布窗口。
- 关闭窗口无异常。
- `uv run python -m compileall app.py fastdata` 通过。

### Phase 2：深色主题与主工作台

目标：建立符合审美方向的主界面。

实现内容：

- 顶部工具栏。
- 左侧节点库。
- 中间 NodeGraphQt 画布。
- 右侧属性面板。
- 底部状态/日志区域。
- 深色画布背景、节点颜色、连线样式。

验证标准：

- 界面默认为深色。
- 节点、连线、属性面板清晰可读。
- 高 DPI 下字体不模糊。

### Phase 3：配置与路径系统

目标：迁移参考项目的配置能力。

实现内容：

- 实现 `fastdata/config.py`。
- 支持读取、合并默认配置、保存 `config/config.json`。
- 配置面板可编辑 API Key、base_url、模型、比例、分辨率、并发数、轮询间隔、最大轮询次数。
- 路径字段可选择文件夹并保存。

验证标准：

- 首次启动无配置文件也能使用默认值。
- 保存配置后重启能恢复。
- API Key 不在日志中明文出现。

### Phase 4：核心功能迁移

目标：把参考项目业务逻辑迁入 `fastdata/core/`，并去除 UI 依赖。

实现内容：

- 迁移 `generator.py`。
- 迁移 `convert_png.py`。
- 迁移 `resize_match.py`。
- 将 `resize_to_1024.py` 改造为 `resize_image.py`。
- 迁移 `prompt_writer.py`。
- 统一函数签名，保留 `progress_callback` 或改为事件回调。

推荐核心函数：

```python
convert_images_to_png(input_dir, output_dir, progress_callback=None)
convert_images_to_jpg(input_dir, output_dir, quality=95, overwrite=False, progress_callback=None)
resize_folder_to_reference(reference_dir, target_dir, output_dir, overwrite=False, progress_callback=None)
resize_images(input_dir, output_dir, width, height, output_format="png", resize_mode="fill_crop", overwrite=False, progress_callback=None)
generate_prompt_files(prompt, count, output_dir, filename_prefix="", progress_callback=None)
generate_images_async(config, input_dir, output_dir, prompt, only_missing=True, progress_callback=None, stop_token=None)
generate_text_to_images_async(config, output_dir, prompt, count=1, progress_callback=None, stop_token=None)
```

验证标准：

- 每个核心函数可脱离 UI 单独调用。
- 本地图片处理函数能在测试目录中产生正确输出。
- 图生图和文生图在缺少 API Key 时给出明确错误。

### Phase 5：节点类型实现

目标：让节点承载参数和连接关系。

实现内容：

- 实现基础节点类。
- 实现输入类节点。
- 实现 Prompt 类节点。
- 实现生成类节点。
- 实现图片处理类节点。
- 实现输出类节点。
- 选中节点时右侧属性面板显示对应参数。

验证标准：

- 可从节点库创建节点。
- 节点之间可连线。
- 选中节点后能编辑参数。
- 参数变化能保存到节点实例。

### Phase 6：节点执行

目标：从节点图触发真实功能。

实现内容：

- 实现节点输入解析。
- 实现“运行当前节点”。
- 实现“运行到当前节点”的最小依赖执行。
- 使用 Qt worker 或后台线程执行耗时任务。
- 将进度回写到节点状态和底部日志。
- 图生图和文生图节点支持停止。

验证标准：

- PNG 转换节点可真实输出文件。
- JPG 转换节点可真实输出文件。
- 尺寸匹配节点可真实输出文件。
- Resize Image 节点可按自定义宽高真实输出文件。
- Prompt Batch Generate 可真实输出 txt。
- 图生图和文生图节点不阻塞 UI。

### Phase 7：工作流保存与模板

目标：让用户能复用节点流程。

实现内容：

- 保存当前工作流到 `workflows/*.json`。
- 打开已有工作流。
- 提供默认模板：图生图、文生图、PNG 转换、JPG 转换、尺寸匹配、尺寸缩放、Prompt 批量生成。
- 启动时可选择模板或打开上次工作流。

验证标准：

- 保存后重启能恢复节点、连线、参数。
- 模板能一键加载。
- 加载后可直接编辑和运行。

### Phase 8：打包整理

目标：形成可分发的 Windows 桌面工具。

实现内容：

- 检查 PyInstaller onedir 打包。
- 确认 NodeGraphQt、Qt 绑定、Pillow、aiohttp 能被正确收集。
- 确认 `config/`、`data/`、`workflows/` 目录创建逻辑。
- 确认中文路径、中文 Prompt 正常。

验证标准：

- `uv run python -m compileall app.py fastdata` 通过。
- `uv run python app.py` 能启动并运行本地功能。
- PyInstaller onedir 产物能启动。

## 代码编写计划

代码编写按 A/B/C/D 四个大阶段推进。每个子任务都必须能独立验证，避免一次性混合 UI、节点、业务逻辑和打包问题。

当前阶段状态：

```text
[x] A：项目基础与主窗口骨架
[x] B：核心功能与配置层
[ ] C：节点系统与执行流程
[ ] D：工作流、打包与验收
```

### [x] A：项目基础与主窗口骨架

目标：建立稳定可运行的桌面应用外壳，让 NodeGraphQt 画布、主窗口布局和基础目录结构先跑起来。

#### [x] A-1：整理项目结构

实现内容：

- 创建 `app.py` 作为正式入口。
- 创建 `fastdata/` 包。
- 创建 `fastdata/core/`、`fastdata/ui/`、`fastdata/nodes/`。
- 创建 `config/`、`data/`、`workflows/` 目录。
- 保留 `demo/` 作为技术验证样例，不作为正式入口。

验证标准：

- `uv run python -m compileall app.py fastdata` 通过。
- 目录结构与 DEV_SPEC 推荐结构一致。

#### [x] A-2：实现 Qt 主窗口

实现内容：

- 创建 `fastdata/ui/main_window.py`。
- 使用 PySide6 创建主窗口。
- 设置窗口标题、默认尺寸、最小尺寸。
- Windows 下启用 DPI awareness。
- 使用 `Microsoft YaHei UI` 作为默认字体。

验证标准：

- `uv run python app.py` 能打开空主窗口。
- 关闭窗口无异常。
- 高 DPI 下界面不明显模糊。

#### [x] A-3：嵌入 NodeGraphQt 画布

实现内容：

- 创建 `fastdata/ui/graph.py`。
- 在主窗口中央嵌入 NodeGraphQt 画布。
- 注册一个最小测试节点。
- 创建并显示两个测试节点和一条连线。

验证标准：

- `uv run python app.py` 能看到 NodeGraphQt 画布。
- 测试节点可选中、拖动、连线。
- 画布缩放和平移正常。

#### [x] A-4：搭建主界面区域

实现内容：

- 顶部工具栏：新建、打开、保存、运行、停止、设置。
- 左侧节点库区域。
- 中间 NodeGraphQt 画布。
- 右侧属性面板占位。
- 底部状态/日志区域。

验证标准：

- 主窗口各区域布局稳定。
- 窗口缩放时画布扩展，侧栏和状态栏尺寸保持可用。

#### [x] A-5：实现深色主题基础样式

实现内容：

- 创建 `fastdata/ui/theme.py`。
- 设置主窗口、侧栏、属性面板、日志区基础深色样式。
- 设置 NodeGraphQt 画布背景、节点基础颜色和连线观感。

验证标准：

- 界面默认为深色。
- 节点、端口、连线、文字清晰可读。

### [x] B：核心功能与配置层

目标：先让业务逻辑脱离 UI 独立可运行，再让节点层调用这些稳定函数。

#### [x] B-1：实现配置模块

实现内容：

- 创建 `fastdata/config.py`。
- 实现 `get_app_dir()`、`get_config_path()`、`get_default_config()`。
- 实现 `load_config()`、`save_config()`。
- 支持默认配置与用户配置合并。
- API Key 写入 `config/config.json`，不得硬编码。

验证标准：

- 无配置文件时能返回默认配置。
- 保存后能重新读取。
- 配置文件使用 UTF-8 JSON。
- 日志不输出完整 API Key。

#### [x] B-2：迁移图片转 PNG

实现内容：

- 创建 `fastdata/core/convert_png.py`。
- 从参考项目迁移 RGB PNG 转换逻辑。
- 支持 `input_dir`、`output_dir`、`overwrite`、`progress_callback`。

验证标准：

- 给定测试图片目录，可输出 3 通道 PNG。
- 输出目录不存在时自动创建。
- 透明通道图片转换后为 RGB。

#### [x] B-3：新增图片转 JPG

实现内容：

- 创建 `fastdata/core/convert_jpg.py` 或与转换模块合并。
- 使用 Pillow 将图片转换为 RGB JPG。
- 支持 `quality`、`overwrite`、`progress_callback`。

验证标准：

- 给定测试图片目录，可输出 3 通道 JPG。
- RGBA 图片可正确转为 RGB JPG。
- quality 参数生效。

#### [x] B-4：迁移尺寸匹配

实现内容：

- 创建 `fastdata/core/resize_match.py`。
- 从参考项目迁移同名图片匹配逻辑。
- 保留等比缩放 + 居中裁剪。
- 支持 `overwrite`、`progress_callback`。

验证标准：

- 参考目录和目标目录存在同名图片时，可输出与参考图同尺寸的目标图。
- 无同名图片时给出明确结果。

#### [x] B-5：实现自定义尺寸缩放

实现内容：

- 创建 `fastdata/core/resize_image.py`。
- 将旧固定 1024 逻辑改造为自定义 `width`、`height`。
- 支持 `output_format`: `png`、`jpg`、`keep`。
- 支持 `resize_mode`: `stretch`、`fit`、`fill_crop`。
- 统一输出 RGB。

验证标准：

- 可输出用户指定宽高。
- 三种 resize mode 行为清晰可验证。
- PNG 和 JPG 输出均可用。

#### [x] B-6：迁移 Prompt 批量生成

实现内容：

- 创建 `fastdata/core/prompt_writer.py`。
- 迁移批量 txt 生成逻辑。
- 支持 `prompt`、`count`、`output_dir`、`filename_prefix`。

验证标准：

- 可生成指定数量 txt。
- 文件名从 1 开始递增。
- 中文 Prompt 保存正常。

#### [x] B-7：迁移图生图

实现内容：

- 创建 `fastdata/core/generator.py`。
- 迁移 `AsyncImg2Img` 核心逻辑。
- 保留异步提交、轮询、下载、并发控制。
- 支持 `stop_token` 或等价停止机制。
- 不直接依赖 UI。

验证标准：

- 缺少 API Key 时给出明确错误。
- 输入目录为空时给出明确结果。
- `only_missing=True` 时，输出目录已有同名图片的输入图会跳过，不提交 API 任务。
- 不在日志中输出完整 Authorization Header。

#### [x] B-8：新增文生图

实现内容：

- 在 `fastdata/core/generator.py` 中实现 `generate_text_to_images_async(...)`。
- 复用 API Key、base_url、model、aspect_ratio、image_size、poll_interval、max_retries。
- 支持 `count` 和输出目录。

验证标准：

- 缺少 API Key 时给出明确错误。
- 参数构造与图生图区分清楚。
- 下载结果保存到输出目录。

### [ ] C：节点系统与执行流程

目标：把核心功能映射为节点，并让节点之间通过端口传递路径、Prompt 和输出目录。

#### [x] C-1：实现基础节点约定

实现内容：

- 创建 `fastdata/nodes/base.py`。
- 定义节点通用颜色、状态、短标题、端口命名规范。
- 定义节点运行状态：idle、running、success、error。
- 保证长文本不直接塞进节点本体。

验证标准：

- 新节点继承基础类后能注册到 NodeGraphQt。
- 节点状态变化可在画布上体现。

#### [x] C-2：实现输入输出节点

实现内容：

- 创建 `Path Input` 节点。
- 创建 `Prompt Input` 节点。
- 创建 `Output Folder` 节点。
- 输出端口分别为 `folder_path`、`prompt`、`output_folder`。

验证标准：

- 三类节点可从节点库创建。
- 节点参数可在右侧属性面板编辑。
- 参数变化能保存到节点数据。

#### [ ] C-3：实现生成节点

实现内容：

- 创建 `Img2Img` 节点。
- 创建 `Text2Img` 节点。
- 输入端口按 DEV_SPEC 定义接收 `folder_path/images`、`prompt`、`output_folder`。
- 参数优先使用节点属性，缺省值从全局配置读取。

验证标准：

- 节点端口可正确连接。
- 缺少必要输入时阻止运行并提示。
- 可调用核心生成函数。

#### [ ] C-4：实现图片处理节点

实现内容：

- 创建 `Image To PNG` 节点。
- 创建 `Image To JPG` 节点。
- 创建 `Resize Match` 节点。
- 创建 `Resize Image` 节点。
- 所有写文件节点都通过 `output_folder` 输入端口获取输出路径。

验证标准：

- 节点端口可正确连接。
- 缺少 `output_folder` 时阻止运行并提示。
- 节点能调用对应核心函数。

#### [ ] C-5：实现 Prompt Batch Generate 节点

实现内容：

- 创建 `Prompt Batch Generate` 节点。
- 输入端口接收 `prompt` 和 `output_folder`。
- 参数支持 `count`、`filename_prefix`。

验证标准：

- 可通过节点生成 txt 文件。
- 缺少 Prompt 或输出目录时给出明确提示。

#### [ ] C-6：实现属性面板

实现内容：

- 创建 `fastdata/ui/property_panel.py`。
- 选中节点时展示对应参数。
- 支持路径选择、文本输入、数字输入、下拉框、复选框。
- 长 Prompt 在属性面板中编辑。

验证标准：

- 选中不同节点时属性面板能切换。
- 修改参数后节点数据同步更新。
- 长路径和长 Prompt 不导致节点本体截断。

#### [ ] C-7：实现节点执行器

实现内容：

- 创建 `fastdata/ui/workers.py`。
- 实现后台 worker 或线程执行。
- 实现节点输入解析。
- 实现运行当前处理节点。
- 将进度和结果回写到节点状态和底部日志。
- 支持图生图、文生图停止。

验证标准：

- 长任务不阻塞 UI。
- 成功、失败、停止状态可见。
- 错误弹窗和日志信息清晰。

### [ ] D：工作流、打包与验收

目标：让用户能保存、复用和分发这个工具。

#### [ ] D-1：实现工作流保存与打开

实现内容：

- 保存当前节点、连线、节点参数到 `workflows/*.json`。
- 打开已有工作流并恢复画布。
- 启动时可打开上次工作流。

验证标准：

- 保存后重启能恢复节点布局、连线和参数。
- 打开损坏工作流时给出明确错误。

#### [ ] D-2：实现默认模板

实现内容：

- 图生图模板。
- 文生图模板。
- PNG 转换模板。
- JPG 转换模板。
- 尺寸匹配模板。
- 尺寸缩放模板。
- Prompt 批量生成模板。

验证标准：

- 模板可一键加载。
- 模板节点连接符合端口模型。
- 加载后可直接编辑参数并运行。

#### [ ] D-3：完善状态、日志和错误处理

实现内容：

- 底部日志显示开始、进度、完成、失败。
- 错误弹窗显示用户可理解的信息。
- API Key、Authorization Header 永不完整输出。
- 节点显示成功/失败状态。

验证标准：

- 常见错误路径都有明确提示。
- 日志能辅助用户定位输入缺失、输出路径错误、API 配置错误。

#### [ ] D-4：全功能本地验收

实现内容：

- 准备小型测试数据目录。
- 验证 PNG 转换。
- 验证 JPG 转换。
- 验证尺寸匹配。
- 验证自定义尺寸缩放。
- 验证 Prompt 批量生成。
- 验证图生图和文生图参数校验。

验证标准：

- `uv run python -m compileall app.py fastdata` 通过。
- `uv run python app.py` 可启动。
- 本地功能均能真实输出文件。
- 网络功能缺少 API Key 时提示明确。

#### [ ] D-5：PyInstaller 打包

实现内容：

- 添加或整理 PyInstaller 打包命令。
- 使用 `onedir` 模式。
- 确认 NodeGraphQt、PySide6、Pillow、aiohttp 资源被收集。
- 确认 `config/`、`data/`、`workflows/` 目录在打包产物旁可创建。

验证标准：

- 打包成功。
- `dist/FastData/FastData.exe` 可启动。
- 打包产物可运行本地图片处理功能。

#### [ ] D-6：交付前清理

实现内容：

- 更新 README。
- 确认 `.gitignore` 忽略 `.venv`、`config/config.json`、`data/` 输出文件、`dist/`、`build/`。
- 确认 DEV_SPEC 与实际实现一致。
- 删除或标记仅用于验证的临时代码。

验证标准：

- 工作区没有误提交的 API Key 或生成图片。
- 文档能指导用户启动和运行。
- DEV_SPEC 不与实际代码冲突。

## 成功标准

第一版成功标准：

- 用户可以打开一个深色主题的 NodeGraphQt 桌面应用。
- 用户可以用节点搭出或加载默认工作流。
- 参考项目中的核心功能可通过节点运行，并新增文生图、JPG 转换、自定义尺寸缩放节点。
- 旧 Tkinter UI 不再作为产品界面存在。
- 配置、路径、Prompt、工作流可保存。
- 长任务运行时 UI 不冻结。
- API Key 安全处理，不进入代码和日志。

## 当前推荐结论

当前项目推荐路线是：

```text
保留 asyncgen-image 的核心功能
新增文生图、JPG 转换、自定义尺寸缩放能力
废弃 asyncgen-image 的 Tkinter UI
使用 NodeGraphQt 重做桌面端节点工作台
处理节点通过 Output Folder 端口接收输出目录
默认深色主题
用属性面板承载节点参数
用后台 worker 执行耗时任务
用 JSON 保存配置和工作流
用 PyInstaller onedir 分发
```

这条路线比继续堆叠传统表单页更符合节点式图片工作流的审美和使用方式，同时能复用已经验证过的 Python 业务逻辑，并让输出路径在画布连线中保持可见。
