# NodeGraph Demo

这个目录只用于验证当前环境里的 `NodeGraphQt + PySide6 + Python 3.14` 能不能先跑起来。

## 当前已知问题

`NodeGraphQt 0.6.44` 仍然在导入时使用 `distutils.version.LooseVersion`，而 Python 3.14 已移除 `distutils`。

所以这个 demo 在启动前做了一个很小的兼容 shim，仅用于验证环境可用性，不代表后续正式项目结构。

## 运行

```powershell
uv run python demo/nodegraph_demo.py
```

如果能看到一个 NodeGraphQt 窗口，里面有 `Input Images`、`Prompt Text`、`Async Generate` 三个节点并已经连好线，说明基础组合可以继续推进。
