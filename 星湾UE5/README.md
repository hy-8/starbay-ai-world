# 星湾 · Unreal Engine 5

2026-09-22 起，本项目以 **UE5 Windows 独立游戏**为后续方向。浏览器原型保留作玩法和本地 AI 协议参考。

## 当前交付是什么

当前是 **引擎迁移与场景资产基础**，不是已经完成的 UE5 游戏。

- 已创建 `.uproject`、渲染配置、场景导入与坐标校准脚本。
- 已制作风栖茶庭：石铺地、喷泉水池、木廊、长椅、桌上物件、灯串和独立叶片树冠。
- 已补充夜市货品、木箱、招牌、旗帜、绿化与长廊细节。
- 已从实际场景导出主街区、新增细节、左右门扇和三份一米校准体，共 7 个 FBX。
- FBX 已在 Blender 回读，验证尺寸、顶点数量、有限坐标与文件校验和。
- `Preview/茶庭_Blender资产预览.png` 是 Blender 资产预览，**不是 UE5 截图**。
- 引擎内导入、碰撞、第三人称控制、原生 NPC、AI 对话、任务、存档、帧率与 Windows 打包仍需在 UE5 安装后验证和实现。没有验证前，不能声称已交付这些能力。

## 首次进入 UE5

1. 在 Epic Games Launcher 安装 UE5，建议安装至 D 盘。当前项目先以 5.6 API 为目标；安装其他 5.x 版本时要实际验证导入脚本。
2. 安装选项保留核心引擎、Windows 支持、模板与功能包；首轮不需要 Android、iOS、Linux 支持或巨大的编辑器调试符号。
3. 使用发布包内的 `SourceAssets`，或按下面命令重新导出。
4. 先保存编辑器中打开的地图，再运行 `Tools/Open-Starbay.ps1 -ImportScene`。启动脚本只自动选择 `.uproject` 指定的引擎版本；若自动发现失败，传入 `-EngineRoot 'D:\Program Files\Epic Games\UE_5.6'`，以实际安装位置为准。
5. 导入前会检查未保存地图、目标地图是否已存在、整个导入目录是否已有资产、清单中的必需模型与重复名称，以及全部 FBX 和可选 PBR 文件的路径、校验和、材质角色。通过这些检查后才导入 FBX、校准比例和水平轴、创建场景、设置复杂静态碰撞、太阳、天空、雾、后处理和玩家起点。原生开门逻辑尚未实现，首次场景不放置阻挡入口的门扇。
6. 查看 `Saved/scene_import_report.json`。只有 `status=scene_created` 且校准通过，才能继续验收场景。若失败，保存日志并修复具体错误；脚本不会自动清理失败导入留下的资产，也不会覆盖既有地图。重试时应在工程副本中工作，或将脚本的 `CONTENT` 改为全新的导入目录；若地图已生成，还需使用新的 `MAP` 路径，并同步地图配置及 `Open-Starbay.ps1` 中的地图存在性检查路径。
7. 使用官方 Third Person 功能包，将关卡 GameMode 设为 `BP_ThirdPersonGameMode`，检查角色、动画、相机、碰撞与起点。下面的模板脚本应在首次场景导入前运行，场景脚本检测到该蓝图后会自动使用它；也可从编辑器添加功能包。默认飞行 Pawn 不算第三人称玩法完成。

首次导入前 `.umap` 尚不存在，项目地图设置指向待生成的 `L_Starbay`。这是预期准备状态；不要把只有 `.uproject` 的工程描述成完整可玩游戏。

Unreal 的 `new_level()` 会关闭当前地图且不保存。脚本因此在开始导入前、创建地图前各检查一次未保存地图；发现改动就停止，由使用者先保存或主动放弃这些改动。它不会代替使用者保存既有地图。末尾仅保存本次导入目录，资产保存失败也会记入失败报告。这些保护已完成静态与模拟检查，仍需安装引擎后验证真实导入行为。

首次行走按 [首次步行验收](Design/首次步行验收.md) 核对出生点、门洞与各区域。源 FBX 射线检查发现浏览器的部分导航线穿过树、入口柱和单车；原导航图不能直接作为 UE 原生导航使用。

在引擎完整安装后，从 `星湾UE5` 目录运行一次：

```powershell
python Tools/install_third_person.py --engine-root 'D:\Program Files\Epic Games\UE_5.6'
```

它复制本机官方 ThirdPerson 模板及 Characters、Input、LevelPrototyping 三组共享资源，保留 `/Game` 路径，并加入模板的 `DefaultInput.ini`。全部目标先检查冲突，已存在的同名文件不会覆盖；也不会替换本项目的 `.uproject`、地图或渲染设置。复制记录和 SHA-256 位于 `Saved/template_import_report.json`。这些 Epic 模板资源遵循引擎许可，不属于项目原创资产。

地图打开后，可在编辑器 Python 环境执行 `Tools/validate_scene.py`。它只检查当前地图的结构、出生点、碰撞设置和少量地面/通道射线，输出 `Saved/scene_validation_report.json`；不切图、不保存地图、不启动 PIE。仍须用真实角色进行走跑跳、镜头和门洞验收。

## Epic 启动故障的恢复

2026-09-22 实际遇到 Epic 的“Online Services Unavailable”：安装文件完整，但 EOS 日志报 `Unsupported architecture: unknown`，退出码 71。原因是启动它的自动化进程缺少 Windows 常规 CPU 环境变量。仅恢复新子进程的机器环境值后，EOS 日志确认 `MAINSERVICE_READY`，UE 5.6.1 下载正常开始。

`Tools/Start-Epic.ps1` 封装了这次修复：通过已安装的官方 EOS Bootstrapper 启动，不修改系统环境、注册表或登录信息；若 Epic 已运行则直接返回，不重启或中断下载。正常从桌面启动 Epic 无需此脚本。`Open-Starbay.ps1` 也只在新编辑器进程中补齐这些标准环境值。

若已经开始安装，且希望安装完成后衔接首次导入，可运行 `python Tools/continue_after_install.py --engine-root 'D:\Program Files\Epic Games\UE_5.6'`。这是一次性流程：等待 Epic 登记安装完成，执行带冲突保护的模板复制，再启动编辑器导入；任何一步失败就停止，不自动重试、不覆盖既有资产。默认总等待上限为 120 分钟，进度在 `Saved/continuation_status.json`，详细输出可重定向至本地日志。它不执行玩法验收或打包，也不更新交付完成状态。

## 重新生成资产

以下命令均在 `星湾UE5` 目录执行，并使用独立的后台 Blender 进程。导出脚本会拒绝在交互式 Blender 中运行，避免清空正在编辑的场景。

仅在需要重新制作增量场景时运行下面的建模命令。先保护 `星湾街区_第六版场景.blend`、`assets/星湾_第六版增量场景.blend` 及其对应增量资产的手工修改；建模脚本本身仍会更新这些生成文件，FBX 导出保护不涵盖这一步。

```powershell
$taskBlender = 'D:\tools\Blender\blender-4.5.9-windows-x64\blender.exe'
& $taskBlender --background --factory-startup --python '..\星湾街区_3D探索\build_detail_v6.py'
```

已有交付包含 FBX，再次执行默认导出会主动停止，不会覆盖。用 `--` 后的 `--output-dir` 指定全新候选目录；脚本会创建该目录，但若其中已有任意 FBX 或 `asset_manifest.json`，仍会拒绝运行：

```powershell
$taskBlender = 'D:\tools\Blender\blender-4.5.9-windows-x64\blender.exe'
$taskAssetVersion = Join-Path $PWD ('SourceAssets_candidates\' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
& $taskBlender --background --factory-startup --python 'Tools\export_assets.py' -- --output-dir $taskAssetVersion
```

只有尚无 FBX 和清单的全新工程，才可以省略 `--output-dir`，首次输出到默认 `SourceAssets`。导出只读取游戏目录中的两个 GLB，不修改原始 `.blend` 或 GLB。

**`--output-dir` 仅改变 FBX 导出位置。** `verify_assets.py`、`fetch_materials.py` 和 Unreal 导入脚本仍读取工程内的 `SourceAssets`，不会自动跟随候选目录。采用新版本前，建议在工程副本中保留旧 `SourceAssets` 完整备份，再以候选目录作为该副本的 `SourceAssets`，并保留原有 `Materials` 子目录或重新获取材质。不要把旧、新 FBX 与不同版本清单混放。完成这一步后，再针对实际采用的 `SourceAssets` 执行回读验证：

```powershell
$taskBlender = 'D:\tools\Blender\blender-4.5.9-windows-x64\blender.exe'
& $taskBlender --background --factory-startup --python 'Tools\verify_assets.py'
python Tools/fetch_materials.py
```

最后一项需要 Python `requests`，从 Poly Haven 公共 API 获取两组 1K CC0 材质，核对来源 MD5 并记录 SHA-256。已有完整材质时可跳过；材质文件和具体许可见 `SourceAssets/Materials/material_sources.json`。导入脚本对 DirectX 法线贴图使用 Normal Map 压缩、关闭 sRGB，并将粗糙度贴图设为线性数据。

`preview_assets.py` 读取游戏目录的 `星湾街区_第六版场景.blend`，生成 Blender 预览并更新 `Preview` 中的同名文件；它不是 FBX 回读验证或 Unreal 渲染。需要更新预览时再执行 `& $taskBlender --background --factory-startup --python 'Tools\preview_assets.py'`。旧的 `星湾街区.blend` 保持不动。

## 文件索引

| 文件 | 作用 |
|---|---|
| `StarbayUE5.uproject` | UE5 工程入口，启用编辑器 Python 与编辑器脚本工具 |
| `Config/` | Lumen、虚拟阴影、TSR、Windows DX12 与地图设置 |
| `Tools/export_assets.py` | 后台 Blender → 烘焙变换后的独立 FBX；保护已有导出，支持新输出目录 |
| `Tools/verify_assets.py` | FBX 回读与尺度、顶点、校验和检查 |
| `Tools/fetch_materials.py` | CC0 PBR 素材下载与来源记录 |
| `Tools/bootstrap_scene.py` | UE 编辑器内完整预检、未保存地图保护、导入、PBR 材质、轴向校准和建图 |
| `Tools/Open-Starbay.ps1` | 发现已安装引擎、正常打开或首次导入 |
| `Tools/Start-Epic.ps1` | 在缺少标准进程环境时，通过官方入口启动 Epic |
| `Tools/install_third_person.py` | 从完整安装的同版本官方模板复制角色、动画和输入依赖 |
| `Tools/continue_after_install.py` | 一次性等待安装完成，然后接入模板与首次导入 |
| `Tools/validate_scene.py` | 当前编辑器地图的结构与稀疏碰撞射线检查 |
| `SourceAssets/asset_manifest.json` | 导出源、包围盒、大小与校验和 |
| `Validation/asset_validation.json` | 已执行的 Blender 回读验证结果 |
| `Preview/` | 标注来源的资产预览 |
| `Design/制作路线.md` | 写实目标、性能预算与功能迁移次序 |

当前代码仓库不包含 UE 引擎、账号信息、缓存或 Epic 官方角色模板。大型源工程与资产包通过 Release 交付；FBX 也可以用仓库中的原始 GLB 和脚本重建。
