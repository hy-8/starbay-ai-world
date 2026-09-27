# 第三方素材说明

人体基础来自 MakeHuman Community：

- `base.obj`：https://github.com/makehumancommunity/makehuman/blob/master/makehuman/data/3dobjs/base.obj
- 男性形体目标： https://github.com/makehumancommunity/makehuman/blob/master/makehuman/data/targets/macrodetails/asian-male-young.target

两个下载文件均在文件头明确写有 “This asset was explicitly released as CC0 in september 2020.”，采用 CC0 1.0： https://creativecommons.org/publicdomain/zero/1.0/ 。这针对这两个资产，不表示 MakeHuman 整个软件或所有第三方内容都采用同一许可。

原资产列出的贡献者包括 Data Collection AB、Joel Palmius、Jonas Hauquier。保留下载文件原始声明；下载地址及 SHA-256 见 `Source/sources.json`。

本工程的服装、配饰、发束和展示台由本次脚本建立。用户参考图仅用于理解造型方向，未打包或上传原图、原游戏 Logo、游戏模型和纹理。不对设计权利或商业授权作未经审查的保证。

## v0.2 精修补充

新增 15 个 MakeHuman 面部形体目标，均检查文件头中相同的明确 CC0 声明；地址、权重与 SHA-256 见 `Source/couture_sources.json`，原始文件及声明随模型附件提供。没有更改下载的原始文件。

`Materials/Ember_Brocade_Albedo.png` 通过内置 image_gen 根据原创文字描述生成，未使用原游戏贴图。完整提示词保存在 `Materials/texture_provenance.json`。ORM 和切线空间法线由 `Tools/bake_textile.py` 在 Blender 中从该图派生并烘焙；它们是艺术化材质参数，不是现实织物的扫描测量数据。

## v0.4 动态角色补充

`Source/default.mhskel` 与 `Source/default_weights.mhw` 来自 MakeHuman 官方仓库，文件内部许可字段为 CC0；来源和 SHA-256 见 `Source/hand_binding_sources.json`。

`Source/UE_Reference` 中的 Manny 骨架参考及六项基础动作，由本机 UE5.6 官方模板导出。它们以及从其转换的动作保留 Epic Games 的许可约束，不属于 CC0；来源和哈希见 `Source/UE_Reference/sources.json`。UE 第三人称、战斗模板、动画蓝图和 Niagara burst 模拟同样保留 Epic 许可。

四秒施法关键帧、服饰辅助骨骼动画、红金造型与火焰 Sprite 着色器为本项目制作。现有披风和发丝使用烘焙骨骼动画，没有真实布料模拟。
