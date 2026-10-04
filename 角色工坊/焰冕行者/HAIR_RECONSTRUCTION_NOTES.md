# 红发角色 · 更换发型方法记录

用户要求持续改善真实三维发型，并允许更换方法。当前目标仍在进行，任何输入图、成功推理、通过文件检查或发丝数量都不能替代艺术验收。

## 2026-10-04 · 头皮转移诊断与自由导向线

上一轮尚未同步的 `groomart01/02` 与 `hairfit02` 已复核：前者仍像平滑短发帽，后者大面积露头皮，均未采用为成品。本轮没有复跑旧目录或覆盖历史工程。

实际新证据：Hair Editor 人体有 13,380 个 `body` 顶点、4,778 个辅助几何顶点和 1,000 个关节辅助顶点；头顶最高的部分顶点属于 `helper-hair`。旧对应拟合把所有面都放入头皮 BVH，且只用发根三角面的线性坐标系变形整条头发。两者存在风险，但不能把所有视觉失败都归因于这一点。`radialgroom01` 排除辅助面、沿整个发丝保留径向头皮间距后仍然秃顶。`donorcontrol01` 把同一份旧缓存放回原头模也出现秃顶，证明缓存本身已经存在问题。未更改修改器参数的 `radialgroom02` 恢复更多前部覆盖，但侧后方仍太稀、太贴头；默认模板同样没有达到目标。

因此新增 `build_freeform_rock_groom.py`：发根贴合实际头皮，可见层采用独立的空间 S 形导向线，不再沿实心假发网格追踪或全部紧贴球面。分别设计左右头顶、眉侧刘海、耳侧和后颈；原生毛发及隐藏导向线保留在 Blender 工程中。`freeformrock01` 出现成对过高的顶部拱形，`02` 压低并增加独立刘海，`03` 加入长短交错的上层及向下生长的后颈曲线。这些仍是未通过验收的结构试验。

`finish_freeform_groom.py` 进一步裁剪旧底发：`freeformrock04` 的 12—23mm 底发暴露了过大的支撑空隙；`05` 按发根区域保留 26—64mm 的支撑层；`06` 保留毛发中段的厚度，把主要变细过程集中到发梢。最新检查工程为 `Exports/freeformrock06/Ember_Regent.blend`，实际四视角为 `Renders/freeformrock06`，Cycles/OptiX 192 samples、不去噪、1200×1400。

**已经逐张查看，仍未达到用户参考级质量。** 顶部与侧面的发束仍有重复排布，局部头皮缝隙仍可见；后颈变长，但发梢过于直、偏稀。脸部及服装没有因此达到作品标准。结构验证只检查几何有限值、正半径、贴图存在和文件哈希，不能充当艺术验收。没有新骨骼、动作、UE 导入或发布。

新增资源调查：Blender 官方 `Hair Styles` 示例已实际下载至 `Source/BlenderHairStyles/Bystedt_HairStyles.blend`，作者 Daniel Bystedt，官方页面和文件内 `Hair demo file info` 明确为 **CC BY-SA**，没有在这些证据中注明版本，不能写成 CC0 或擅自标 4.0。源文件 SHA-256 为 `1ad6202095c1793678fee7d69a7e9f8b5fdb6e5c293d300eb1062d2d437e8d48`。实际以关闭自动执行脚本的方式打开并检查，包含 curly hair、long hair main/strands、cyberpunk hair、braided hair 的原生导向线和节点设置；来源记录在 `Source/official_groom_sources.json`。原 curly hair 两张实际控制渲染在本地 `Renders/officialcurly01`，已经读图：分缕和头皮覆盖正常，但密集小卷的默认风格不符合目标，需要软化卷度及重新设计男性层次。图中灰色女性头模是原资产，**不是用户角色成果**。尚未拟合或采用到本轮角色中，也未分发原资产或改编资产。下一步评估松散波浪、偏分、耳侧及后颈造型与目标头部的贴合，不能仅凭来源成熟就宣布效果合格。

复现需本地已有基础工程及许可资产；在干净副本中用全新版本名：

```powershell
# Blender 后台 --python Tools/build_freeform_rock_groom.py
# -- 新导向线版本 --refine --flow
# Blender 后台 --python Tools/finish_freeform_groom.py
# -- 新修整版本 新导向线版本 --support --shaft
```

`fit_radial_groom.py` 保留作失败方法研究；`bake_native_donor_groom.py` 仅求值原修改器、不修改参数，生成缓存及哈希。不能用这些失败模板替换当前角色完成品。所有大型工程留在本地，GitHub 同步经过检查的源码、来源和真实渲染证据。

## 已实际检查的失败方案

| 本地版本 | 方法 | 四视角实际结论 |
| --- | --- | --- |
| hairfit01 | CC0 Hair Editor，以人体顶点对应关系拟合 | 短发模板不符合目标，头顶稀疏、头皮暴露 |
| hairdesign02 | 头皮射线 + 原创狼尾曲线 | 顶部过于平滑，前额散发遮脸、后颈像直帘 |
| hairasset01 | Elvaerwyn 的 Maxwell 发片 | 短尖发型不合适；高光像塑料帽 |
| hairasset02 | Elvaerwyn 的 inverted curly bob 发片 | 波浪层次可参考，长度不合适、发片像亮薄片 |
| hairgroom01 | 作者波浪发片按 UV 转为原生细发丝 | 造型仍像宽带，前额卷曲和后颈层次不合格 |
| hairrecon01 | 本地 Hunyuan3D 形状重建，直接初步拟合 | 前额层次更丰富，但后脑穿进头皮；有悬浮碎片，材质仅为检查泥模 |
| hairrecon02 | 保留最大连通网格，移动后脑壳、偏分变形 | 大面积后脑穿插已修正；仍是形状检查，不能称为真实头发 |
| hairrecongroom01 | 最小主曲率与偏分梳理场，沿重建表面追踪原生发丝 | 块状输入网格隐藏；头顶存在覆盖缺口，侧面底发不足，仍有带状高光 |
| hairrecongroom02 | 补短底发、1800×2100 不去噪实渲 | 发丝可辨，但底发实际过长遮眼遮脸、后颈有直帘；未采用 |
| hairrecongroom03 | 底发逐条裁短、深色红发材质 | 四视角确认眼脸恢复可见、后脑覆盖完整；外翻发束和部分发根端仍生硬 |

`hairdesign01`、`rawhair01`、`rawhair02` 是提前报错的保留目录，没有可用成品。前者是数组类型问题；后两者是新工具低内存加载适配中发现的未发布编码器参数和缺失 components 属性。`rawhair03` 已实际完成推理及网格导出。

## 当前本地重建路线

1. 使用用户红发演唱会角色参考，生成一个透明底、没有人脸和人体的发型重建输入。`Source/HairReconstruction/hair_input01.png` 是 **AI 生成的输入**，不是完成角色建模的展示图。
2. 在独立环境 `D:/tools/Hunyuan3D-hair-runtime` 运行官方 `tencent/Hunyuan3D-2mini` 的 shape-only 推理。源码在 `D:/tools/Hunyuan3D-2-hair`，模型权重在 `D:/models/Hunyuan3D-2mini-hair`；均未复制进仓库。
3. 使用 mmap、meta 参数赋值和组件 CPU 卸载，减少这台 16GB RAM / 8GB VRAM 机器上的加载峰值。仅删掉推理不会调用且发行权重不存在的 VAE encoder/pre_kl；没有随机初始化缺失的生成参数。补充官方卸载方法缺失的 components 字典，并修正采样设备元数据。
4. `rawhair03`：seed 10203、40 steps、guidance 5、384 网格采样、4000 chunks、fp16，实际输出 761,984 顶点 / 1,523,874 三角面。约 76.72 秒完成本次推理与导出。数量仅为数据记录。
5. 保留最大连通发型，剔除 86 个悬浮小碎片，按 Blender 角色头部拟合。后脑向后修形，前额不整体平移；顶部偏分向一侧移动约 2cm。输入网格与所有失败候选保留。
6. 在临时简化网格上拟合局部曲率、设计偏分梳理场，追踪真实三维导向曲线，插值成 Blender 原生 CURVES。重建的实心块状网格保持可编辑，但渲染时隐藏。
7. `hairrecongroom02` 增加来自 `hairdesign02` 的短头皮底发、修正顶部导向曲线终止位置，并用 1800×2100、256 samples、不去噪的 Cycles/OptiX 实渲复核。实际细发丝出现，但底发过长，不能采用。
8. `polish_reconstructed_groom.py` 把底发逐条裁到眉毛之上、缩短鬓角和后颈，收深物理红发颜色。`hairrecongroom03` 已读四视角：眼脸重新露出、后脑覆盖完整，但外翻层次仍生硬。
9. `root_reconstructed_groom.py` 将 85,056 条表面导向发丝的根部回贴真实头皮，前 20% 平滑过渡，发梢增加 3—14mm 的独立重力垂落。`hairrecongroom04` 四视角确认脸部无遮挡、背面覆盖完整，但顶部两处高起发束与外翻轮廓还生硬。
10. `style_asymmetric_fringe.py` 平滑压低头顶体积、加强前部偏分，并增加 22 条独立梳理导向曲线/4,180 条原生发丝的斜向刘海。`hairrecongroom05` 四视角已读：眼脸可见、后脑连续、偏分增强；仍有生硬的顶部/侧后方卷翘与规整层次，未达到参考作品质量。可见头发均为原生 CURVES；可见实心假发网格为零。
11. `hairrecongroom05` 结构检查通过，当前仍是静态候选；新近景 `editorial09` 已完成 1800×2100、Cycles 384 samples、不去噪真实渲染并读图。细发丝与红色层次可辨，局部顶部卷翘/宽弧形刘海仍不自然，不能称为参考级成品。沿用几何静态展示姿势，不是新增动作或骨骼。

所有输出使用全新版本目录，脚本拒绝覆盖旧版本。静态发型实验未接入 UE、未生成新动作或物理头发模拟。

## 来源和许可

- Hair Editor：Tomáš Klecer，CC0；既有来源记录在 `Source/hair_editor_sources.json`。
- 作者发片：Elvaerwyn，来源 `https://static.makehumancommunity.org/assets/assetpacks/hair02.html`。实际使用的 `.mhclo` 明确标 `CC_by` / `CC-BY`，版本未注明，不写成 CC BY 4.0。`elvs_witchy_lil_bob` 的文件头是 AGPL3/Unknown，未使用。
- 本地模型：Tencent Hunyuan3D-2，源码 commit `f8db63096c8282cb27354314d896feba5ba6ff8a`。实际下载根 LICENSE 为 **TENCENT HUNYUAN 3D 2.0 COMMUNITY LICENSE AGREEMENT**；不是 CC0、不是 MIT，也不能把旧源文件头的文字当作完整现行许可。许可包含地区限制，输出本身不属于 Model Derivatives，Tencent 不主张输出权利；不把这些陈述扩写成无条件使用承诺。未分发模型或工具代码。
- 权重 SHA-256：`3cc66f3bea33e4062b7dbc875ffe1d70c4888914aec3e91b60f94e9bd01b522b`。
- 输入图、原始网格、拟合工程都保留本地。私有 GitHub 仅同步经过检查的制作脚本、来源与渲染证据；没有新 Release 或社交平台发布。

## 重现入口

在已有源资产、独立环境和模型文件的干净副本上使用新版本名：

```powershell
& 'D:\tools\Hunyuan3D-hair-runtime\Scripts\python.exe' -X utf8 'Tools\reconstruct_hair_shape.py' 新原始版本 --steps 40 --resolution 384
```

原始网格清理后，Blender 后台执行 `fit_reconstructed_hair.py -- 新拟合版本 原始版本 --fit-back`，再执行 `groom_reconstructed_hair.py -- 新发丝版本 拟合版本 --fill-scalp --detail`。清理需要 `connected_hair.npz`，短底发需要既有 `Exports/hairdesign02`。原项目文件不能在缺少依赖时被当成可从脚本独立重建的交付包。
