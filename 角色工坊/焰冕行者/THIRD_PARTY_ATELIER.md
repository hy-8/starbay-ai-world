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
