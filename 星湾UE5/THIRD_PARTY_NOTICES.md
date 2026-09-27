# 第三方素材与工具

## Unreal Engine 与官方 Third Person 模板

本项目使用 Unreal Engine 5.6.1 和本机同版本的 Epic 官方 Blueprint Third Person 模板。2026-09-26 已复制并校验 246 个模板及共享资源文件，共 135,456,610 字节，涉及 ThirdPerson、Characters、Input、LevelPrototyping 内容及输入配置。文件级来源与 SHA-256 保存在本地 `Saved/template_import_report.json`。

这些模板角色、动画、蓝图、输入与共享素材由 Epic 提供，**不是项目原创资产，也未被本项目重新授予开源许可**。适用许可见 [Unreal Engine EULA](https://www.unrealengine.com/en-US/eula/unreal)。

- Git 仓库不提交官方模板 Content 或引擎安装程序；保留模板复制脚本与说明。
- Windows 打包游戏包含已烘焙模板资产及所需 Unreal 运行时对象代码，按 Epic 对产品分发的适用条款使用。
- Release 的可编辑源工程包若包含 `Content` 中的官方模板资源，其接收、修改和再分发仍须符合对应 Epic 许可。工程包的提供不将模板改为公共域，也不赋予超出原许可的权利。
- UE 编辑器、Epic Games Launcher、账号资料和本地工具缓存不打包进项目源工程交付。

## Poly Haven 材质

`cobblestone_floor_01`、`brown_planks_03` 使用 **CC0 1.0**。来源：[Poly Haven 许可](https://polyhaven.com/license)、[石铺地](https://polyhaven.com/a/cobblestone_floor_01)、[木板](https://polyhaven.com/a/brown_planks_03)。文件级 URL、许可标识及校验和保存在 `SourceAssets/Materials/material_sources.json`。

## 本项目资产与外部工具

原创街区几何、茶庭、夜市与增量植被由项目制作脚本生成。本项目未为整个工程新增开源许可证，不应把第三方资源的许可与项目原创内容混为一谈。

Blender、Unreal Engine、Epic Games Launcher 与可选 Windows SDK / MSVC 是外部工具，按各自许可使用。其安装程序不随本项目源资产包提供。本次 Blueprint 预编译 Windows 打包已在无可用 Windows SDK / VS C++ 工具链的环境中成功；未来新增需要编译的代码或插件时再准备对应工具链。

## 焰冕行者动态角色 v0.4.0

新使用 Epic Standard/Variant_Combat 中的 Blueprint 战斗逻辑、输入、动画接口和 Niagara burst 模拟，依照 Unreal Engine 相应许可使用。角色基础骨架与走跑跳动作参考本机 Epic Manny 模板，不属于 CC0。人体、面部形体和原生手指关节/权重来自明确标注 CC0 的 MakeHuman 资产；具体文件、来源与哈希见角色工坊的 THIRD_PARTY_NOTICES.md 及 Source 清单。程序织锦、造型、施法关键帧及火焰 Sprite 着色器为本项目制作。没有包含用户参考图片或原游戏标识。
