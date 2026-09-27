# 星湾 · Unreal Engine 5

星湾是一个虚构街区。主线为 **UE5 Windows 独立游戏**；浏览器原型保留作玩法与本地 AI 协议参考。当前已进入第三人称可玩原型阶段，距离完整开放世界仍有明显差距。

## 焰冕动态角色 · 2026-09-27

新增独立试炼地图 `/Game/Starbay/Ember_v04/L_EmberArena` 与 `BP_EmberHero`。原生输入测试通过走路 300 cm/s、冲刺 600 cm/s、空格跳跃和 Q 施法；动作结束后恢复并支持再次施放。火星由动画通知驱动，不依赖 Python 运行时。详细操作、架构和局限见 [动态试玩说明](Design/焰冕行者_动态试玩.md)，最终独立包验证见 `Validation/ember_delivery.json`。这次没有把浏览器 AI、任务或 NPC 迁入 UE。

## 街区原有状态 · 2026-09-26

本机使用 UE **5.6.1**，已安装到 `D:\Program Files\Epic Games\UE_5.6`。

| 项目 | 已取得的实际证据 | 边界 |
|---|---|---|
| 场景 | 7 个 FBX 已导入并完成轴向、米/厘米校准；`Content/Starbay/Maps/L_Starbay.umap` 已实际保存并重新打开 | 场景仍以两大片合并静态网格为主 |
| 官方角色 | 已复制并校验 246 个 Third Person 模板及共享资源文件，共 135,456,610 字节，约 135 MB；地图已配置官方 GameMode | 使用 Epic 模板角色，尚未迁移原型中的四类居民 |
| 编辑器碰撞 | 当前地图结构检查、77 条地面/通道射线及障碍对照通过，报告中无检查问题 | 稀疏射线不能证明完整角色胶囊、全部路线或相机通行 |
| 原生 PIE | 真实角色出生、原生移动与跳跃通过；沿测试方向移动 317.743 cm，跳跃最大上升 127.53 cm，并稳定落地 | 使用角色输入/跳跃接口驱动，没有传送；未完成键盘映射、完整路线与视觉步态人工验收 |
| 独立程序 | 一次使用引擎预编译 Development 目标的真实 `BuildCookRun` 返回退出码 0；生成的 Windows `.exe` 已直接打开 | 独立版完整线路、键盘操作、稳定性和性能尚未全面验收 |
| 材质修正 | 已复制并调整叶片/发光材质，在地图组件上设置覆盖，保留原网格与材质 | UE 原生截图已检查叶片背面和灯串效果；尚未进行性能基准 |

**NPC 自主活动、Qwen 对话与目的地决策、任务、昼夜、存档尚未迁移到 UE。** 原浏览器版的这些功能不能算作独立游戏已实现。任意玩家上传场景自动生成可玩世界仍是后续方向。

当前采用 DX12、SM6 与 Lumen。实际运行中出现了巨型非 Nanite 网格导致的 **Virtual Shadow Map overflow**；目前配置已改为常规阴影。下一步需拆分场景、分离装饰碰撞，再评估 Nanite 与虚拟阴影，而不是仅放大缓存。最终修订 EXE 已独立加载，启动视图未再出现该阴影警告；稳定帧率仍待测量。

`Preview/UE5_Courtyard_v02.png` 是 UE 编辑器原生截图，`Preview/UE5_Windows_v02.png` 是最终独立游戏的原生 F9 截图。

风栖茶庭、喷泉水池、木廊、夜市、货品、灯串和新植被已进入场景。`Preview/茶庭_Blender资产预览.png` 仍是 **Blender 资产预览，不是 UE 实机截图**。

## 打开、验证与打包

以下命令在 `星湾UE5` 目录执行。已有地图时直接正常打开，不再运行首次导入：

```powershell
& .\Tools\Open-Starbay.ps1
```

启动脚本只自动选择 `.uproject` 指定的引擎版本；必要时传入 `-EngineRoot 'D:\Program Files\Epic Games\UE_5.6'`。DDC、Zen 和临时目录默认位于引擎所在盘的 `UECache`，本机即 `D:\UECache`，也可用 `-CacheRoot` 指定。路径与缺失的标准 CPU 环境变量仅作用于启动进程，不修改系统全局环境或注册表。

在已打开的编辑器 Python 环境执行对应脚本：

- `Tools/validate_scene.py`：只读检查当前地图，不切图、不保存、不启动 PIE；写入 `Saved/scene_validation_report.json`。
- `Tools/smoke_play.py`：启动自身管理的真实 PIE，检查出生、短距离原生移动、跳跃和稳定落地，然后结束该测试会话；写入 `Saved/native_play_smoke.json`。不代替完整路线、手动键盘或性能验收。
- `Tools/refine_materials.py`：备份地图文件，在全新的 `Art_v02` 目录创建材质副本并保存地图覆盖。已执行过的目标会被保护，不能反复重跑覆盖。

后续手动验收遵循 [首次步行验收路线](Design/首次步行验收.md)。源 FBX 检查发现旧导航线穿过树、入口柱和单车；不能直接把浏览器导航图当作 UE 原生导航。

打包使用：

```powershell
& .\Tools\Package-Starbay.ps1
```

默认在 `Builds` 下创建唯一输出目录，也可通过 `-OutputDirectory` 指定**空目录**。脚本使用已安装引擎的预编译 Windows Development 目标，跳过 C++ 编译；执行 cook、stage、pak/IoStore、package 和 archive，并在 `Saved/package-*.json`、`.log` 中记录实际退出码及 exe 是否存在。打包成功后仍需单独运行生成的游戏。

本机未安装可用 Windows SDK / Visual Studio C++ 工具链，Turnkey 的 SDK 检查显示无有效 SDK，**但上述 Blueprint 预编译路线已经实际打包成功**。当前不因此补装工具链。以后增加 C++ 或需要重新编译的插件时，再准备兼容 SDK 与 MSVC；不要通过随意禁用默认插件来改变预编译目标集合。

发布版本为 [ue5-playable-v0.2.0](https://github.com/hy-8/starbay-ai-world/releases/tag/ue5-playable-v0.2.0)，最终修订版位于 `../星湾发布/UE5-v0.2.0/Windows/StarbayUE5.exe`。已重新打包并直接运行，使用 Enhanced Input 开发命令检查前进、柱子碰撞与起跳落地；物理键盘长按和全部路线仍待完整验收。操作见 [试玩说明](Design/试玩说明_v0.2.0.md)，证据见 `Validation/windows_package.json` 与 `windows_runtime.json`。

## 历史导入结果与重导保护

首次导入已完成模型导入、校准、GameMode 设置和地图保存，但脚本末尾曾使用错误的 Python 保活类名，导致 `Saved/scene_import_report.json` 的历史状态保留为 `failed`。正确导出名是 `unreal.EditorPythonScripting`。之后修正调用、正常重开已保存地图，并通过独立场景检查与 PIE 测试；没有为消除历史错误而重导或覆盖地图。

因此，当前状态应结合已存地图、`scene_validation_report.json` 与 `native_play_smoke.json` 判断。历史失败报告不改写成成功；新的首次导入流程仍须检查其实际完成状态。

仅在**没有既有地图和导入资产的新工程或受保护的副本**中，才执行首次流程：

```powershell
python Tools/install_third_person.py --engine-root 'D:\Program Files\Epic Games\UE_5.6'
& .\Tools\Open-Starbay.ps1 -ImportScene
```

模板脚本复制官方 ThirdPerson、Characters、Input、LevelPrototyping 资源并加入模板输入配置，先检查全部目标冲突，不覆盖同名文件；记录位于 `Saved/template_import_report.json`。这些资源受 Epic 许可约束，见 [第三方说明](THIRD_PARTY_NOTICES.md)。

场景导入先检查未保存地图、既有目标地图、整个导入目录、必需模型及重复名称，以及 FBX/PBR 源文件和校验和。创建地图前还会再次检查未保存地图，因为 Unreal 的 `new_level()` 会关闭当前地图且不保存。脚本不代替使用者保存既有改动，也不自动清理失败导入的部分结果。重试优先使用工程副本和新的 `CONTENT` 目录；若需新地图，还要同步 `MAP`、地图配置及启动脚本的存在性检查路径。

2026-09-22 的 Epic 登录后安装失败源于自动化子进程缺少标准 CPU 环境变量；`Tools/Start-Epic.ps1` 使用官方 EOS 入口并仅补齐子进程环境。引擎现已安装，正常继续开发不需要再次运行等待安装的 `continue_after_install.py`。

## 重新生成资产

以下操作使用独立后台 Blender。FBX 导出脚本拒绝在交互式 Blender 中运行，避免清空正在编辑的场景。

仅在需要重新制作增量模型时运行建模命令。先保护游戏目录中的 `星湾街区_第六版场景.blend`、`assets/星湾_第六版增量场景.blend` 及增量资产的手工修改；**建模脚本仍会更新这些生成文件，FBX 的防覆盖保护不涵盖这一步**。

```powershell
$taskBlender = 'D:\tools\Blender\blender-4.5.9-windows-x64\blender.exe'
& $taskBlender --background --factory-startup --python '..\星湾街区_3D探索\build_detail_v6.py'
```

已有交付包含 FBX，默认导出会主动停止。指定全新候选目录，不覆盖已交付文件：

```powershell
$taskBlender = 'D:\tools\Blender\blender-4.5.9-windows-x64\blender.exe'
$taskAssetVersion = Join-Path $PWD ('SourceAssets_candidates\' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
& $taskBlender --background --factory-startup --python 'Tools\export_assets.py' -- --output-dir $taskAssetVersion
```

目录已有任意 FBX 或 `asset_manifest.json` 时仍会拒绝执行。只有无 FBX 和清单的新工程才可省略 `--output-dir`，首次输出到 `SourceAssets`。导出只读取两个 GLB，不修改原始 `.blend` 或 GLB。

**`--output-dir` 仅改变 FBX 导出位置。** 验证、材质获取和 UE 导入脚本仍读取工程的 `SourceAssets`。采用候选版本前，在工程副本中完整备份旧目录，再以新目录作为该副本的 `SourceAssets`；保留原 `Materials` 或重新获取，不混用旧、新模型与清单。切换完成后运行：

```powershell
& $taskBlender --background --factory-startup --python 'Tools\verify_assets.py'
python Tools/fetch_materials.py
```

最后一项需要 Python `requests`，从 Poly Haven 获取两组 1K CC0 PBR 材质并核对 MD5、记录 SHA-256；已有完整材质时可跳过。导入对 DirectX 法线贴图使用 Normal Map 压缩并关闭 sRGB，粗糙度使用线性数据。

`preview_assets.py` 读取游戏目录的第六版 `.blend`，更新 `Preview` 中的 Blender 预览；它不是 FBX 回读或 UE 渲染验证。旧 `星湾街区.blend` 保持不动。

## 文件与交付边界

| 文件 | 用途 |
|---|---|
| `StarbayUE5.uproject`、`Config/` | 工程入口、DX12/SM6、Lumen、常规阴影、输入与地图设置 |
| `Tools/Open-Starbay.ps1` | 正常打开、首次导入或执行指定脚本；仅设置进程缓存路径 |
| `Tools/bootstrap_scene.py` | 带预检和冲突保护的首次导入、校准与建图 |
| `Tools/install_third_person.py` | 复制同版本官方模板及依赖，记录文件校验和 |
| `Tools/validate_scene.py` | 当前地图只读结构与稀疏碰撞检查 |
| `Tools/smoke_play.py` | 真实 PIE 的出生、原生移动、跳跃和清理检查 |
| `Tools/refine_materials.py` | 保留原资产的叶片与发光材质副本修正 |
| `Tools/Package-Starbay.ps1` | 带输出保护和日志的预编译 Development 打包 |
| `Tools/export_assets.py`、`verify_assets.py` | 独立 FBX 导出与 Blender 回读验证 |
| `Tools/fetch_materials.py` | CC0 PBR 获取与来源记录 |
| `SourceAssets/asset_manifest.json` | 源 FBX 尺寸、大小和校验和 |
| `Design/首次步行验收.md` | 完整路线、已知障碍和待验收项目 |
| `Saved/` | 本地导入、模板、射线、PIE、材质与打包原始报告；不作源码上传 |

Git 保存制作脚本、配置和说明，不提交 Epic 官方模板 Content、引擎、账号信息或缓存。Windows 成品包含已烘焙资产与所需运行时对象代码；Release 的可编辑源工程包若包含模板 Content，同样受 Epic 对应许可约束，不能当作项目原创开源素材。具体许可见 [第三方说明](THIRD_PARTY_NOTICES.md)。
