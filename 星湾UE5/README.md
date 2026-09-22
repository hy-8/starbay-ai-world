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
4. 运行 `Tools/Open-Starbay.ps1 -ImportScene`。若自动发现失败，传入 `-EngineRoot 'D:\tools\UnrealEngine\UE_5.6'`，以实际安装位置为准。
5. 脚本会导入 FBX、校准比例和水平轴、创建场景、设置复杂静态碰撞、太阳、天空、雾、后处理和玩家起点。原生开门逻辑尚未实现，首次场景不放置阻挡入口的门扇。
6. 查看 `Saved/scene_import_report.json`。只有 `status=scene_created` 且校准通过，才能继续验收场景。若失败，保存日志、修复具体错误；脚本默认拒绝覆盖既有资产和手工编辑，重试需新建导入版本或在副本中工作。
7. 在编辑器添加官方 Third Person 功能包，将关卡 GameMode 设为 `BP_ThirdPersonGameMode`，检查角色、动画、相机、碰撞与起点。脚本仅在该蓝图已经存在时自动使用它；默认飞行 Pawn 不算第三人称玩法完成。

首次导入前 `.umap` 尚不存在，项目地图设置指向待生成的 `L_Starbay`。这是预期准备状态；不要把只有 `.uproject` 的工程描述成完整可玩游戏。

## 重新生成资产

先保护任何手工编辑。在游戏目录运行增量建模脚本，再在此目录运行导出、验证和预览：

```powershell
$taskBlender = 'D:\tools\Blender\blender-4.5.9-windows-x64\blender.exe'
& $taskBlender --background --factory-startup --python '..\星湾街区_3D探索\build_detail_v6.py'
& $taskBlender --background --factory-startup --python 'Tools\export_assets.py'
& $taskBlender --background --factory-startup --python 'Tools\verify_assets.py'
& $taskBlender --background --factory-startup --python 'Tools\preview_assets.py'
python Tools/fetch_materials.py
```

最后一项需要 Python `requests`，从 Poly Haven 公共 API 获取两组 1K CC0 材质，核对来源 MD5 并记录 SHA-256。材质文件和具体许可见 `SourceAssets/Materials/material_sources.json`。导入脚本会将法线贴图设为 DirectX Normal、非 sRGB，将粗糙度贴图设为线性数据。

旧的 `星湾街区.blend` 保持不动；增量脚本输出新的 `星湾街区_第六版场景.blend` 和 `assets/星湾_第六版增量场景.blend`。这些生成目标在重跑时会更新，手工修改前应另存。

## 文件索引

| 文件 | 作用 |
|---|---|
| `StarbayUE5.uproject` | UE5 工程入口，启用编辑器 Python 与编辑器脚本工具 |
| `Config/` | Lumen、虚拟阴影、TSR、Windows DX12 与地图设置 |
| `Tools/export_assets.py` | Blender → 烘焙变换后的独立 FBX |
| `Tools/verify_assets.py` | FBX 回读与尺度、顶点、校验和检查 |
| `Tools/fetch_materials.py` | CC0 PBR 素材下载与来源记录 |
| `Tools/bootstrap_scene.py` | UE 编辑器内导入、PBR 材质、轴向校准和建图 |
| `Tools/Open-Starbay.ps1` | 发现已安装引擎、正常打开或首次导入 |
| `SourceAssets/asset_manifest.json` | 导出源、包围盒、大小与校验和 |
| `Validation/asset_validation.json` | 已执行的 Blender 回读验证结果 |
| `Preview/` | 标注来源的资产预览 |
| `Design/制作路线.md` | 写实目标、性能预算与功能迁移次序 |

当前代码仓库不包含 UE 引擎、账号信息、缓存或 Epic 官方角色模板。大型源工程与资产包通过 Release 交付；FBX 也可以用仓库中的原始 GLB 和脚本重建。
