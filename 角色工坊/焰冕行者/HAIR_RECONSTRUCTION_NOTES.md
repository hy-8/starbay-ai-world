# 红发角色 · 更换发型方法记录

用户要求持续改善真实三维发型，并允许更换方法。当前目标仍在进行，任何输入图、成功推理、通过文件检查或发丝数量都不能替代艺术验收。

## 2026-10-04 · 整束分区、头皮小块与授权发片路线

最新实际检查点为 `regionalgroom08`，四视角已经逐张查看，1200×1400、192 samples、不去噪；`editorial13` 的实际近景已经查看，1800×2100、384 samples、不去噪。两个工程的结构检查通过。**仍未通过参考级艺术验收，目标继续。下文其他“当前”段落均为历史检查点。**

### 诊断与更换方法

`diagnose_spatial_groom.py -- layerisolation01 spatialfringe04` 逐组隔离实际毛发，四张图均已查看；保留区域的 76,484 条曲线没有发丝到达所定义的上前额诊断区，宽冠部主要来自自绘前额。检查源文件哈希未变。该诊断区只是本次定位范围，不是全头的穿插检测。

`author_concert_fringe.py` 增加 `--root-patches --soft-patches --fibers-per-guide`，改为从每条自绘导向线附近的实际 body 头皮小块生长长发，避免宽 donor-root 偏移扇成一大片。控制图07为 32 条明确设计的路径，不自动展开为随机大束；08加强部分横向转折却产生绳圈和空隙，09撤回过强冠部改动，只保留两束眉侧刘海的重画。可见 CURVES 本身可编辑，控制图修改后需要重新烘焙，隐藏路径不是实时驱动器。

另从官方公开免费接口获取 Ddr Rcs 的 **Female Shaggy Mullet Haircut**，检查 424 个实际连接发片、Factor BYTE_COLOR、UV 和打包贴图。常量 `curve_group_id_ht` 不能分组，实际按网格连接分组。`groom_asset_card_guides.py --wave-cut --atlas-fibers` 从中心线生长真实原生毛发，并在原 UV 上采样 alpha，避免将贴图透明区域填成实心波波头。改编仍是 Royalty Free，不是 CC0，几何提取清单 `licensed_groom_design.json` 留本地。

### 已查看的试验与不足

| 试验 | 实际检查结论 |
| --- | --- |
| spatialfringe06 / 07 | 小块生根降低宽扇面；06 绳状交叉，07 湿细感和侧面缺口，未作为成品 |
| spatialfringe08 | 软截面和更多长短发丝，冠部仍顺滑，前后衔接不足；全质量四视角已看 |
| spatialfringe09 / 10 | 09 加强冠部转折导致圈状交叉和空隙；10 恢复较克制冠部，只保留两束眉侧的重画 |
| assetshag01 | 原发片的实际拟合控制，覆盖连续，但微短刘海和直长侧后发不匹配目标 |
| nativeasset01 / 02 | 从授权发片提取实际中心线转发丝；02 采样原 atlas 透明度，仍有圆帽与钝齐刘海 |
| regionalgroom01 | 按发根高度删掉源冠部，却同时删掉覆盖后脑的长发；后方大块裸露，否定 |
| regionalgroom02 | 改为按完整发束末端/走向保留侧后区域，恢复后脑覆盖；发尾仍偏直，耳前有硬角 |
| regionalgroom03 | 上短下长和波浪调整过强，后方轮廓过圆；冠部控制08也带圈状空隙 |
| regionalgroom04 | 压缩后脑、撤回冠部圈状改动；试验含后向位移未渐隐的问题，保留但不复用 |
| regionalgroom05 / 06 | 修复位移、分散转折/剪裁；硬高度阈值仍造成横向条带，未采用为成品 |
| regionalgroom07 / 08 | 后脑压缩用连续空间权重过渡，横向硬折线减轻；08 为全质量检查点，仍有顺滑宽冠部、偏直后发和针状尾部 |

这批试验的四视角均已实际检查，草稿为 64 samples、80% 分辨率；无 `--draft` 为 192 samples、全分辨率。所有图都由实际 3D 工程渲染，没有使用生成肖像冒充建模。历史01—06的脚本参数和阈值经历调整，最终脚本不保证逐字节复现这些历史结果，源模型与旧图均保留。07/08 的清单记录处理脚本哈希。

### 当前实际工程与复建条件

`regionalgroom08` 可见几何由 32,000 条原创前额、23,657 条 Bystedt 短支撑、74,113 条 Ddr Rcs 衍生侧后发丝组成；数量只是结构记录。头皮间距修正针对最近 body 表面，未对全部衣物或动画穿插作证明，后颈/领口需继续检查。`editorial13` 使用静态几何摆姿，不是新骨骼或动画。

本地依赖必须已经存在；仅从 GitHub 清单不能恢复授权源模型。用新版本名运行，不能覆盖历史目录：

```text
Blender --python author_concert_fringe.py -- 新前额版本 layercut08 --choppy-locks --reference-cut --root-patches --soft-patches --fibers-per-guide 1000 --design Source/HairReconstruction/concert_fringe_control09.json
Blender --python shape_regional_groom.py -- 新组合版本 nativeasset02 新前额版本 --scissor-layers --lean-wolf --stagger-locks
Blender --python render_editorial_pose.py -- 新展示版本 新组合版本 --portrait-only --hair-detail
Blender --python validate_concert_still.py -- 新组合版本
```

08 组合使用 `spatialfringe10` 的实际几何，它虽按草稿参数渲染，模型几何精度相同。来源/许可见 `Source/licensed_shag_sources.json` 与 `THIRD_PARTY_ATELIER.md`。作者原资产、预览、贴图、提取的几何路径及含该资产的 `.blend` 均留本地；只同步源码、原创前额控制、非几何清单和所选真实渲染。没有新 Release、UE 接入、动作或社交发布。

下一步应先打散冠部宽顺滑面和后颈针状尾部，比较保留授权发片贴图与原生发丝的实际差异；再独立重做面部神态和服装受力褶皱。提高采样已证明不能解决当前造型缺陷，不作为主要方法。

## 2026-10-04 · 改为在目标头皮直接重梳前额

新的实际检查候选为 `Exports/targetfringe04/Ember_Regent.blend`，中性四视角 `Renders/targetfringe04` 已逐张查看，1200×1400、Cycles/OptiX 192 samples、不去噪。**仍未达到参考级作品质量，目标继续。** 相比旧版，前额的高起硬结减轻，侧面缺口得到补充，前额有不同长度与转折；仍有过厚、片状的刘海、相似的弯曲和不够自然的前后衔接，面部与衣服仍为 WIP。

这次区分了几个问题：`layercut04` 的实际根半径最高为 110µm；只把发丝变细会暴露原来覆盖不足的区域，因此 `layercut06` 增密后采用 34—46µm 根半径。分缝附近的高起形状主要位于发根/中段，不能靠随机裁剪发梢解决。检查源节点发现了预设分缝吸附和另一组 `long hair strands` 分支；绕过它们的实际对照 `directgroom02` **仍有前额隆起和发帘**，所以不能把原节点写成唯一原因。

采用的新方法 `Tools/recomb_target_fringe.py`：从已检查的 `layercut08` 保留耳侧与后颈，在角色本身的真实 body 头皮上建立径向表面距离场，直接规划前额路径；分区域设计长短、侧向转折、贴合距离和独立末端，另加较短的支撑发丝。可见部分全部为原生 CURVES，没有用生成肖像或图片平面替代模型。隐藏的代表路径可编辑，但**不是烘焙可见毛发的实时控制器**；可见毛发本身保留为可编辑曲线。

本轮实际试验均保留：

| 版本 | 方法与实际检查结论 |
| --- | --- |
| layercut05 | 全局降低卷度/聚束；四视角更散、更宽，未采用 |
| layerflow01 | 局部压低冠部、细化发丝、分开末端；四视角暴露后方覆盖不足，未采用 |
| layercut06 / rootflow01 | 增密细化，再对局部分缝发根作头皮切线过渡；四视角仍有硬结，未采用为成品 |
| layercut07—09 | 重做源前额三次曲线、关闭/减弱 roll、调整聚束、扩大冠部刘海范围；全部四视角已检查。08 的侧后层次用于新路线的基础，但前额仍不合格 |
| directgroom01 | 绕过节点后缺少 radius 属性而提前报错，没有成品；保留目录，不重跑覆盖 |
| directgroom02 | 直接插值改形后的原导向线，排除装饰发束和分缝吸附；四视角仍过厚、呈发帘，未采用。另存带原生节点的作者坐标系源库，不是最终角色 |
| targetfringe01—03 | 在目标头皮重梳；全部四视角已检查。01 过齐且侧面有缺口，02 补支撑并聚束，03 分散转折并调整长短；均为 64 samples、80% 分辨率检查稿 |
| targetfringe04 | 03 方法的全质量四视角，仍有片状感和相似曲线，保留为本轮实际几何检查点，未通过艺术验收 |

`targetfringe04` 中记录的 70,969 条前额重梳发丝、23,657 条支撑发丝及 171,110 条总曲线仅为几何数据，不是质量证明。Bystedt 改编部分继续遵循 CC BY-SA，版本在所检查证据中未注明；来源及署名见对应 JSON 与 `THIRD_PARTY_ATELIER.md`。所有旧模型和未提交的其他工作保持原状；没有新游戏接入、动画、布料或候选 Release。

实际新近景 `Renders/editorial11/03_Portrait.png` 已完成并查看，1800×2100、384 samples、不去噪，来自 `targetfringe04` 的实际静态摆姿工程 `Exports/editorial11/Redline_Editorial.blend`。发丝可辨、分缝硬结降低，但宽带感、重复转折和面部神态仍未满足参考。两个工程的结构检查通过，检查范围是有限值、正毛发半径、贴图存在及哈希；没有做全量穿插或动作验证，不能扩大其结论。

复现时必须已有 `layercut08` 与其本地依赖，并使用全新输出名：

```powershell
# Blender 后台 --python Tools/fit_official_layercut.py
# -- 新基础版本 --mirror --loose --part --sweep --fiber --clean-flow --lock-flow
# Blender 后台 --python Tools/recomb_target_fringe.py
# -- 新目标版本 新基础版本 --locks --loose-fringe
```

加 `--draft` 只用于检查造型；无该参数为 192 samples 全分辨率。GitHub 保存所选实际渲染与制作记录；原始参考图、作者源库和大体积 `.blend` 保留本地。

## 2026-10-04 · 从已有导向线的原生梳理开始剪裁

本轮完成并查看 `officialwave01—04`、`hybridshag01/02`、`layercut01—04` 的实际四视角，所有目录保留，未覆盖任何旧工程。

| 本地试验 | 方法 | 实际检查结论 |
| --- | --- | --- |
| officialwave01—04 | 官方 curly hair 软化卷度/噪声、整个发丝的真实头皮场转移、分区延长/偏分/粗细与穿插修正 | 覆盖改善，但仍是蓬松圆波波头；前额移末端形成宽带，未采用 |
| hybridshag01 | 原发型裁成很短的底发，外加独立空间导向线与密集束状发丝 | 头顶/后方像规则条带，短底发末端有异常外翘，未采用 |
| hybridshag02 | 保留连续源覆盖、压缩轮廓、减少外层束并增加低频发丝差异 | 覆盖恢复，但仍有重复外层条带、侧面隆起，未采用 |
| layercut01 | 对 long hair main 原始导向线分区剪裁/刘海塑形，再运行原生插值/clump/noise | 耳侧、后颈首次有较自然的男性层次；前额卷度仍太强、形成小圈 |
| layercut02 | 降低 roll、补密度、导向线 S 弯，重做重侧刘海方向 | 小圈减少，后颈松散层次较好；轻侧发束跨向另一侧，前额三角缺口突兀 |
| layercut03/04 | 按发根所在分侧塑形，分开两侧刘海方向，04 加重侧前额 S 弯 | 四视角已看，侧后轮廓与前额层次明显改善；分缝团簇偏硬、部分前额高光仍规整，仍不是参考级成品 |

实际原资产控制图 `Renders/officiallong01` 的两张灰色女性头模渲染已经查看。它们仅用于确认 long hair main 本身的连续覆盖和自然发丝表现，不能当成用户角色图。所有源文件都关闭自动脚本执行。

当前可复核候选：`Exports/layercut04/Ember_Regent.blend`、`Renders/layercut04`。流程在 `Tools/fit_official_layercut.py`：先改变 346 条实际原生导向线的长度/形状，再运行原有插值、分束、噪声及轮廓节点，烘焙可见 CURVES；按真实人体 BVH 转移整条发丝并修正发根/局部穿插。源导向线另保存在隐藏、可编辑集合，原文件不改写。该版本不是通过叠加 AI 肖像、发型图片平面或实心发帽得到。

由该候选生成的展示工程 `Exports/editorial10/Redline_Editorial.blend` 与近景 `Renders/editorial10/03_Portrait.png` 已完成并查看，1800×2100、Cycles 384 samples、不去噪。实际读图：发型方向和层次比旧检查点自然，但分缝仍有硬弧形团簇，人物面部神态与服装精细度并未达到参考。仅保留作真实三维进展证据，非最终作品，未发布新 Release。

结构检查 `Exports/layercut04/structural_validation.json` 通过。额外的距离诊断抽样 20,000 个 z>1.795m 的实际发丝点，0 个负间距，样本最小间距约 0.801mm。此结果只适用于该样本和上部范围，不扩写成对整头毛发/下部/动画的完整证明。来源与改编署名同步到 GitHub，原始 `.blend` 和大型候选留本地。当前仍需精修，目标保持进行。

干净副本中、已有本地依赖时，以全新版本名执行：

```powershell
# Blender 后台 --python Tools/fit_official_layercut.py
# -- 新版本 --mirror --loose --part --sweep
```

原 `officialwave` 的起点是 curly hair，新 `layercut` 的起点是 long hair main；两者都是 Daniel Bystedt 改编毛发，CC BY-SA，所检查证据未注明版本。不要把“更换方法”误写成原创/CC0 毛发。

## 2026-10-04 · 独立空间发束方法与实际结果

这轮进一步试验 `targetfringe05—07`：真实体积截面、眉毛解剖位置对应的放长和冠部分层裁剪。眉毛实际范围为 z=1.752859—1.767436m，平均约 1.760511m。此前把眉毛估在 1.79m 附近造成过短刘海；纠正落点没有自动解决厚重规则前帘。三个版本的四视角都已查看，仍未采用为作品。

新的 `Tools/author_concert_fringe.py` 在实际头皮发根上建立独立空间路径，将原生 CURVES 拆为保留侧后发、短底发与刘海三个对象。18 组初始空间路径的原始版 `spatialfringe01` 形成大卷/交叉；`02` 平滑与相邻导向线混合，变为两片厚扫发；`03` 拆为 54 组离散长、中、短路径、缩短底发，前额开始出现错落的细束，但上部仍像较厚发帽。前三个版本均为 960×1120、64 samples 的检查稿，四视角都已实际查看。

`spatialfringe04` 用保存的 `Source/HairReconstruction/concert_fringe_control04.json` 实际重建：调整部分冠部和眉眼发束的末端，减少底发与改变根部扇出；该输入分支已执行，不是只提供未验证接口。1200×1400、Cycles/OptiX 192 samples、不去噪四视角均已查看。真实刘海落点和小幅波浪改善，但冠部仍偏厚，部分高光依旧连成宽片，侧后发偏规则，**没有达到参考级艺术质量**。结构验证通过仅检查有限坐标、正半径、贴图文件和哈希，没有做全量穿插或动画验收。

`spatialfringe05` 保留同一控制图，添加锁级空间起伏、更早汇聚及更多长发丝；四视角实际读图发现细绳状交叉和过窄发束，未选为展示基础。它也通过文件结构检查，进一步说明结构通过不能替代造型判断。

`editorial12` 由 `spatialfringe04` 生成，实际 1800×2100、Cycles/OptiX 384 samples、不去噪近景已完成并查看，结构验证通过。细发丝存在，但大片上部刘海、头顶小隆起与规则后颈仍可见；面部神态与衣物也仍是制作中状态。没有用生成肖像替代模型，不新增动作、绑定或游戏接入。

新空间路径可在控制图中改动并重新烘焙；隐藏 Blender 路径仅为可编辑证据，**不与密集可见发丝实时连接**。`--choppy-locks` 与 `--relaxed` 互斥；提供 `--design` 时不再重复扩展导向线。`--reference-cut` 需要 `--choppy-locks`，`--sculpted-clumps` 需要前者；不同造型方法保留，不能把细绳状版本称为最佳结果。

重建较柔和检查点（需本地许可资产、`layercut08` 基础工程，使用全新输出名）：

```powershell
# Blender --background --factory-startup --python Tools/author_concert_fringe.py --
# 新版本 layercut08 --choppy-locks --reference-cut --design Source/HairReconstruction/concert_fringe_control04.json
# Blender --background --factory-startup --python Tools/render_editorial_pose.py --
# 新展示版本 新版本 --portrait-only --hair-detail
```

源导向线、根部及侧后发为 Daniel Bystedt 改编，保留 CC BY-SA 署名/修改说明，所检查证据未注明许可版本。原始与派生大工程仍在本地。最新静态工作继续，未创建新 Release。

资源调查实际边界：UE5.6 MetaHuman 插件本地 `.uasset`/`.abc` 文件检索只确认毛发材质、纹理和工具管线，未找到可直接采用的完整发型几何。额外查看 Cem Yuksel 的 Hair Model Files 页面及 natural/dark/wWavyThin 预览；页面明确允许个人/研究用途并要求公开材料链接来源，未把它记作无条件游戏商用许可。预览为中长女性发型，没有下载几何或采用进角色，研究预览仅留本地。来源：https://www.cemyuksel.com/research/hairmodels/ 。

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
