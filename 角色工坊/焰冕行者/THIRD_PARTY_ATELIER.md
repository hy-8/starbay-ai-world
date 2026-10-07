# Atelier 角色检查稿的第三方资产署名

`regionalgroom15—19`和`editorial15`延续相同组件许可：前额控制13/14及独立细发束为项目原创，侧后是Ddr Rcs Royalty Free衍生，短支撑是Bystedt CC BY-SA衍生。18新增沿实际生长路径剪短/半径收尖，修改不改变来源许可。`anatomy01`在既有MakeHuman CC0人体网格上做项目原创局部雕刻；不改变保留毛发或服装的组件署名。上述版本均未通过参考级艺术验收，原/衍生几何留本地，只同步代码、原创控制、非几何清单与选定已查看检查图。

本轮 `regionalgroom10—14` 继续使用 Ddr Rcs 的 Royalty Free 侧后原生毛发衍生几何，进一步放松末端聚拢、加入小幅偏移与连续后颈弯曲；仍保留 Bystedt CC BY-SA 短支撑（来源证据未标明版本）。前额控制11/12与小块生根造型是本地原创；修改不将保留的授权组件转成CC0。原/衍生几何不进入本次Git提交，仅同步加工代码、原创控制与实际检查图。`editorial14`是静态展示摆姿，不是新绑定/动画或候选发布。

## 分层发片的实际拟合与转换研究

**Short hair card — Salman Ramezani**，BlenderKit Royalty Free，**非 CC0**。基础资产 ID `4793aff4-5e46-4902-a329-314731ebde09`，版本 ID `0a91297d-d3c1-43a6-9d38-d1f00c352f00`；来源哈希及改动见 `Source/licensed_layered_sources.json`，许可见 https://www.blenderkit.com/docs/licenses/ 。通过官方免费资产端点获取，原作者预览只用于研究，不能当作本项目成果。

实际试验保留原 UV/打包贴图，更新父级变换后烘焙并拟合；红色转换显式断开原粗糙度/镜面连接，减小不适用的次表面与涂层响应。随后在求值后的真实 UV 三角形内做重心坐标采样，以原灰度不透明度筛选，生成原生毛发；不是用生成肖像替代建模。分区组合选完整冠部发丝，保留原创长刘海、Ddr Rcs 侧后发和 Bystedt 短支撑，分别保留许可。

原文件、打包贴图、UV/几何提取记录、衍生 `.blend` 留本地；仅同步加工代码、非几何来源/检查清单与实际已查看渲染。所有试验尚未通过参考级艺术验收，新来源未作为优于 regionalgroom08 的造型采用，不发布独立素材包或候选 Release。

## 授权发片与原生发丝的新试验

**Female Shaggy Mullet Haircut — Ddr Rcs**，来自 BlenderKit / Blendkit，许可为 **Royalty Free，非 CC0**。免费获取不等于公有领域。

- 资产版本 ID：`ab9575fd-24cd-4790-a421-efa3f4c5e170`；基础 ID：`7e71d351-a00e-4188-82ef-54d0ade05423`。
- 官方许可：https://www.blenderkit.com/docs/licenses/ 。原文："Both allow you to sell higher-level-derivative works, but royalty free license doesn't allow to re-sell 3D models even if modified."
- 来源哈希、实际结构和使用清单：`Source/licensed_shag_sources.json`。36,274,728 字节原 `.blend` 含 424 个独立发片和打包贴图，打开时禁用自动脚本执行。
- 修改：真实男性头皮拟合、逐片根部调整、红色材质；从连接关系与 Factor 提取中心线，结合原 UV alpha 采样成原生发丝；分层剪短、波浪、宽度收尖、完整发束分区与后脑轮廓平滑。
- `assetshag01`、`nativeasset01/02`、`regionalgroom01—08` 及 `editorial13` 均为未验收试验；当前 `regionalgroom08` 仅选作实际几何检查点。
- 原发片、作者预览、贴图、提取的几何导向线、含该来源的 `.blend` 全部留本地；不作为独立发型资产或素材包分发。GitHub 仅同步本项目加工代码、非几何来源清单与实际角色渲染证据。

组合模型的原创前额来自角色实际头皮小块与本项目控制图；短头皮支撑依然是 **Daniel Bystedt Hair Styles 的 CC BY-SA 改编**，证据未注明版本。两种组件分别保留原许可，不能将整个组合写成 CC0 或全原创。当前没有新游戏包或公开社交发布。

> Side/nape hair adapted from “Female Shaggy Mullet Haircut” by Ddr Rcs, BlenderKit Royalty Free. Modified scalp fitting, geometry-to-fiber conversion, layering and taper. Short frontal support adapted from “Hair Styles” by Daniel Bystedt, CC BY-SA (version unspecified in inspected evidence). Preserve component attribution and modification notices.

## 实际采用的皮靴

**Shoes Biker Boots Male — Mindfront (Sweden)**，授权为 **Creative Commons Attribution 4.0 International (CC BY 4.0)**。

- 资产页面：https://static.makehumancommunity.org/assets/assetpacks/shoes03.html
- 下载包：https://files2.makehumancommunity.org/asset_packs/shoes03/shoes03_ccby.zip
- 许可：https://creativecommons.org/licenses/by/4.0/
- 许可依据：`mindfront_shoes_biker_boots_male.mhclo` 文件头明确写有作者和 `CC BY 4.0`。
- 本项目的改动：根据 MakeHuman 人体做重心插值拟合、对齐脚部站位和地面、转换 Blender 材质、使用原始底色与法线贴图。
- 用途：`atelier05` 及其后续选用版本，包含 `atelier09` / `editorial08` 的人物和图片。尚未用于新游戏 Release。

如果重新分发模型或公开发布这些图片，请一并保留以下署名和许可链接：

> Boots: “Shoes Biker Boots Male” by Mindfront (Sweden), CC BY 4.0. Adapted for body fitting, stance and Blender materials. Source: https://static.makehumancommunity.org/assets/assetpacks/shoes03.html — License: https://creativecommons.org/licenses/by/4.0/

下载包中还检查了 MaciekG 的皮靴，其文件头与包表述的许可不一致。该资产**没有用于本轮模型**，不随模型发布。包级别许可不能替代逐文件核对。

## 人体、皮肤、眼睛和基础上衣

沿用 MakeHuman 明确 CC0 的基础资产，逐项来源及哈希见 `Source/showcase_cc0_sources.json` 与此前来源清单。CC0 不要求署名，本项目保留来源记录。衣物面料节点、裁片和饰件为本项目制作。毛发需按具体候选区分：早期原创曲线与以下 Bystedt 改编资产不能混记。

## 本地发型新试验的 Bystedt 原生导向线

**Hair Styles — Daniel Bystedt**，官方页面及内置 `Hair demo file info` 标注 **CC BY-SA**，所检查证据没有注明版本，不能擅自填写 4.0 或改成 CC0。

- 官方页面：https://www.blender.org/download/demo-files/
- 下载：https://download.blender.org/demo/geometry-nodes/hair_nodes-female_hair_styles.blend
- 原始哈希和使用版本：`Source/official_groom_sources.json`。
- 改动：卷度/噪声节点、导向线分区剪短和刘海塑形、真实头皮转移、发根与穿插修正、红色毛发材质。`officialwave`、`hybridshag`、`layercut` 系列均包含该来源的改编毛发。
- 后续 `layerflow`、`rootflow`、`directgroom`、`targetfringe` 及对应静态展示工程仍包含该来源的改编毛发；新增局部冠部/发根梳理、节点旁路对照、目标头皮前额规划、独立末端和短支撑曲线。它们不是全部原创或 CC0 毛发，未发布为最终作品。
- `spatialfringe01—05` 及对应展示工程继续包含该来源的根部、短支撑和耳侧/后颈；前额改为独立空间 S 导向线，增加离散长短层次、重新剪裁、体积扰动和锁级起伏。改编毛发继续保留 CC BY-SA，证据未注明版本。隐藏导向线是可编辑设计证据，烘焙后的密集发丝须通过脚本重建。
- 改编毛发继续保留 CC BY-SA、作者署名与修改说明；工程内嵌 `ADAPTED_HAIR_CREDITS`。大型原资产和改编 `.blend` 目前保留本地，无新 Release 或社交发布。GitHub 的检查图仅是制作证据，不是已验收成品。

> Hair adapted from “Hair Styles” by Daniel Bystedt, CC BY-SA (version unspecified in the inspected source). Source: https://www.blender.org/download/demo-files/ . Modified guide lengths/shape, grooming nodes, scalp fitting and red hair material. Preserve attribution and ShareAlike for adapted hair.

## 测试后未采用的毛发模板

Tomáš Klecer 的 Hair Editor 功能资产包，官方功能包页面标为 CC0。

- 页面：https://static.makehumancommunity.org/assets/assetpacks/haireditor.html
- 许可依据：https://static.makehumancommunity.org/assets/assetpacks/index.html
- 哈希与本地检查记录：`Source/hair_editor_sources.json`。

拟合渲染没有通过检查，模板不包含在 `atelier09` / `editorial08` 中。不得把下载成功或模板存在写成高质量发型已实现。

## 本轮自然原生发流试验：Abhay Pratap

**Realistic Hair — Abhay Pratap**，BlenderKit官方元数据标记免费/validated，许可 **BlenderKit Royalty Free，非CC0**。版本ID `dc2bed6d-0cd8-43be-b94e-801688a39a18`，来源/哈希见 `Source/licensed_abhay_sources.json`，许可 https://www.blenderkit.com/docs/licenses/ 。

实际读取10个普通CURVE对象/9,870条POLY发丝；原女模人体未导入项目。拟合世界坐标、沿生长剪裁、原生纤维转换，比较完整发型与短底层后，完整发型均未采用；当前smoothflow02/editorial16只新增依据该原生发流方向、在实际角色头皮面积采样并沿表面传输的短支持发丝。原/衍生几何留本地，不重发独立发型资产；GitHub仅加工脚本、非几何记录和实渲证据。

> Natural scalp flow adapted from “Realistic Hair” by Abhay Pratap, BlenderKit Royalty Free (not CC0). Modified scalp fitting, actual growth-path cuts, native fibers, and surface-sampled short support flow. License: https://www.blenderkit.com/docs/licenses/ . Original/derived geometric assets retained locally.

最新组合另含Ddr Rcs Royalty Free侧后、Bystedt CC BY-SA短支撑与项目原创前额；不能给整个模型贴单一CC0许可。图片仍是未验收制作证据。

## 2026-10-04 后部造型替换补充

`originalsweep03`新增后部64,000条毛发的根分布/240造型路径，以及测量带区补充的36,000条短覆盖，均由项目在真实CC0人体表面原创生成。旧Ddr侧后组件隐藏保留，并未删除其来源/许可。仍可见Bystedt CC BY-SA短支撑和Abhay Pratap BlenderKit Royalty Free发流衍生短支撑；整个角色不能因此宣称完全原创或完全CC0。原/衍生几何保持本地，不作为独立发型素材包分发。

本轮只查看Radhe Rathod Stylized Hairstyle与Dr toxic Male Character Base Mesh with Hair Cards的官方预览以评估替代路线，未取得或导入其.blend，预览不作为项目渲染证据。原始检索元数据/签名下载地址不进入仓库。材质研究sheengroom01/02不改变既有几何或许可；原创短覆盖/后发替换也不改变其他组件归属。


## 原始 Sintel 粒子毛发的本地电影发流对照

原始Sintel / Blender Foundation / Durian，以及BenDansie的Sintel Lite 2.57b，CC BY 3.0。来源容器为Scthe `unity-hair` 固定提交 f183bb39d370cc8786d0f4fe649d72878b0cc167，哈希与获取边界见 `Source/SintelFilm/acquisition.json`；许可证据 `BLENDSWAP_LICENSE.txt`，官方 https://durian.blender.org/sharing/ ，许可 https://creativecommons.org/licenses/by/3.0/ 。

仅从SintelHairOriginal提取原始粒子发流，转为原生毛发、按目标头皮拟合并做分层剪裁、红色材质与有限离散身体保护。源/衍生几何留本地，sintelfit01—03全部未通过艺术验收。源灰头控制仅用于本地对照，未导入角色身体。

容器内Scthe代码、Unity着色器、Vincent Page发卡、NC-SA睫毛各有独立许可，不给整包声明CC BY或CC0；这些组件未采用，源自动脚本未执行。03保留旧原创前额，其他旧许可毛发隐藏但未删除，不改其归属。

> Hair flow derived from original Sintel (Blender Foundation / Durian), Sintel Lite by BenDansie, CC BY 3.0. Source container supplied by Scthe, unity-hair. Modified particle-path extraction, native curves, head fit, regional cuts and red hair materials. https://durian.blender.org/sharing/ — https://creativecommons.org/licenses/by/3.0/

## 免费 Fab 毛发的本地研究

Free Medium Layered HairStyle for MetaHuman - MHPKG — Muzammil。https://www.fab.com/listings/a87649a9-ae53-4d58-84b7-b4cdd47151fc ，Fab Standard License https://www.fab.com/eula ，NoAI，非CC0。用户于2026-10-05明确同意该免费资产的EULA，实际费用0。

本轮关闭源自动脚本，从 Blender 版提取已有粒子轨迹，转为原生曲线、在角色实际身体表面拟合根、延长侧后、改红色材质、做离散身体保护。普通脚本仅操作既有内容；没有送入生成模型、训练集或生成AI开发。04另导入原始方向性 Hair 材质并改变红色渐变。来源哈希与边界见 Source/FabMediumLayered/acquisition.json。

fabfit01—04均未通过目标艺术验收，稳定基础不变。原始头皮只在源控制图使用，没有导入人物身体；旧许可组件隐藏但未删除，03/04恢复的Bystedt/Abhay等短支撑仍依其原许可。原/衍生几何留本地，不出售或分发成独立发型包。GitHub仅审查代码、非几何清单和项目渲染证据；没有新的候选Release。

2026-10-05追加修改记录：Bystedt long hair的已改编layercut04毛发重新用于根区头皮重铺、实测负X冠部局部收低；原生源梳理求值后分区剪短对照；完整前额发丝组合；原创材质分支对照。均为本地CC BY-SA改编，版本沿用已检查证据的“未注明”，未变成CC0。原始资产、提取/派生几何留本地，未新增独立发型分发或Release。

2026-10-05 补充：Fab源用官方便携Blender5.1.2做只读版本控制，求值粒子/原素材渲染与4.5.9对照。Bystedt本地派生毛发试验包含实际发束分层、近似静态杆松弛、反向梳理、三个聚束Factor（其中两个连接上游轮廓）的缩放，以及Roll控制。既有CC BY-SA（版本未注明）、Royalty Free短支持和Fab Standard/NoAI边界保持；原/派生几何保留本地，没有独立发型包或新Release。


2026-10-05 nativebranches07/nativeaffine08/nativefront09/nativefrontwave10/nativefinish11/nativepart12 为现有Bystedt衍生毛发的本地几何/材质研究，CC BY-SA（原来源版本未指定）。Abhay/原创短支撑保留。Fab来源原文件不变，Standard/NoAI且非CC0，未送入神经重建。原/衍生几何与导向坐标不上传；仅加工代码、非几何聚合记录和角色实渲同步。目标未验收。


2026-10-06：nativeunderflow14 延展本地已授权Abhay短底发；15/17/18修改Bystedt主发（CC BY-SA，来源版本未指定），来源/衍生几何留本地。原Fab Standard/NoAI文件哈希保持，未用作神经重建输入。组件ID/聚合点深度仅梳理诊断，512样本图为实际Cycles+OpenImageDenoise，无AI肖像替代或作品验收。


2026-10-07：19—25加工已有本地毛发，不新增来源。Bystedt衍生曲线/所有blend仍留本地。Fab Standard/NoAI源未用作神经重建输入。Huang颜色输入相同不意味着跨模型物理吸收相同；原历史清单保留，另加解释。


2026-10-07：26加工已有Bystedt CC BY-SA短底发，来源许可版本仍未指定；27改原创后冠支持，28/29为原创小样。全部源/衍生三维几何仅本地，Fab Standard/NoAI源哈希保持且未输入神经模型。同步实际Cycles实渲与加工源码/聚合证据，无新来源或收费。


2026-10-07：31/33/34/37修改已有本地Bystedt主发，CC BY-SA来源版本未指定；分束索引与源/衍生几何不上传。32为临时分色实渲，不保存替换源。没有新增来源，Fab Standard/NoAI未输入神经模型。512样本近景为实际Cycles+OpenImageDenoise。


2026-10-07：39/40与44/45继续本地Bystedt衍生主发梳理；46/47只改材质，均否定。没有新增来源或许可；原/衍生几何和索引不上传。43为临时分色诊断；45近景为实际Cycles+OpenImageDenoise。Fab Standard/NoAI未输入神经模型。


2026-10-07：49/50/52/53/60/61/62为本地许可毛发的几何梳理，54/56/58/59为源真实毛囊上的补发小样；所有原/衍生几何和局部索引留本地。没有新资产/新协议/付费来源。Fab Standard/NoAI未输入神经生成或重建；BlenderKit候选为付费Full Plan、DeviantArt候选无明确复用许可且需登录，均未获取。61近景为实际Cycles+OpenImageDenoise，非生成肖像。


2026-10-07：64/65/68沿现有本地许可主发路径剪短，原/衍生几何仍本地，66只是临时组件分色，67是只读聚合诊断。没有新来源/协议/费用或神经重建；Fab NoAI未输入AI生成。68近景是实际Cycles+OpenImageDenoise，不是生成肖像。


2026-10-07：69—76沿已许可本地源制作材质/局部曲线对照。Fab/Bystedt原文件哈希保持，不新增来源/费用/协议，不把NoAI资产输入神经重建。源/衍生几何仍本地，76近景为保存工程重新载入的真实Cycles/OIDN结果；不发布试验角色。


2026-10-07：77—86为已有许可本地主发/曲线分段显示和传统几何加工；没有新增来源、协议、费用或神经重建，Fab NoAI源未输入生成模型。81/82/86衍生几何本地，86仅同步代码、聚合与实际Cycles/OIDN渲染；不发布新角色包。


2026-10-07：继续使用已授权本地Fab/Bystedt原生曲线做确定性分层与局部整束还原，源哈希保持；未再次下载、未将NoAI几何送入神经生成/重建。94为未完成WIP，原/衍生.blend与索引仅本地。详见SHOWCASE_BRIEF上冠分层记录。


2026-10-07：96/98确定性本地曲线修剪，已授权Fab/Bystedt源哈希保持；不向AI发送NoAI源几何。98是未完成继续版本；原/衍生几何仅本地，详见SHOWCASE_BRIEF本轮记录。


2026-10-07：101/102确定性毛囊曲线造型试验未采用；103只更换主发材质，全部几何保持，源哈希未改。103为未完成WIP；不将NoAI源/衍生几何上传至AI，几何仅本地。


2026-10-07：104—106确定性本地曲线雕刻，无新增第三方来源。106实际修改旧61刘海归属中的6038根；源哈希和其余组件许可保持，仍为未完成WIP。几何仅本地，不发送NoAI源/衍生几何至AI。


2026-10-07：107—112均为确定性本地原毛囊曲线编辑，无新来源/费用。112为中长碎发WIP，原Fab/CC0来源许可和源哈希保持，NoAI几何未发送至AI服务；原/衍生几何仍仅本地。


2026-10-07：113/115—117确定性本地曲线重塑、114临时实际分色，无新增来源/费用。原Fab/Bystedt源哈希/许可保持，NoAI几何未发往AI服务。117仍为未完成WIP，原/衍生几何仅本地。
