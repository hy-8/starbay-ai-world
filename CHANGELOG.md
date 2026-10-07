# 更新记录

## 2026-10-05 · Blender版本实证与源节点梳理对照（未完成）

Fab 原 hairstyle.blend 已确认保留。安装官方便携 Blender 5.1.2 于 D:\tools\Blender，ZIP 的官方 SHA-256 校验通过，旧 4.5.9 保留。4.5.9/5.1.2 在 frame_set(1) 后读取**求值粒子**，54,764 根的全部 8 键逐字节一致，共有标量设置一致，新增 API 属性仅 is_linked_packed。两张原素材同机位实渲均查看，仍为短梳发；8位RGB平均绝对像素差约0.00487。只能排除这次粒子/设置/控制视角的跨版本解释差异，不能泛化为所有Blender功能兼容。早期01数据探针读取了未求值的零键，不能作为几何证据；修正后的02要求非零求值长度，错误探针保留本地。

现有发型新试验全部为真实几何、独立版本：nativesublayer01两组浅分层、nativesections01六组更深分层均改善有限；nativerods01近似静态杆松弛令部分刘海垂到眼前，否定；crosspart01反向梳理出现交叠宽S片，否定。没有推广到整头，也没有称为物理动画。

源节点梳理：nativedeclump01改到一个未链接Factor和三处末端散开/偏移，两个链接Factor未改，不是完整的Factor对照。02通过Math乘法保留两个上游控制轮廓，并有效缩放三个Factor至原强度的55%；03同流水线保留原强度作配对，04只将Roll从0.18降至0.03。每版一张960×1120/OptiX96/不去噪实渲均已查看，仍有冠部团簇/刘海宽片，不采用作新成品。记录参数只能说明这些源控制试验，不能证明逐项复现了历史layercut04未记录的所有运行选项。

八个工程成对静态检查保留原141个网格/UV/形态键/变换，原生曲线有限值/正半径/贴图可用；短底发几何与nativecoverage05完全一致，前四个局部改梳工程的全部主发根也逐字节一致。源节点02/03/04的主发半径相同，根与位移差异另见native_source_pairs06.json。这些不是艺术验收或完整头发段/眼睛/服装/动画碰撞验证。

**目标仍进行，当前继续雕刻候选保持nativecoverage05，稳定备份napeunderlay02不替换。** 本轮没有合格新发型、动画/UE接入、新候选Release、社交发布或付费。源/衍生几何保持本地；仅同步加工源码、聚合记录和已查看的角色实渲。Fab与Bystedt源文件、稳定模型及六项无关修改哈希保持。


## 2026-10-05 · 原生波浪发根重铺、生成后剪裁与材质对照（未完成）

2026-10-05五视角补充复核：nativecheck04（1200×1400 / OptiX192 / 不去噪）五张均已查看，另一侧暴露了此前单视角看不出的鬓角上方明显头皮缺口，04没有通过完整造型检查。随后保存nativecoverage05，在相同完整主发型下恢复Abhay14,000、Bystedt23,657与原创后枕36,000根短底发，并统一为主发材质；没有新增实心头皮帽或重画贴图。

nativecoveragecheck05同规格五张均已查看：头皮裸露减轻，长侧后波浪/后颈保留；仍有前额宽带与冠部团簇，未达到参考级作品。当前继续雕刻候选为Exports/nativecoverage05/Ember_Regent.blend，稳定备份napeunderlay02不覆盖。七个试验成对静态文件检查通过，方向性材质03/04的可见曲线几何哈希与nativeroot03完全一致；另一个05成对检查证明主发与04、恢复短底发与稳定源的几何完全一致。原141个网格/UV/形态键/变换保持，可见原生曲线有限值、正半径和贴图可用性通过。只证明静态文件，不是艺术验收、全发丝段/服装/动画碰撞证明。六项无关文件和所有源/稳定工程哈希保持。


复核历史 layercut04 的实际四视角，侧后波浪与后颈长度比近期碎束更贴近参考，因此在保留 napeunderlay02 的全部身体/衣物网格的副本中重新导入其可见原生毛发，隐藏但保留全部旧毛发。没有修改或覆盖历史工程。

nativeroot01 先重铺正X侧局部12,737根发丝的前48%到实际头皮的柔和抬升层；看图后扩大到02的28,464根前/冠部发根。完整发梢与侧后波浪保留，根部硬拱减轻，但刘海仍有宽带。测量02最高发丝发现小冠部拱起集中在负X约-0.02m处，而历史压缩集中正X。03将这个实际局部拱起收低；四视角已查看，改善有限，不能称参考级完成。

新对照 postscissor02 不再改写源导向线，在原生梳理节点完整求值后再分区剪短，仅提高插值密度并在输出设置物理半径。它没有同样的硬刘海拱起，但额头裸露、后脑圆滑，单视角即否定为目标造型。01在读取链接的Radius输入时报错，无可用工程，日志保留；修复仅移除无须修改的源半径输入，改用输出半径。

nativecompose01保留postscissor02自然冠部与侧后，加nativeroot03完整前额发丝11,092根；四张草稿已看，未发现显著头皮断缝，但冠部/后脑更圆，否定为进一步基础。不是按发丝点拼实心外壳。

nativelobe03是03的材质对照，原生方向性Hair BSDF过暗/扁平，否定；04以原Principled分支混入25%方向性分支，略减偏粉高光并保留体积，仍只是检查候选。前两次材质脚本因枚举大小写与不存在的HairInfo Tangent输出提前报错，无模型；按实际API修复，不复用失败目录。方向性分支采用未连接的默认Tangent输入，没有声称显式读取不存在的输出。

目标仍进行：当前较值得继续雕刻的候选为nativeroot03及其04材质副本，仍有前额宽束、冠部团簇、侧后层次不足。稳定备份napeunderlay02不替换，没有艺术验收、动画/UE接入、新候选Release、社交发布或付费。所有毛发仍为实际可编辑三维，未用生成肖像替代。继续处理可见造型，不能仅靠更多密度、采样或压暗来达标。源/衍生几何仅留本地；加工源码、聚合清单与精选实渲同步。


## 2026-10-05 · 完整发丝核查、实际头框与局部梳理对照（未完成）

已确认用户下载的 Fab hairstyle.blend 在指定 Source/FabMediumLayered 目录，原文件哈希保持。逐根读取 54,764 根粒子的全部 8 个保存键，与前缓存根/尾比较，差异最多 3.73e-9m；三组长度中位数约 25.5/28.7/31.5mm，没有漏掉隐藏长尾。它仍不匹配参考的中长碎发。

按实际求值头部校正 Fab 的缩放/平移，fabfit05 发根修正中位数约 2.8mm、90%约 8.7mm，原试验分别约 4.8/21.2mm。但三分之四实渲依然是短梳发，不采用；根部贴合改善不能证明造型合格。

原创 cubic Bézier 两束小样 bezierlock01—03 均已读图，03 近景能看清细纤维；组成 44 束/22,000 根的 cubicshag01 后，四视角显示分离条带、耳后拱形和冠部空隙，明确否定。隐藏控制曲线是烘焙证据，不是实时连接。不能把两束成功迁移为完整发型成功。

转回稳定 napeunderlay02 的完整覆盖作局部试验：settledshag01 轻收侧面、统一材质；02 同几何色素对照偏橙棕，否定；03 在01基础上仅沿侧后发丝逐段保长弯向下方、加根部相干缓弯。03四张实际草稿已查看，外翘减少且覆盖保留，但冠部仍厚、后脑仍圆，是局部研究，不替换稳定WIP。五视角较高采样结果另外记录。

八个候选与稳定基础做成对静态检查，原141个网格的几何/UV/形态键/变换保持；可见原生曲线有限值、正半径和贴图可用性通过。这不是艺术验收，也不是发丝段、服装、眼睛、动作的完整碰撞保证。稳定WIP、Fab源文件及六项无关文件哈希保持。原/衍生几何留本地；同步代码、聚合记录与精选实渲，没有新付费、AI肖像替代、动画、UE接入、候选Release或社交发布。目标仍进行。


## 2026-10-05 · 免费 Fab 毛发的原始对照与目标适配（未通过）

用户当场同意接受 Muzammil 免费发型的 Fab EULA。浏览器接受后页面显示 Done，但下载事件接口卡住且未交付本机路径；用户随后将 `hairstyle.blend` 放入 `Source/FabMediumLayered`，已实际读到并核验 SHA-256。费用 0，Fab Standard / NoAI，非 CC0；源和衍生几何仅留本地。

实际读取三组共 54,764 条粒子毛发，源文件 Blender 5.1，关闭自动脚本，用 4.5.9 原样读取完整 33 点缓存并重建原生 CURVES，未覆盖源文件。fabcontrol01 两张转换控制图与 fabparticlecontrol01 两张原始粒子控制图都已查看。源多数路径约 2–4 厘米，整体是顺直偏梳的短层；原始粒子粗细和方向性 Hair BSDF 与小半径 Principled 转换控制的光照响应不同，不能把转换图差异全算成造型本身。

fabfit01—04 的十二张真实角色草稿均已查看：960×1120、Cycles/OptiX 64 samples、不去噪。01 直接拟合成贴头短发；02 保留刘海并延长侧后，隐藏底发导致露头皮；03 恢复 Bystedt/Abhay/原创短覆盖并保留更多耳前根，覆盖改善但后方仍圆、直、蓬；04 只换新发型的原始方向性材质并改红，降低粉色雾感，却出现新旧组件明暗不一致，圆后枕未解决。**四版均不采用为新作品基础，稳定 WIP 仍为 napeunderlay02。目标未完成。**

配对检查确认每版原 141 个网格的几何/UV/形态键/变换保持，新曲线有限、半径为正、贴图可用；03/04 新毛发几何哈希完全一致，材质比较没有变形。范围是文件不变量，离散头部保护也不是全量穿插或动作验证。没有新的动画、UE 接入、候选 Release、社交发布或付费服务。面部/衣服仍需打磨；来源资产成功下载不等于达到参考作品质量。

源码、非几何来源和精选实渲同步 GitHub，原/衍生几何和诊断路径缓存保持本地。下一轮不能直接重跑短顺直资产的拉长参数；先找出能改变松散分层轮廓的方法，并用少量原始造型对照验证。详见 HAIR_RECONSTRUCTION_NOTES.md 与 Source/FabMediumLayered/acquisition.json。


## 2026-10-05 · 显式主束与电影毛发适配试验（仍未通过）

稳定研究基础仍为 `Exports/napeunderlay02/Ember_Regent.blend`，本轮没有替换。先画31条完整空间主束，authoredrear01/02/03的九张真实草稿均已查看：宽根片形成棉团，薄截面传输出现尖结/硬折，头部包络又合并成平滑假发片，三版均否定。

随后改用有许可证据的原始Sintel粒子毛发，来源为Scthe混合许可容器的固定提交；只提取SintelHairOriginal，不导入其他发卡、Unity材质、NC睫毛或脚本。原文件Zstandard压缩、SHA与Git LFS一致，自动脚本关闭。旧粒子短子发缓存长度不同，第一烘焙检查报错；按每根真实连续点数分别重采样后，control01得到11,628条、control02得到57,228条。四张实际源头模渲染均已查看，它们不是项目角色成果。

sintelfit01/02/03的九张角色实渲均已查看：960×1120、Cycles/OptiX64 samples、不去噪。01/02减少旧硬块但顺直帘和圆后枕仍不合参考；03组合旧前发出现前冠衔接空隙，明确否定。各版保存原生可编辑CURVES，根投影/整根位移和离散身体保护不是实时毛发驱动或全量穿插保证。网格/UV/形态键/变换与稳定源成对检查另存，结构通过不能证明艺术通过。

**目标未完成，模型仍需打磨；不采用本轮任一版本作为新作品基础。** 这轮证实成熟资产的造型匹配比单纯增加密度重要。下一步先选与目标相近的男性中长层次毛发，核对源造型实渲与许可，再做少量针对性拟合；不要再以顺直短发或失败的程序化团簇反复扫参数。面部与服装仍未达到参考质量。源码/清单/精选检查图同步，原/衍生几何留本地；保留旧工程及六项无关文件，没有新付费、AI肖像替代、动画、UE、候选Release或社交发布。


## 2026-10-05 · 切线弯曲分束与后枕体积对照（未通过作品验收）

- 实际试验切线旋转分束、分长短层、开放末梢、头皮法线后枕收拢及下层S弯/长度恢复；五版全部保留。五视角05仍有冠部尖结/硬束和另一侧折痕空隙，未采用；当前稳定WIP仍napeunderlay02，目标未完成。
- 原生后发隔离图定位主要圆体积；保留28片底层网格，不把有限对照称作全层剥离。05结构检查通过，20k同样本头皮潜在标记5→0，非艺术或完整碰撞保证。
- 同步源码、清单与精选实渲；本地保留模型和构造几何，六项无关文件哈希保持。没有新资产/付费服务、AI肖像替代、动画、UE、候选Release或发布。

## 2026-10-05 · 原创后颈透明底层与未采用的上层塑形

- 根据真实长发密度/长度诊断，新增28个原创可编辑细窄发片与方向UV/程序化透明材质。第一版塑料条感被否定，napeunderlay02暗哑光透明改善有限，五个192 samples中性图已查看；所有既有原生毛发与身体/衣物/UV/面部形态键保持。
- 上层剪裁扩到41003条并尝试220个局部收束，五视角和384 samples真实editorial24近景揭示刷毛感；两版完整三次曲线侧/背仍圆帽/平行帘，均否定，没有把结构通过当成艺术完成。下一轮基础仅为napeunderlay02，目标继续。
- 源配对检查明确声明并核对新增28个网格，确认原对象不变。失败方案的有限头皮/衣物样本归档，不能替代全量面穿插/动作或艺术验收；新增发片的静态展示跟随同一头部矩阵。
- 源码/审核和精选原生检查图同步；模型/来源几何留本地，保留旧工程和六项无关文件。无新付费服务/外部资产、AI肖像替代、动画、UE、候选Release或社交发布。

## 2026-10-05 · 后颈包络收拢与共享冠部空间变形

- 改用个体发丝连续塑形收拢悬空后颈，保留长短/曲率差异；napecage01过猛，02限制位移和高度。前冠共享空间场替代各束相反大波浪；01头皮抽查出现新接触，被否定，02按源皮肤余量限制。
- crowncage02五个192 samples原生中性检查图已查看。后颈悬空减轻、前冠有小幅变化，但圆后枕、薄后颈及另一侧小弧仍在，尚未达到参考质量。源配对结构/完整毛发半径和刘海区域哈希通过。
- 新增源配对限定头皮抽查：冠部02为20000点0→0潜在标记；后颈为20000点1→1同索引，衣领12000点0标记。离散诊断不代表全量穿插或动作安全。保留失败证据、全部旧工程和六项无关文件。
- 保存为可编辑烘焙CURVES，没有新增交互网格笼或实时导向驱动。源码/审核/精选渲染同步，无付费生成、新资产、动作、UE、候选Release或社交发布；目标保持进行。

## 2026-10-05 · 刘海内部偏移清理与独立中心曲线

- 从实际原生发丝读取细束分布，定位旧末端扩散；保留所有毛囊，重建细束内部偏移与独立长度，再拟合完整三次曲线调整父束手柄。fringefield02五张192 samples、不去噪的实际检查图均查看，细梢和眉侧分束改善，整体仍未达到参考质量。
- 源配对检查增加前冠/刘海独立区域哈希与真实细束分布记录：02前冠6160条完全保留、刘海末端90%分布距离中位数约10.86→5.46mm；检查不是艺术评分。softcrown01只改前冠，刘海21600条完全保留，但三分之四暴露新交叉圈结，保留失败版本而不采用。
- 渲染工具可在核对同一源SHA和实际图像SHA/分辨率/采样后复用已检查的另一侧图，节省重复渲染；本次失败冠部五视角验证使用该机制。最终刘海候选五张均单独实渲。
- 未重做未受影响的后颈接触抽查。源码、审核与精选实渲同步，六项无关文件和历史模型保留；无新许可资产、付费生成、动画、UE、候选Release或社交发布。目标继续。

## 2026-10-05 · 发束隔离诊断与完整冠部路径重建

- 保留冠部端点转向、仿射转向、自由梢和后颈展宽的实际失败小样；较高后枕根加入长后颈层，比平均展宽更能保留重叠。全部旧工程保留。
- 新增分层侧面检查，实际定位左侧顶部圈结主要在旧上部后发；前冠重建不足以修复它。改用真实头皮附着段/自由重力出口，替换旧中段偏移，加入连续高度过渡、侧向聚束与长短层。
- crownflow04真实模型及crownflowcheck01五张192 samples实渲已检查。明显左侧圈结减轻，层次增加；另一侧交叉细弧、前额宽高光及薄后颈仍在，目标继续，未作为成品。源配对结构通过，限定后颈12,000点潜在衣领接触标记0，不代表全量穿插/动画安全。
- 同步源码、审核清单和精选实渲；六项无关改动及本地许可几何保留，没有付费生成、新动画、UE、候选Release或社交发布。

## 2026-10-05 · 中后脑空间发流、自由后颈与领口抽查

- 重画原创后发空间中心路径，使中层较早离开头皮，加入松散波浪及从毛囊深度自由垂落的后颈。spatialrear08四视角与oppositegroom05另一侧已看，192 samples、不去噪。中后脑圆壳和硬转弯减轻，宽冠部/细稀后颈/规则感仍在，目标继续，未当成品。
- 新增真实衣物背面包络约束、只读限定区域后颈抽查。12,000点潜在接触标记从03的246降至04/06/08的0；开口衣物最近面法线抽查不代表全量穿插/动作安全。06/08源配对根、根半径、网格UV/形态键/变换及未改毛发不变量通过。
- 保留前额三次未采用波浪试验、硬转弯后颈对照及全部旧工程。同步源码、限定检查及精选实渲；六项无关修改不动，许可几何留本地，无付费生成、动画、UE、候选Release或社交发布。

## 2026-10-05 · 原生发丝错层剪裁与上部羽层转折

- 新增实际弧长剪裁、相邻根分冠部小束、细梢重生。01暴露刘海过短和个人剪裁未作用于中心路径的问题，保留失败稿；修复后02只做后发小样，剪短仍圆。03只缩短底覆盖发，外轮廓几乎不变，未选为基准。
- 04改变上部外层末段的真实空间走向，使其离开头皮、向外向上形成碎发轮廓；05复用04，只修改前发且保留长度。05四张192 samples全质量与真实另一侧oppositegroom03均实际查看，无去噪；仍宽冠部、圆后脑/重复条纹、细条后颈，目标继续。
- 复用结构检查器增加声明源哈希与实际全量根/根半径/变换、未修改网格UV/形态键/毛发哈希对照，04/05均通过；有限值、正半径、贴图通过，不代表艺术或全量穿插/动作验收。
- 保留历史及六个无关修改，源码、检查记录和选定实渲证据同步；没有付费生成、新动画、UE、近景展示或候选Release。

## 2026-10-04 · 真实发型隔离与面部形态键精修

- 查看八张当前后发/冠部隔离图；原创后发增加长度变化和真实深度起伏，三导向插值反而成圆滑壳，保留失败对照。抽查1157个实际前额根间距约0.5mm，排除该样本的根部浮空推测。
- 新增沿实际人体法线的选定前发中心路径间距拟合，保留真实根/截面；frontalenvelope03全质量四视角、editorial19近景和oppositegroom02另一侧已查看，眉侧悬空减轻，仍宽/规则。
- 从真实眼眉位置制作五个可编辑相对形态键，眉卡回投实际表面、睫毛跟随。portraitsculpt02的192 samples四视角、editorial23的384 samples近景均查看，面部更集中但高清改善温和，整体未达参考。
- 修复展示姿势只改网格不改形态键的错位；保留editorial20失败稿。增加形态键有限值与成对拓扑/UV/眼球/可见毛发哈希检查，均通过；采样眼睛投影面积减少约27%，不代表全量穿插或动画验收。
- 同步实际渲染证据、源码与检查记录；源/衍生几何和无关修改保留本地。目标继续，未新增UE、动画、候选Release或社交发布。

## 2026-10-04 · 分区剪裁诊断与原创侧后毛囊重建

- 保存referenceflow01—05、sheengroom01/02、editorial17和间距压缩的实际对照。保留完整长底发能遮皮但仍圆；降低材质粗糙度不改几何，局部压低间距改善有限，均没有当作完成。
- 新增真实弧长分区剪裁与独立面积采样短覆盖。强剪裁露皮，按猜测采样仍失败；实际侧面相机/人体BVH射线定位带区约z1.77—1.79m，修正下边界后rootlayer06四视角恢复覆盖。保留失败版本与实际求交证据。
- 新增原创后发重建：真实头皮新毛囊、不规则造型分区、自由下垂后颈，隐藏旧Ddr侧后。01过短/分开、02尖尾，03保留下部根分布并加入轻微空间弯曲，240路径、64,000新实际原生发丝。
- originalsweep03全质量四视角192 samples及editorial18近景384 samples均实际查看、无去噪。耳侧/后脑较旧壳收窄；宽冠部、后部规则感、直尾及脸服差距仍在，目标继续。结构通过不等于艺术/完整穿插/动作验收。
- 同步源码、审核清单和选定实际渲染；源/衍生几何及搜索signed URL留本地，保留无关修改，未新建候选Release、UE接入或社交发布。

## 2026-10-04 · 自然发流替代、面积采样头皮补发与空间重梳

- 六张实际冠部/刘海/支撑/后发隔离图确认重叠来源；分束强剪裁、温和剪裁、降低前额根部均检查四视角，效果和失败明确保存。
- 合法取得Abhay Pratap免费Royalty Free原生发丝，核对世界变换/哈希；完整剪短发型仍偏中分波波头，低根漏剪修复后组合刘海仍圆且接缝明显，未采用。授权原/衍生几何及signed URL留本地。
- 在真实头皮按三角面积新增14000条短底发，沿自然源方向做表面传输；82束原创前发用实际空间三次曲线重梳，所有原根保留。新版smoothflow02全质量四视角192 samples及editorial16近景384 samples全部已看、无去噪。
- 顶部露皮与前额交叉减轻，宽冠部、偏圆侧后、脸服通用感仍在；结构验证通过不代表艺术/完整穿插/动画验收，目标仍进行。模型及历史版本留本地，源码/原创控制/非几何清单/实渲证据同步，未新增UE、动作、候选Release或社交发布。

## 2026-10-04 · 独立细发束、密度对照与沿生长路径剪裁

- 同一控制图前额密度33,400降至20,040条仍有宽片，排除“仅增减发丝就能完成”的判断；原创控制13/14改短侧向冠部与独立长短眉侧细束，缩小真实根部小块和体积截面。
- 完成regionalgroom15—18草稿四视角检查，新增沿实际生长路径剪短侧后的arc-scissor对照；18轮廓不理想，未采用。新增实际脸部雕刻anatomy01，四视角草稿已看，仍通用数字人，未代替当前基准。
- 当前regionalgroom19四视角1200×1400、192 samples不去噪，editorial15近景1800×2100、384 samples不去噪均实际查看；眉侧细束改善，宽冠部/交叉/局部小缝与脸服差距仍在，目标继续。19/15/anatomy01结构检查通过，不代表艺术或完整穿插/动画验收。
- 保留全部历史及用户无关修改，同步本次源码/原创控制/选定真实渲染；授权几何留本地，未新增UE、动作、候选Release或社交发布。

## 2026-10-04 · 放松发尾与成对窄冠部路径

- 添加实际毛发末端截面/偏移处理，独立随机数保持既有整束位置；首轮.65聚拢偏蓬松，改.85与半幅偏移，加入连续下后颈S弯，保留全部试验。
- 新原创控制11先加稀疏短层；控制12进一步用28条窄成对路径替换14条冠部/羽层路径，保留18条眉眼/鬓角路径。处理原生CURVES，统一可见毛发粗糙度，不用生成肖像代替模型。
- 实际查看regionalgroom14的1200×1400、192 samples不去噪四视角，及editorial14的1800×2100、384 samples不去噪高清近景。两个工程结构检查通过；发尾更柔和，但冠部仍连片/规则，脸服仍有差距，艺术验收未通过，目标继续。
- 同步加工源码、原创控制及真实检查证据，许可保持Bystedt CC BY-SA / Ddr Rcs Royalty Free；大型源/衍生几何留本地，保留无关修改，不新增UE、动作、候选Release或社交发布。

## 2026-10-04 · 更换分层发片方法及真实毛发采样对照

- 保留 Ddr Rcs 原贴图做 texturedgroom01 对照；原创冠部细截面 spatialfringe11 仍条带，强化转折 spatialfringe12 产生交叉/沟槽，未采用。
- 实际获取并检查 Salman Ramezani Short hair card，记录 Royalty Free 非 CC0 来源与哈希；更新父级世界坐标后拟合，修正原粗糙度/镜面连接覆盖参数的问题，保留透明度贴图与所有原工程。
- 新增 UV 三角形重心坐标/灰度不透明度采样转原生 CURVES；调整发根判定、刘海落点与毫米波浪，单独发型仍偏圆帽，未采用为改善。
- 新增完整冠部发丝分区组合，layeredhybrid02 四视角 1200×1400、192 samples、不去噪均已实际查看；仍有冠部团簇和沟槽，未认定优于 regionalgroom08 / editorial13。目标继续，未达到参考质量。
- 同步处理源码、非几何许可/验证清单及真实检查图。授权原/衍生几何和作者预览留本地；保留无关未提交修改。不新增候选 Release、UE 接入、动作或社交发布。

## 2026-10-04 · 授权发片转发丝与完整发束分区

- 隔离渲染前额、短支撑和保留区域，定位冠部宽片主要来自自绘前发；修改为实际头皮小块生成长发，完成 spatialfringe06—10 与原创控制图07—09，均保留历史版本。
- 检查并使用 Ddr Rcs 的 BlenderKit Royalty Free 发片，记录来源/哈希/许可；按连接关系、Factor、原 UV alpha 提取实际导向线并转为原生 CURVES。原/衍生几何全部留本地，不作为素材包同步。
- regionalgroom01 按发根删束造成后脑裸露，否定；02 采用完整发束走向恢复覆盖；03—06 的剪裁、卷度与体积调整仍有硬折线或过圆轮廓；07/08 用连续空间过渡消除压缩阈值的横向折线，分开发尾长度。
- 实际查看 regionalgroom08 的 1200×1400、192 samples、不去噪四视角，以及 editorial13 的 1800×2100、384 samples、不去噪高清近景。两工程结构检查通过，艺术质量仍未通过：冠部过顺滑、侧后方偏直，脸服仍需独立精修。
- 同步本轮制作源码、非几何来源、原创前额控制和所选渲染/检查证据；保留无关未提交文件。目标继续，没有新动画、UE 接入、Release 或社交发布。

## 2026-10-04 · 独立空间发束与长短层次试验

- 复核 targetfringe05—07：增加体积、按真实眉毛位置放长刘海及分层裁剪，仍形成厚重规则前帘，未采用为作品。
- 新增 author_concert_fringe.py，将前发拆成独立空间导向线、短头皮支撑和保留耳侧/后颈三组原生毛发。spatialfringe01—05 四视角均实际检查；原始空间导向线过卷，平滑后过厚，分层后改善落点，过强聚束则出现细绳状交叉。
- spatialfringe04 以独立 JSON 控制图实际重建，输出 1200×1400、Cycles/OptiX 192 samples 不去噪四视角，结构验证通过。它仍有较厚冠部、片状高光和不足的自然层次，尚未达到参考级质量。
- 完成并实际查看以该候选为基础的 editorial12 高清近景：1800×2100、384 samples、不去噪；结构验证通过，但冠部、后颈及脸服仍需精修，不能作为最终作品。
- 新版保留 Bystedt 改编根部与侧后发，继续按 CC BY-SA 保留署名和修改记录。MetaHuman 本地检索只找到毛发材质/工具，未确认可用发型几何；额外研究发型页面没有采用进角色。
- 所有候选均使用新目录，原工程保留；没有新游戏接入、动作、Release 或社交发布，目标继续。

## 2026-10-04 · 目标头皮前额造型与方法对照

- 对粗发丝、局部发根、卷曲/聚束、预设分缝与附加发束分别进行实际几何对照，保留失败候选。绕过原节点的版本仍未合格，没有把推测写成已解决的唯一原因。
- 新增直接在角色实际头皮规划前额走向的脚本，保留耳侧/后颈、设计长短和转折、补短支撑毛发，保存 targetfringe01—04。最新全质量四视角已实际查看，仍有片状感和相似曲线，未通过参考级艺术验收。
- 原生曲线和编辑工程保持本地，隐藏代表路径明确为证据而非实时 Groom 驱动；保留 Bystedt CC BY-SA 署名与改编记录。
- 完成并实际查看 editorial11 的 1800×2100、384 samples 不去噪近景；模型与展示工程的文件结构检查通过，仍有宽带式前额与通用数字人神态，不能代替艺术验收。
- 同步所选真实渲染、脚本和检查记录；保留用户既有改动，目标继续，不新增候选 Release、游戏接入或动画。

## 2026-10-04 · 原生导向线分区剪裁发型

- 实际拟合并检查 Bystedt 官方 curly hair；软化与混合原创束状发丝的尝试仍不合格，保留全部试验与失败证据。
- 更换为 long hair main：先剪裁、塑形原始导向线，再运行原生分束/插值/噪声；制作 layercut01—04，改善耳侧、后颈层次和偏分刘海，四视角已实际检查。
- layercut04 文件结构检查通过；上部发丝的 20,000 点间距抽样未发现头皮穿插，未把样本检查扩大为全量或艺术验收。
- 输出并实际查看 editorial10 的 1800×2100、384 samples 不去噪真实近景，保留原生毛发及编辑工程，仍是作品打磨稿。
- 更新 CC BY-SA 作者、来源和改编说明。候选仍需精修，不发布新游戏、动作或候选 Release，目标继续。

## 2026-10-04 · 自由导向线发型与原模板失效诊断

- 对旧 Hair Editor 缓存做原头模对照；发现辅助头皮几何风险，沿整条发丝使用真实 body 头皮场转移后仍不能达到目标。保留失败结果，未把算法运行成功当作合格造型。
- 新增可编辑的独立空间 S 形头顶、刘海、耳侧及后颈导向线；按区域裁剪支撑底发，调整长短层次和毛发中段/发梢粗细。保存 freeformrock01—06，最新候选四视角已实际查看，结构检查通过，但仍未通过参考级艺术验收。
- 核对并下载 Daniel Bystedt 的 Blender 官方 Hair Styles 示例；记录官方页面、内置 CC BY-SA 许可与哈希，关闭源文件自动脚本执行。仅检查资产结构，尚未采用或分发。
- 同步本轮源码、来源和真实渲染证据；保留用户既有改动。没有新增动作、UE 接入、社交发布或候选 Release。

## 2026-10-02 · 红发本地三维重建与原生 Groom 实验

- 测试头皮对应拟合、原创曲线梳理、明确 CC-BY 作者发片与发片转原生发丝；逐项记录实际失败结果，没有把运行成功写成造型合格。
- 配置 D 盘独立 Hunyuan3D-2mini shape-only 环境，完成真实图生三维网格导出；通过 mmap/meta 参数赋值及组件 CPU 卸载适配 16GB RAM / 8GB VRAM，本次未运行全量贴图管线。
- 保留原始输入/网格，清理悬浮小碎片，修正后脑贴合；沿局部曲率和偏分梳理场生成原生 CURVES，隐藏实心块状网格，逐条裁短底发、回贴发根、释放发梢并加入独立斜向刘海。
- `hairrecongroom05` 通过几何/毛发半径/贴图结构检查，中性四视角已实际查看；仍有卷翘生硬和层次过于规则的问题，未达到参考级作品质量。目标仍继续，不发布新游戏、候选 Release 或社交平台作品。
- 同步制作脚本、明确的许可与输入来源记录、实际检查证据；AI 发型输入不当作最终 3D 作品图，大型模型与权重留在本地。

## 2026-10-02 · 角色原生毛发与分件服装方法试验

- 按用户允许更换方法的要求，测试原生 CURVES 毛发、人工梳理模板拟合和授权皮靴；人工模板与若干表层发束没有通过实际渲染检查，未纳入选定版本。
- 保存新的 atelier09 模型与 editorial08 四视角 Cycles 192 samples 检查图；调整分层毛发、长外套裁片、织物表面、立领、肩部皮革、腰带和皮靴，补充原生毛发静态姿势变换。
- 逐文件核对 Mindfront 皮靴 CC BY 4.0 许可并补充署名。结构检查覆盖有限值、毛发半径、贴图和输出哈希；源工程与旧版本均保留。
- **仍是未通过艺术验收的 WIP**：发型、面部神态、衣物褶皱与参考存在明显差距；不发布新游戏或候选 Release。MetaHuman 仅做依赖探查，没有声称已接入。

## 2026-10-02 · 绯序角色静态效果图检查稿

- 根据用户新的演唱会风格参考，优先打磨实际 Blender 模型与静态图，暂停这批候选的 UE 接入和成品 Release。
- 增加 CC0 资产提取和来源记录、连续外套/肤质基础、眉毛/发片与细发丝、贴合胸口的项链、内搭穿插修正；保留全部旧试作与已发布 v0.4.0。
- 保存 concert14 模型及 editorial03 展示工程，输出全身、半身、近景、背面 Cycles 图片，加入可编辑的静态展示姿势和弧形摄影棚。
- 本轮是 WIP 检查稿，未达到参考图质量；姿势由几何变形得到，不是已验证的动画、布料或游戏角色。发型、面部神态、衣物褶皱仍需继续打磨。

## 2026-09-27 · 焰冕行者原生动态候选 v0.4.0

- 将 v14 静态造型制作成 rig04 骨骼模型与 motion05 七项动画；保留原候选和发布，修正最近邻手部蒙皮拉伸，增加原生手指与独立裙摆骨骼。
- UE Ember_v04 接入原生 CharacterMovement、动画蓝图/混合空间、施法 Montage 与 Niagara 动画通知；普通走路、Shift 冲刺、空格起跳、Q 施法、施法恢复和重复施放通过 PIE 输入映射测试。
- 修复材质副本未落盘导致的灰模；重建材质响应、固定曝光与试炼场熔岩材质。LOD0/1/2 分别为 527,837 / 146,241 / 77,689 个 UE 渲染顶点。
- 将父子蓝图的移动 Input Action 拆开，消除双重输入；关闭战斗父类的第二台相机，保留 FollowCamera，实际检查原生第三人称镜头。独立 Windows 包与最终截图的证据见 `Validation/ember_delivery.json`。
- 增加试玩/架构说明、输入和镜头回归脚本、依赖收集、ZIP CRC/哈希打包工具，区分 Epic 模板许可与 MakeHuman CC0。生成的 AndroidFileServer 设置不进入源码或发行包。
- 尚未达到参考级角色质量；披风/发丝仍为烘焙动画，地面法阵与服装蓄能尚未接入原生技能，NPC/Qwen/任务没有迁入 UE。

## 2026-09-27 · 焰冕行者造型与材质层次精修 v0.3.0

- 新候选位于 `角色工坊/焰冕行者/Exports/v14`，保留 v11、v04 和历史发布。通过 v12 草图、v13 与 v14 实际渲染比较调整造型。
- 收紧唇形并微调面颊/下巴，重新组织分束白发与散发；深红主料替代大面积满铺织锦，把织锦集中到领襟、袖口、下摆和披风边饰。
- 减少窄披风分片，重塑宽幅曲面和褶皱，增加太阳纹章；饰线改沿局部表面法线偏移。细化王冠卷纹/爪镶/珠边、肩饰和内搭包边；绕颈项链改为拟合真实颈部表面。
- 保存六视角真实渲染及可编辑 Blender 工程，导出静态 GLB/FBX；470 个网格、4,564,612 三角形。此轮为展示造型精修，面数增加，不是游戏性能优化；仍需面部精雕、服装模拟、低模/LOD、绑定及 UE 实机验收。
- 增加单版本打包脚本，核对模型哈希与 ZIP CRC，排除参考图、日志、旧候选及 Blender 备份。大型文件通过新 Release 附件保存。

## 2026-09-27 · 焰冕行者红金织锦精修 v0.2.0

- 保留 v04 初版，通过 v05—v11 的多轮实际渲染检查重做头发、面部形体、服装和披风；当前候选为 `角色工坊/焰冕行者/Exports/v11`。
- 增加 15 个明确 CC0 的面部目标及出处校验，调整眼睑、鼻梁、唇形和头部姿态，增加眉毛/睫毛、虹膜和细曲线白发。
- 重建开襟内搭、长摆、褶袖、肩饰、腰链与绕颈项链；披风增加宽幅流动面料、细长分片及静态火焰薄片/余烬。
- 通过内置 image_gen 创建原创红金织锦底色，实际映射到服装 UV；用 Cycles 烘焙 ORM 与法线并嵌入 Blender/GLB，保存提示词与资产来源。
- 输出六视角真实渲染，包括 2560×1600 展示图、正背面、近景和关闭火焰/辉光的素光检查。人物图均由本次 3D 工程渲染。
- 静态导出包含 319 个网格、4,053,148 三角形，主要面数来自独立发丝。该展示模型不适合直接替换实时游戏角色；尚需低模/发片或 Groom、精细肤质、骨骼蒙皮与动态布料验证。没有把模型导出视为 UE 游戏接入完成。

## 2026-09-27 · 工程恢复与焰冕行者静态角色初版

- 根据用户要求把活动工程恢复到 `E:\星湾世界\starbay-ai-world`。克隆 main，并核对四个历史 Release 包的 SHA-256 和 ZIP CRC；恢复 UE Content、SourceAssets、Windows 试玩、第六版 Blender 场景和原四类居民工程。
- 保留 Git 中的配置和制作工具，仅补回缺失资产；更新活动目录与恢复记录。没有把未备份的本地修改、旧视频工程或新的实机验收声称为已恢复/完成。
- 新增“焰冕行者”男性红金造型静态初版：CC0 人体、分件内搭/外袍、七片披风、白发、断裂日轮冠与法杖，附可编辑脚本、Blender 工程、静态 GLB/FBX 和四视角实渲图。
- 通过 Blender 独立回读：两种格式均为 391 个网格、559,760 三角形，含冠/法杖整体约高 2.07 米；检查几何有限值、材质、尺寸和 Blender 外部贴图依赖。当前属于展示建模，尚无低模优化、绑定、布料/发丝动态或 UE 操控。
- 角色大型资产另发 `character-ember-v0.1.0` 预发布附件，保留原 UE 和宣传片发布。

## 2026-09-26 · UE5 原生第三人称试玩 v0.2.0

- 确认 D 盘 UE 5.6.1 完整安装，导入 7 个 FBX 与 PBR 材质，保存真实 UE 街区地图。接入 246 个官方 Third Person 模板及共享资源文件。
- 77 次实际引擎碰撞采样通过；PIE 中角色真实移动约 3.18 米、起跳约 1.28 米并稳定落地。测试不涵盖全地图、NPC、任务或性能目标。
- 使用引擎预编译 Development 目标成功生成 Windows EXE，并直接启动进入街区。浏览器原型的 NPC、Qwen、昼夜、任务和存档尚未移植。
- 修正叶片双面透光与灯串发光，仅给场景组件添加新版材质覆盖；已备份地图并验证原网格、原材质未改。新增真正的 UE 茶庭截图，与 Blender 预览分开标明。
- 启用 DX12 SM6 与 Lumen。实测合并大模型触发虚拟阴影队列溢出，当前试玩改用常规阴影，后续拆模与 Nanite 转换后再评估 VSM。
- 修复 Epic 新版安装登记识别、失效等待锁与 Python 保持编辑器运行的接口；新增原生移动检查和带日志、环境恢复、输出保护的打包脚本。缓存与临时文件放 D 盘。
- 保留首次导入末尾 Python 接口异常的历史记录；通过重新打开已保存地图的独立验证确认结果，不覆盖已有地图重导。

## 2026-09-22 · 安装恢复与导入预检

- 定位 Epic Online Services 启动时的 CPU 架构识别失败；恢复新子进程的标准 Windows 环境后，官方服务正常启动并开始下载 UE 5.6.1。新增可复用启动脚本，不修改系统环境或中断现有下载。
- 修正 UE Python 的 Rotator 参数顺序和体积雾调用，校准茶庭观察相机；导入前检查完整来源、目标冲突及未保存地图，避免覆盖编辑。
- FBX 导出改为拒绝覆盖已有文件，并支持全新候选输出目录。
- 按本机 UE 5.6 官方模板核对第三人称角色、动画和输入的完整依赖，新增保留项目配置的模板安装脚本。
- 根据实际 FBX 的源几何检查，整理避开柱子、树、长椅、单车和花池的首次步行验收路线；新增引擎内只读验证脚本。源几何检查和脚本静态检查不等于 UE 实际玩法验收。
- 新增一次性安装衔接流程：等待 Epic 完成登记后接入模板并首次导入；有冲突、失败或超时即停止，状态写入本地报告，不自动声称完成玩法验收。

## 2026-09-22 · UE5 迁移与场景资产基础

- 用户明确改用 Unreal Engine 5，目标为长期提升写实画质的 Windows 独立游戏；浏览器版保留作功能参考。
- 新增风栖茶庭、静态喷泉水池、木廊、灯串、花槽、独立叶片树冠与夜市生活细节，另存组合 Blender 工程，保留原工程。
- 新建 UE5 项目配置、FBX 导出/回读验证、坐标校准与编辑器场景导入脚本；准备两组 1K CC0 PBR 材质。
- 七个 FBX 的 Blender 回读、比例、顶点数量与校验和检查通过；六张材质贴图的尺寸与校验和检查通过。新增预览为 Blender 渲染，不代表 UE 实机画质。
- 当前尚未完成 UE5 引擎内运行、原生 NPC/任务迁移或独立游戏打包；工程基础不能视为这些能力已交付。
- 更新项目约定和可复用提示词，后续默认进入 UE5 路线。

## 2026-09-13 · 项目目录与复用工作流

- 本地项目根目录改名为 `3d驱动NPC的3d世界`，游戏和发布子目录保持原有名称，工作区入口同步更新。
- 新增可直接复制的完整制作提示词、实际流程与文件索引、Blender 到游戏的关系及导出说明。
- 明确 Blender 提供几何资产，运行时光照、NPC 动作与交互由游戏实现；场景上传生成世界仍为未来愿景。
- 改名后以临时本地服务验证健康接口、首页、脚本、环境与四类 NPC GLB 均可读取，检查复用文档链接与本地文件索引；验证服务已关闭。

## 2026-09-13 · 双比例视频封面

- 新增4:3横版与3:4竖版概念封面，以“AI让NPC活了”为视觉主题。
- 分别构图，使用统一人物、字体和薄荷青/暖金配色；明确标注虚构世界与未来场景生成愿景。
- 保存PNG原图和生成提示词，封面随仓库同步。

## v5.1.0 · 中文旁白宣传片

- 加入六段 MiniMax 精英男声中文旁白，分别对应开场、室内、AI 对话、居民带路、任务和结尾，保留64秒剪辑。
- 音乐在人声时降低、间隔恢复；音轨和音量关键帧保留为可编辑内容。
- 结尾将玩家上传场景生成三维世界明确列为未来愿景，当前能力为本地AI居民互动。
- 游戏版本与运行资源沿用v5.0.0，旁白版成片与视频工程单独发布。

## v5.0.0 — 2026-09-13

- 统一为星湾街区 Starbay 虚构都市设定，更新建筑招牌、游戏界面、地图、任务地名和 AI 世界描述。
- 保留丰富的服饰、数码、餐饮陈设和男女老少四类原创都市居民。
- 保留昼夜循环、12 个探索地点、8 类任务、自动存档与本地 Qwen 对话和目的地决策。
- 全部九段宣传镜头重新录制，并使用固定 30 fps 时间步长采集运动；完整替换宣传身份和片头文案。
- 重编玩法与 AI 技术说明，更新截图和架构描述。
- 入口、导航、任务存档与四类步态回归通过。


### 2026-10-05 · Native frontal guide study (WIP)

- Tagged/isolated original main and accent source branches; global affine fit control did not fix broad crown.
- Scalp-fitted diagonal fringe with 231 sections and small layered waves; all five neutral views inspected, target quality still unmet. Continue sculpting from nativefrontwave10, preserve backups.
- Rejected shader-only and local part-cover controls after actual paired renders. Six static character/curve checks and localized source comparison pass within their stated scope.
- No animation, UE migration, candidate Release, paid service or artwork acceptance. Raw/derived geometry remains local.


### 2026-10-06 · Undercoat attribution and side/back layered cut (WIP)

- Actual component IDs identify exposed Abhay undercoat; extend local fibers into a scalp-following side layer.
- Preserve fringe and layer 38,176 existing side/back shafts using measured root/end-flow partitions. Five neutral views inspected; crown bands and part still require work. Rejected flat crown reflow.
- Four localized file comparisons pass within their stated static scope. Actual 1920×2240/512-sample denoised Cycles presentation inspected; no geometry/lighting substitution or art acceptance.
- Continue from nativelayerflow18; preserve old candidates/source geometry locally. No new fee, animation, UE migration, candidate Release or social posting.


### 2026-10-07 · Staggered fringe and root-flow comparisons (WIP)

- Continue from nativefeather21: longer staggered fringe inspected in five neutral views and a 512-sample actual Cycles portrait. Crown/part/back remain below reference quality.
- Reject same-side curtain, overly dark Huang controls and sheet-like individual scalp-arc/wave routes. Clarify unchanged shader color inputs do not imply absorption equivalence.
- Seven localized static comparisons pass within stated scope; source geometry and unrelated edits preserved locally. No new Release.


### 2026-10-07 · Local part support alignment (WIP)

- Align14025 central Bystedt undercoat shafts beneath nearest real long-hair flow; preserve primary hair. Five neutral views and512-sample actual portrait inspected: part bristles reduced, reference quality still incomplete. Continue from nativepartunder26.
- Reject posterior support as a significant crown remedy, detached three-lock accents and jagged sampled-field drape. Preserve all local studies.
- Four paired static comparisons preserve existing mesh/hair within stated scope. No candidate Release or UE migration.


### 2026-10-07 · Whole-path posterior locks and continuous frames (WIP)

- Reproduce96 whole-path families for38176 nonfrontal shafts. Narrow posterior sections, then stagger loose85mm bends and relax tips.
- Diagnose11 radial-frame flips; parallel-transport frame study removes those numerical flips. Current nativebacktransport37 edits40families/16773shafts; selection differs by one141-shaft family from earlier controls.
- All five neutral views and512-sample actual portrait inspected: posterior waves/tips improved, crown/part/reference quality incomplete. Four localized static comparisons preserve existing meshes/roots/other hair.
- Continue from37, preserve prior geometry locally. No new fee, candidate Release or UE integration.


### 2026-10-07 · Missed crown ownership and small-lock sculpture (WIP)

- Frontal studies39/40 do not fix the crown. Read-only all-shaft probe42 and actual ID views43 locate high arches in previously untouched nonfrontal primary hair. Failed empty-subset probe41 is preserved locally.
- Prototype44 sculpts1483 crown shafts;45 applies the method to four high families/3379 shafts. All five neutral views and512-sample actual portrait reviewed: modest crown improvement, posterior37 retained, reference quality incomplete. Continue from45.
- Two explicit pure-Chiang pigment comparisons remain pink/white and are rejected. Four local geometry and two material-only comparisons preserve existing meshes/hair boundaries; material controls also preserve all hair geometry and scene lighting/cameras.
- Source/derived geometry remains local; no new fee, candidate Release or UE integration.
