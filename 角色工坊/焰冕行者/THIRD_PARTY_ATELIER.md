# Atelier 角色检查稿的第三方资产署名

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
- 改编毛发继续保留 CC BY-SA、作者署名与修改说明；工程内嵌 `ADAPTED_HAIR_CREDITS`。大型原资产和改编 `.blend` 目前保留本地，无新 Release 或社交发布。GitHub 的检查图仅是制作证据，不是已验收成品。

> Hair adapted from “Hair Styles” by Daniel Bystedt, CC BY-SA (version unspecified in the inspected source). Source: https://www.blender.org/download/demo-files/ . Modified guide lengths/shape, grooming nodes, scalp fitting and red hair material. Preserve attribution and ShareAlike for adapted hair.

## 测试后未采用的毛发模板

Tomáš Klecer 的 Hair Editor 功能资产包，官方功能包页面标为 CC0。

- 页面：https://static.makehumancommunity.org/assets/assetpacks/haireditor.html
- 许可依据：https://static.makehumancommunity.org/assets/assetpacks/index.html
- 哈希与本地检查记录：`Source/hair_editor_sources.json`。

拟合渲染没有通过检查，模板不包含在 `atelier09` / `editorial08` 中。不得把下载成功或模板存在写成高质量发型已实现。
