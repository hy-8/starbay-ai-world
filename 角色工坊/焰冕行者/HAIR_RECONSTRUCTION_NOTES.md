# 红发角色 · 更换发型方法记录

## 2026-10-05 · Fab 专业资产的短路径与材质诊断

实际来源：Muzammil, Free Medium Layered HairStyle for MetaHuman - MHPKG，Fab Standard / NoAI；原/衍生几何留本地，不作生成模型输入。`Source/FabMediumLayered/acquisition.json` 保存来源/用户同意/文件 SHA，无签名下载 URL 或账号内容。

工具顺序：`inspect_fab_groom.py` → `bake_fab_groom.py -- fabcontrol01` → `fit_fab_groom.py -- 新版本 [--hybrid --longback --retain-support --source-response]`。只在全新版本目录运行。`render_fab_particle_control.py` 是固定名字的一次性源对照，已执行，不重跑覆盖。`validate_fab_studies.py` 是四个已保存候选的只读检查，也拒绝覆盖已有报告。

源粒子设置 count=0，但实际已保存粒子是 17,012 / 15,926 / 21,826，不应根据 count=0 判为空文件。世界路径在刷新求值后可读；三个系统都是连续 33 点，没有丢短子发。后方长度中位 25.6 mm、两侧 28.8 mm、冠前 31.5 mm。这是大量分布在头皮上的短轨迹，不能只凭商品名「Medium Layered」断言已经有目标的长而松散的层次。

| 候选 | 已查看的实渲及判断 |
| --- | --- |
| fabfit01 | 完整发型，原始流向/长度，投影目标根；三视角。贴头短发，未采用。 |
| fabfit02 | 保留原创刘海；现有后轨迹×3、侧轨迹×2.6，半径55µm；三视角。长度增加但底发隐藏导致大块头皮暴露，否定。 |
| fabfit03 | 恢复已有短覆盖，侧根阈值扩到 y>−65 mm；三视角。衔接露头皮减轻，但仍蓬直圆帽，未采用。 |
| fabfit04 | 与03新毛发的几何/半径/变换完全相同；仅导入源 Hair 材质，改红色渐变；三视角。降低粉色雾状高光，产生组件明暗不一致，没有解决轮廓。 |

原始粒子材质/半径控制也已实际渲染两张；它与原生控制的粗细、材质和光向不同，不能直接把所有图片差异归于某一个变量。真正的材质单变量比较仅03/04；完整路径哈希验证相同。所有草稿不是成品图，也不把更多发丝或更高采样当成通过艺术验收。


## 2026-10-05 · 切线弯曲分束与后枕体积对照（未通过作品验收）

工具：`Tools/style_posterior_rollers.py`，每版独立从napeunderlay02读取，不能在已有目录重跑。默认分区只塑形高根；`--loose-tips`降低中段弯度并开放末梢；`--tuck-occipital`对所有合格后发点按实际头部法线收拢；`--whole-rear`加入下层独立浅S弯；`--restore-nape-length`恢复部分长下层最多45mm。留住原发根，重做修改曲线末梢半径。隐藏可编辑POLY构造线并非实时Groom链接，也不是最终包络修正后的毛发中心线。

| 版本 | 实际查看与结论 |
|---|---|
| rollerflow01 | Side/back64-sample drafts inspected: actual large-roller bends produced small unnatural crown rings. Rejected. |
| rollerflow02 | Side/back64-sample drafts inspected: open tips removed some rings, but the middle posterior remained round and diffuse. Not adopted. |
| rollerflow03 | Side/back64-sample drafts inspected: actual head-normal envelope contraction reduced some upper volume; low-root paths still diffuse. Not adopted. |
| rollerflow04 | Side/back64-sample drafts inspected: lower paths also grouped and bent, but long nape shortened and upper locks still hard. Not adopted. |
| rollerflow05 | Side/back64-sample drafts and all five192-sample views inspected: loose silhouette and more separate nape tips, but crown spike/hard clumps and opposite-side folds/gaps remain. Rejected for advancing the current model. Source napeunderlay02 remains the stable WIP, not an approved final. |

05全五视角是真实3D渲染，不作最终作品。头皮配对20k诊断5→0，结构不变量通过；没有穷尽线段/衣物或运动验证。原生发丝隔离对照保留底层网格，仅支持主后发体积判断。当前稳定基础仍为napeunderlay02，下一步不采用这些失败候选。几何控制JSON/NPZ和.blend继续留本地，Git只收加工源码、非几何清单和精选原生渲染。

## 2026-10-05 · 原生密度诊断、原创透明底层发片与否定的上层方案

当前下一轮基础为 `Exports/napeunderlay02/Ember_Regent.blend`，五张中性图 `Renders/napeunderlaycheck02` 已实际查看（1200×1400、192 samples、不去噪）。新增28个原创细窄扁平网格锁束，沿真实后颈路径下垫约1mm，尖尾、独立UV方向与程序化纵向细丝透明；本轮没有新导入素材或贴图。所有原生毛发/身体/衣物保留。新增网格直接可编辑，原生CURVES仍是烘焙点，没有新增实时导向/模拟驱动。

实际统计64000条后发：后侧低根区5373条，弧长中位约143mm；其上8323条中位约133mm。因此薄尾不能简单归为没有长发。另对原crowncage02后颈12000点看真实衣物背射线，237点命中、向内超过2mm为0，最近面负深度超过6mm也为0；这是少量射线/离散抽样，不能证明完整衣物遮挡或全量无穿插。只保存量化摘要，不打包来源几何。

| 版本 | 实际检查与判断 |
| --- | --- |
| napeunderlay01 | 侧/背64 samples小样：实体/高光发片在背面明显像塑料条，否定；首次因Blender4.5节点输入名错误而在输出目录创建前失败，读取实际输入名后修正，不是付费重试 |
| napeunderlay02 | 暗哑光、较弱高光与纵向透明，最大单面不透明混合0.48，硬边减轻、后颈补一点不透明度；侧/背小样及五个192 samples中性角度已看，作为有限改善WIP保留，整体未到参考质量 |
| rearfeather01 | 只剪高后枕12629条实际弧长，侧/背小样变化有限 |
| rearfeather02 | 扩至原后发上侧41003条，63—91mm目标与轻微离头皮梢，五视角已看：轮廓松散，但形成横向散喷 |
| rearfeather03 | 从相同02底层基础独立构建，在220个近根小区收拢新短梢，五视角及editorial24高清近景已看；收束后仍横向刷毛/重复轮廓，否定，不选作新基础 |
| rearcubic01 | 重画220条完整父三次曲线，抬根/侧弓/内下梢，侧/背小样形成过于同形的圆帽，否定 |
| rearcubic02 | 父束改为不同45—115mm末端下降、不同手柄与84—100%个人弧长，侧/背仍圆且有平行帘感，否定，不再扩展完整渲染/重复检查 |

底层02源配对检查通过：恰好声明28个新增可见网格，全部保留网格/UV/形态键/变换与原生毛发位置/根/半径完全一致。验证器明确核对额外对象集合和源对象不变，不把新增几何误称为所有网格没变化。失败剪裁02/03的结构检查也通过；03的20000点头皮配对潜在标记1→0、12000点后颈/衣物0，最近约0.75mm，但这既不能证明艺术质量，也不是全量曲线/发丝互撞/新增发片面或动作安全。源配对抽查每版从实际改变点独立取样，02和03不能当成同一批样本跨版本评分。

editorial24真实展示工程 `Exports/editorial24/Redline_Editorial.blend` 和近景 `Renders/editorial24/03_Portrait.png` 来自失败rearfeather03，1800×2100、384 samples、不去噪，已看。新增发片和原生毛发在静态摆姿中共享同一刚性头部矩阵，防止尾端因按身体高度插值而错位；继承几何摆姿/物理灯光，不是新动画或游戏骨骼。近景更清楚地否定了刷毛形状，脸部/衣物也仍不精致，不能作成品或证明当前02底层发型。

保留全部失败版本、旧工程及六项无关文件。没有外部新许可源、付费生成、AI肖像替代、UE或候选Release。下一轮从napeunderlay02继续；上层两种简化父束场已明确失败，不能仅换随机种子或再叠相反波浪后默认采用。

## 2026-10-05 · 连续空间控制场与真实颈部包络

瓶颈是重复束状发流与薄而悬空的后颈；给每束加独立大波浪会产生互相交叉。本轮改为保留每根已有发丝的路径差异，用连续空间控制场直接塑形，不重新用一个中位中心压缩整个发束。脚本名称cage仅表示函数控制场，不是可交互网格笼；最终仍是原生CURVES烘焙点，直接可编辑，不存在新增实时导向驱动。

| 版本 | 实际尝试及检查 |
| --- | --- |
| napecage01 | 向真实颈部/外套背射线包络收拢；侧/背草稿已看，收拢过猛，最大位移133mm，不作为新基础 |
| napecage02 | 从fringefield02重新做，根区/高度连续权重，向内位移上限35.1mm，保留个人弯曲与长短；侧/背草稿已看，后颈悬空减轻，但仍薄且缺少厚实垂落层次 |
| crowncage01 | 在02后颈上只给6160条前冠施加共同空间弯曲，避免各束随机反向大弯；完整五视角已看，但20000点头皮抽查0→167潜在接触，不采用 |
| crowncage02 | 从napecage02重新构建，利用实际源头皮距离衰减向内位移、三次邻点最小过滤延长过渡，再扫描修改的内部点；13011点衰减，没有追加推出修补。完整五视角192 samples、无去噪已看；头皮20000点配对抽查0→0，选为下一轮研究基础，未通过艺术验收 |

02真实半径/根/变换及未修改网格/UV/形态键/其他毛发配对检查通过，21600条非冠部刘海哈希完全保留。后颈20000点同索引配对抽查源和候选各1个潜在头皮接触标记（未新增）；12000点后颈/衣物抽查0标记，最近约1.77mm。离散点结果不是全量曲线穿插、发丝互撞、眼/衣物或动画保证。crowncage01原始manifest的full_crown_flow_rebuilt布尔是当时通用冠部审核选择标记，实际方法为变形而非重画全路径；原始记录保留，review明确纠正，后续源码改用crown_spatial_field独立标记。

当前 `Exports/crowncage02/Ember_Regent.blend` 与 `Renders/crowncagecheck02` 是实际研究点。后枕圆体积/重复条纹、薄后颈、另一侧小弧仍需进一步改变；脸和衣服也未完成。未增加粒子、新许可资产、付费生成、AI肖像替代、摆新姿、动作、UE或候选Release。下一轮应针对后枕分层及厚实垂落，而非再次叠加相反的大波浪；所有旧版本保留。

## 2026-10-05 · 细束扩散场重置与整条刘海曲线塑形

最新研究工程是 `Exports/fringefield02/Ember_Regent.blend`，`Renders/fringefieldcheck01` 正面/三分之四/左右侧/背面五张全部实际查看，1200×1400、192 samples、不去噪。前额末梢和眉侧分束有改善，顶冠仍顺滑/部分规则，另一侧细弧及薄后颈仍在。**未完成参考级发型，不作为作品成品。** 本轮没有重新雕脸、改衣物、摆新姿势、做动画或接入UE；旧检查点保留。

实际读取crownflow04前发数据发现：若干细束根部90%点到束中位路径的距离约3.3mm，而末端达到10—18mm。该值包括个人剪裁后的长度/位置差异，不能直接称作发束横截面宽度。长期复用旧内部偏移会将这些差异再次带入新中心路径，所以这轮先把造型中心和细发丝场分开。

| 版本 | 实际方法/检查与选择 |
| --- | --- |
| fringefield01 | 只改54组刘海/鬓角细束内部场：中位中心不重新塑形，个人弧长90—100%，毛囊偏移连续收窄并加少量细散布；正/侧草稿已看，末梢变细，但部分走向仍重复 |
| fringefield02 | 从crownflow04独立构建，在上述场重建之外，对全中心路径最小二乘拟合三次曲线，再按父束修改两个自由手柄、轻微区分同一父束的三个细束。正/侧草稿和完整五视角已看；选为有改善的WIP，不是最终成品 |
| softcrown01 | 在fringefield02上只重画6160条前冠，加入稳定世界平面的大弯，正/侧和另一侧后补全五视角。三分之四出现更紧的交叉圈结，不能因正面有大弯就采用；该冠部被否定，当前仍用02 |

原生数量和真实根均未减少。新参数沿用同一脚本：

```text
restyle_reference_shag.py -- 新版本 crownflow04
  --front-only --keep-front-length --reset-fringe-fibers
  [--sculpt-fringe-centers] --preview-crown --draft
```

02带`--sculpt-fringe-centers`。该版本早期创建清单的通用文字“unchanged actual median centers”只描述01，不准确描述02；保留原报告，在review中按实际布尔字段`whole_fringe_cubic_sculpt=true`纠正。当前脚本已修正后续方法文字。失败大弯为`restyle_reference_shag.py -- 新失败研究 fringefield02 --front-only --keep-front-length --rebuild-crown-flow --soft-crown-wave --preview-crown --draft`，不要自动把它作为新基础。

复用`validate_concert_still.py -- 版本 --audit-cut --audit-fringe`：按既有原创设计的连续曲线数准确分出前冠6160条和刘海21600条，计算实际位置/半径/变换的区域哈希。02前冠完全保留，softcrown01刘海完全保留；两者全量根/根半径、其他毛发/网格/UV/形态键/变换不变量和有限值均通过。02的54组实际刘海90%点距离分布中位数：根3.335→3.335mm、中段5.461→3.562mm、末端10.863→5.462mm；末端跨组最大18.342→8.809mm。它是三维分布证据，不是艺术合格证明，也没有证明全部眼睛/头皮/发丝之间的穿插安全。

本轮没有新增后颈衣物接触测试：02及softcrown01都只编辑前发，后发与衣物保存数据未变；crownflow04旧12k限定抽查仍仅有其旧范围。大波浪失败版本的完整检查先实渲另一侧，再以`render_opposite_groom_side.py -- 新检查 softcrown01 --five-views --reuse-opposite softcrownside01`复用同源SHA、图像SHA、192采样、1200×1400及无去噪设置均匹配的已完成原图，另四张真实相机新渲；不是翻图或使用不同模型。最终fringefieldcheck01五张均新渲，没有沿用不同冠部图片。

所有模型/失败稿留本地，六项无关修改不动。同步所改源码、成对检查、审核清单与精选实渲；源/衍生许可几何和原始诊断日志不进入Git。Bystedt CC BY-SA和Abhay Pratap Royalty Free署名沿用，未取得新资产或增加付费工具。没有新Release或社交发布，目标保持进行。下一轮应处理冠部的清晰分层与后颈厚度，避免再次用全束同一种波浪叠加制造交叉圈结。

## 2026-10-05 · 中段扭转定位与从毛囊重新规划完整路径

当前研究工程 `Exports/crownflow04/Ember_Regent.blend`；`Renders/crownflowcheck01` 五张真实相机图均已查看，1200×1400、192 samples、不去噪。**这是有改善的制作中检查点，尚未达到参考质量。** 正面偏分与长短层更清晰，左侧较大的上部圈结减轻；另一侧仍有局部交叉细弧，部分冠部高光/侧后层次过于规则，后颈梢偏薄。脸服未在此轮重做。不发布候选成品，不把192 samples或结构检查作为艺术验收。

| 保留试验 | 实际结论 |
| --- | --- |
| crownredirect01/02 | 末端往后改向，01顶部太平、02保留拱度但仍宽；不是整体路径重建 |
| napefan01/02 | 用中位中心展宽、再保留个人路径展宽；均有薄纱/帘状感，未选用 |
| napeoverlap01 | 较高后枕毛囊加入长后颈层，得到更有用的重叠；仍薄、条状，与颈部脱开 |
| crownsweep01/02 | 世界平面前额大弯；02四张192 samples和oppositegroom06均查看。正面较松，侧面仍有顶部圈结；结构通过，限定领口抽查标记0 |
| crownsweep03—05 | 整个短冠路径仿射转向、释放末段切线、软化出口。减少部分回头梢，但未修复所有圈结，不是成品 |
| crownflow01 | 从实际头皮重画完整前冠中心，替换旧中段偏移；前冠隔离无旧大圈，整体侧面仍有圈结 |
| crownflowdiag01 | 实际可见冠部/后发/短支撑/刘海各一张侧面隔离图，源工程不改。确认左侧顶部大圈来自旧上部后发，不能再全部归因于前冠；此定位不自动覆盖另一侧全部细弧 |
| crownflow02/03 | 上部后发附着段与自由重力段完全重画；02偏贴头，03增加早释放和蓬松仍较平 |
| crownflow04 | 上层增加侧向偏分、组级不同抬高、较窄出口与长短变化，五视角已检查；进度改善，仍有上述不足 |

新接口沿用 `Tools/restyle_reference_shag.py`，全部拒绝覆盖已有版本：

```text
前冠完整重画：--front-only --keep-front-length --rebuild-crown-flow
上部后发重画：--rear-only --rebuild-rear-crown
上层释放/聚束：--lifted-rear-layers --clumped-rear-layers（依赖后发重画）
低成本正/侧小样：--preview-crown --draft
后颈重叠层：--rear-only --spatial-rear --loose-wave --free-nape --layered-nape
```

实际链路为 `shagcut05` → `napeoverlap01` → `crownsweep05` → `crownflow01` → `crownflow04`；crownsweep05从napeoverlap01构建前发，带既有冠部改向/仿射/自由梢/平面前额扫掠参数，详见原创建清单。01与04只变指定组件，必须保留本地所有源工程才能复建，Git中的元数据不是几何本体。`crownflow01`的早期通用“剪裁”文字已在review中更正，原创建报告保持不动。以前各早期创建清单的文字也以review对实际参数的解释为准。

前冠与上部后发都用真实根开始，仅附着段投影到头皮，随后沿连续切线离开并下垂；避免只拖终点造成路径回头。新中段不再带旧曲线的扭转偏移，改用真实毛囊宽度场和微小个人散布；后发根z=1.825—1.845m之间连续混合，低区沿用长后颈。04将偏分边界移至x=14mm，用不规则空间根分组的相邻出口聚束。这些参数仍是造型研究，不能把该方法宣称为任何头模的通用合格发型。Blender内保存的中位路径是隐藏的烘焙参考，不是实时驱动器，改它不会自动更新可见发丝。

复用检查器完成01/04的源哈希及全量保存数据配对：根/根半径/变换、未修改网格UV/形态键/其他毛发不变量与有限值均通过。04的后发改变可能影响抽查区域，所以实际重新抽查：12,000点、潜在接触标记0、最近约7.15mm。范围仍仅为z<1.735m且y>−.015m的每第四个后发点、上限12k和实际开口外套/后领最近面法线；无全量实体/布料厚度/动作验证。`render_opposite_groom_side.py -- 新检查版本 crownflow04 --five-views`读取同一源，保存四张既有中性相机加真实另一侧相机，不翻图、不改源；`diagnose_crown_flow.py -- 新诊断版本 crownflow01 spatialfringe17 --current-surface-rear --profile-layers-only`复现四层侧面检查。

六项无关源码哈希保留。加工源码、非几何报告及精选实渲同步GitHub；授权原/衍生资产、大型blend、运行日志和临时审核脚本留本地。保留Bystedt CC BY-SA与Abhay Pratap Royalty Free署名，隐藏Ddr授权几何不分发；没有新付费服务、动画、UE接入、候选Release或社交发布。

## 2026-10-05 · 从剪旧路径改为重画空间后发

当前 `spatialrear08` 保留 shagcut05 前发与短覆盖，实际编辑64,000条原创后发。`restyle_reference_shag.py` 新增空间后发、松波、自由后颈和真实衣物包络约束。从相邻根组的真实中位根重新规划路径，只保留短头皮段，中层较早离开表面；后颈不继续跟随向内的颈部切线，改从发根深度自由下落。每根实际根精确保留，按个人比例采新中心路径并保留截面差异。隐藏代表路径仍只是烘焙证据，不是实时驱动器。

| 候选 | 实际检查与结论 |
| --- | --- |
| spatialrear01 | 侧背草稿；下部圆壳减轻、后颈分布变开，仍平行。01—03原创建报告的通用“剪裁”文字不准确，review单独更正为空间路径重画，原报告保留 |
| spatialrear02/03 | 02侧背草稿，03四张192 samples检查；宽松波浪、向更高区域连续过渡，中后脑层次增加，前冠仍宽，后颈与衣领接触 |
| spatialfront01—03 | 三次前额小样，均检查正面/三分之四。强波浪、半幅波浪与连续传输造型坐标轴仍有细圈/浮束，均不采用；不把坐标轴不稳定推测当已证明主因 |
| spatialrear04 | 侧背草稿；限定后发区域全部曲线点用真实外套/后领背面包络约束，12,000点抽样接触标记从03的246降至0。绕领口造成硬转弯，未接受 |
| spatialrear05/06 | 05侧背草稿，06四张192 samples及真正另一侧oppositegroom04；额外后颈长度78mm、避让提前100mm，抽样0标记，仍有贴颈后向外的硬转折 |
| spatialrear07/08 | 07侧背草稿，08四张192 samples及另一侧oppositegroom05；后颈从毛囊深度自由垂落，硬转折减轻。宽冠部、细/稀尾梢与重复层次仍在，08为当前未通过艺术验收的检查点 |

新增只读 `probe_nape_garment_contact.py`：后发z<1.735m、y>-.015m的每第四个曲线点，均匀抽最多12,000点；测试实际求值套装与后立领，距面<6mm且最近面法向间距<-0.5mm为潜在接触标记。03为246，04/06/08为0。开口衣物最近面法线不能给出完整体积内外证明；没有覆盖所有服装、发丝之间或动画。08抽样最近距离最小约8.28mm，须结合实渲判断漂浮/轮廓，不把更大间距自动当作艺术改善。

06/08源配对检查通过全部根/根半径/变换、未修改网格/UV/形态键/毛发不变量及有限值/半径/贴图。四视角和另一侧都是真实3D渲染、不去噪；没有新近景或生成肖像替换。下一步优先重新设计前冠整束方向及后颈宽窄/自然收梢，不再盲目给所有前束增加波浪。许可组件、历史工程、六项无关修改保留；没有动画、UE、新候选Release或付费生成。

本地重建：Blender后台执行 `Tools/restyle_reference_shag.py -- 新版本 shagcut05 --rear-only --spatial-rear --loose-wave --free-nape --garment-clearance --nape-extra 0.078 --guard-transition 0.10`。代表小样加 `--preview --draft`；输出必须全新，禁止覆盖。需要既有本地许可资产和源工程；JSON清单不等于资产本体。

## 2026-10-05 · 错层剪裁的中心路径修复与明确脱离表面的发尾

新增 `restyle_reference_shag.py`，直接编辑 portraitsculpt02 的实际原创前发/后发；全部实际根保留，短支撑和许可组件延用。剪裁按实际弧长采样，冠部小束按相邻根排序拆分；后发使用240个局部根分区，保留细发梢而非剪成旧粗半径。研究导向保存为隐藏CURVE，但它们不是实时连接的梳理控制。

| 候选 | 实际检查与结论 |
| --- | --- |
| shagcut01 | 四张64 samples草稿已看。刘海剪短过多；个人剪短参数只作用于截面偏移、未正确重采中心路径，发尾仍过齐。保留失败，不能用其说明“独立错层已生效” |
| shagcut02 | 修复每根中心路径的实际弧长重采，只改后发，侧/背草稿均已看。64,000条后发中位实际长度99.74→70.41mm；后脑仍圆，剪短本身不足以改变主轮廓 |
| shagcut03 | 在02上只剪36,000条底覆盖发到18—29mm，根和路径方向保留，侧/背已看。外轮廓几乎不变，排除这层是主因；未采用为下一制作基准 |
| shagcut04 | 回到portraitsculpt02，只改后发。上部外层实际加约12mm中段水平离头皮起伏、10mm末端水平离开与18mm上转，低后颈保留向下；侧/背草稿已看，上部边缘更碎，仍有圆体积和下部条纹 |
| shagcut05 | 在04上只改前发，保留中心路径长度，冠部相邻根分束、末端截面变窄和少量独立剪裁。四张1200×1400/192 samples无去噪均已看，上部碎层增加，宽冠部/圆后脑/细条后颈仍在，不接受为参考作品 |
| oppositegroom03 | 05真正另一侧相机渲染，192 samples已看，非图像翻转；另一侧上部碎层可见，中下后脑仍规则，源文件哈希未变 |

个人剪裁修复方式：原错误 `q = new_base + offsets*width` 把各纤维放在相同的整束长度；改为对实际新中心路径按 `personal/fraction` 重采，再叠加同一弧长位置的纤维截面。已有01报告保留原文，新review明确注明错误；后续报告包含实际纤维弧长前后分位，不只记录意图参数。02的99.74→70.41mm只是长度事实，不是艺术进步的充分证明。

复用 `validate_concert_still.py -- 版本 --audit-cut`，不另建独立检查系统。它读取并核对声明源文件哈希，逐位比较所有可见原生发根、根半径、世界变换；确认未修改网格/UV/形态键及毛发数据哈希保持不变。04、05均通过，有限值/正半径/贴图也通过。每四个内点的近体保护与沿路径平滑修正不是全量穿插测试，也未验证发丝之间、衣物或动画。

本轮仍非完成，当前05只是有效改动的制作检查点；不追加旧发型展示近景来混淆结果。后续应重画中后脑的整束方向和自然长度梯度，避免继续依赖剪底层、加密或提高采样。没有收费服务调用、新动画、UE接入、Release或社交发布；授权组件和历史模型全部保留。

## 2026-10-04 · 导向插值对照、实测前额间距与面部替代精修

`crowndiag02` 在 originalsweep03 实际模型上隔离八张冠部/刘海/支撑/后部及侧面图；全部已看，源文件哈希不变。新增入口必须确认原创后发存在，支撑包括新增真实短覆盖和保留自然发流支撑。隔离显示长后发仍有顺滑平行壳感，短支撑跟随头部，冠部与刘海重叠仍宽。

| 实际版本 | 检查与结论 |
| --- | --- |
| originalsweep04 | 四张64 samples草稿已看；240路径/64,000原创后发使用50—110mm基础长度，加长后颈，6—10mm相位不同的真实法向起伏；后部深度更明显，仍有重复层次与偏圆轮廓 |
| originalsweep05 | 四张草稿已看；三近邻根逆距离加权混合实际导向，保留20%末端聚束，反而形成圆滑波波头/耳侧薄片，明确不采用 |
| frontalenvelope01 | 四张草稿已看；18mm上部中心路径间距目标，57束改动，最大22.33mm位移，视觉改善有限，局部偏平 |
| frontalenvelope02/03 | 22mm目标扩到眉侧，49束改动，最大21.89mm位移；02四张草稿、03四张192 samples全质量及oppositegroom02实际另一侧均已看，眉侧悬空感减轻，顶部/后脑仍规则 |
| editorial19 | frontalenvelope03的384 samples实际近景已看，发丝可辨，但脸服仍通用，未接受为作品 |
| portraitsculpt01/02 | 同一中性面部雕刻，01四张草稿、02四张192 samples全质量已看，神态集中、骨相略明确，发型与源完全相同；未达到参考 |
| editorial20/21 | 20只变换网格未变换形态键，造成脸与已摆姿眼球/头发错位，失败稿；21同时变换全部形态键的修复草稿已看 |
| editorial22/23 | 同一雕刻模型的1800×2100/384 samples实际近景均已看，无去噪；23另显式更新Key/Object/依赖图。高清中面部改善仍温和，没有把渲染成功视为验收 |

可复现根部探针 `probe_frontal_root_attachment.py -- originalsweep03` 每24根抽查：冠部257根、刘海900根，实际人体BVH法向间距约0.498—0.501mm；原文件哈希不变。它反驳“这些前额根普遍浮空”的推测，不能外推成全部发根/整根纤维无穿插。

`fit_frontal_volume_envelope.py` 修改实际中心路径而非根部：选定区域法向间距超目标时平滑压低，原发根逐位完全相同、保留截面偏移。03记录的选定中心路径p95间距35.97→22.04mm、最大44.08→29.40mm；前后统计端点资格略不同，不是完整毛发间距。已有01—03生成清单沿用旧键名 `upper_base_gap_after_quantiles_m`，`lower_fringe_included=true` 时实际包括下部刘海。新版脚本改为selected命名，保留旧证据原文，不能误称只测上部或全量穿插验证。

`sculpt_portrait_landmarks.py` 不再使用失准的名义眉位置1.779m：实际眉卡范围1.753—1.767m，实测眼球中心z=1.74878m。五个独立相对形态键保留原Basis/顶点顺序/UV，不改变z≥1.782m头皮、眼球或毛发。`audit_portrait_sculpt.py` 的成对哈希不变量均通过；101×97前视网格每眼可见射线约1497→1100，投影面积减少约27%。近眼选定顶点法向间距仍含负值，且这不是严格封闭碰撞测试；不能宣称全部接触修复或游戏/表情可用。`validate_concert_still.py` 新增形态键有限值检查，02/23结构通过与艺术未通过分别记录。

下一步仍需对冠部/后部做明确方向和长短层次造型，面部个性、服装剪裁独立继续打磨；避免重复把加密、平滑插值或提高采样当作质量突破。所有候选和失败稿保留，不新增动画、UE、Release或社交发布；授权毛发组件来源不变，几何继续留本地。

## 2026-10-04 · 分开覆盖与造型，重建真实侧后发根

本轮完整实渲检查点为 `originalsweep03` 四视角（1200×1400、192 samples、不去噪）及 `editorial18` 近景（1800×2100、384 samples、不去噪），均实际查看。**仍非参考级作品；没有将结构验证或渲染成功当作艺术验收。** 旧检查点与试验不覆盖。

### 保留长覆盖壳的对照

`recomb_visible_locks.py` 新增 smoothflow02 特定入口，必须同时指定 reference-flow / rear-only / preserve-width，并确认canonical后发可见且无重复替代。referenceflow01改变波浪与长短但后方露皮；02保留24,590条交错原长发，恢复覆盖同时保留圆壳；03把外层分为较窄相邻小块，局部层次改善，仍圆。04为同几何全质量源工程，其四张原输出未直接审核；其材质副本sheengroom02的四张192 samples输出已审核。05中央后颈延长更明显，末端有直尾感，未采用。

`finish_native_hair_surface.py`显式改克隆材质粗糙度 .30 / radial .36，以位置/半径哈希验证几何完全不变；sheengroom01/02已查看，只是表面定义改善。editorial17加入真实物理近景灯位，已查看；不解决形状。envelopeflow01沿头皮法线压低选定后部间距，仅7,217个点改变，最大3.94mm，四张已看，视觉改善有限。不能继续把后方偏圆归因于巨大离头皮距离。

### 弧长剪裁与相机射线定位

新脚本 `sculpt_shag_layer_lengths.py` 对74,113条侧后发全部按真实弧长/连续根部空间场剪短，保留所有旧根，不再保留完整长覆盖壳；rootlayer01四张已看，露皮。26000条原创短发按真实头皮面积采样、平行传输后，rootlayer02恢复温和剪裁下覆盖，但轮廓仍圆。

rootlayer03是更短冠部的 **build-only中间模型**，没有自己的渲染评价。rootlayer04组合短底发后仍露皮；rootlayer05扩大侧部采样，但下边界仍偏高，查看三个侧/后图仍有缝隙。通过rootlayer05实际03_Side正交相机射线求交CC0人体，发现选取的露皮带约z=1.77—1.79m，低于原假设1.807m。六个实际求交记录在 `Source/scalp_band_ray_diagnostic.json`，仅该样本，不是全量穿插证明。

`grow_posterior_short_coverage.py --measured-band`改为后部y>.025且z>1.754、其余侧后y>-.074且z>1.773，并排除明显朝下三角面。rootlayer06新增36,000条37—61mm短发，四张草稿均看，修复带状露皮；没有实心毛发帽或图像涂抹。但旧侧后总轮廓仍圆，不能仅把增发当质量提升。

### 原创侧后造型替换

`rebuild_posterior_surface_groom.py`只接受已检查的rootlayer06，要求独立短底发存在；隐藏旧侧后，保留全部历史。以真实头皮按三角面积取新根，通过不规则最远点分布划分造型小块，根部切线沿头皮传输，末段离开表面形成自由下垂。各纤维有轻微弧长差和亚毫米扰动，点检查修复近体穿插；不是读取隐藏Ddr旧曲线重生一份重复毛发。

| 版本 | 实际查看与结论 |
| --- | --- |
| originalsweep01 | 160路径/64,000原创长发，四张草稿已看；侧后收窄、耳侧更清楚，后颈过短且对称分开，不采用为成品 |
| originalsweep02 | 长后颈、较向中央的下部走向和上部偏向，四张草稿已看；长度恢复，但聚为少数尖尾，未接受 |
| originalsweep03 | 240较细分区、下部根分布保留而非统一聚中，后颈加入小幅空间弯曲；四张192 samples实际看，侧后比旧壳收窄，但上后部仍较顺滑/规则，部分发尾偏直，作品验收未通过 |
| editorial18 | 03实际近景384 samples已看；耳侧简洁，前额仍宽，脸服仍通用，仍是制作中检查图 |

03可见原生发丝165,417条，包含27,760原创前额、23,657 Bystedt短支撑、14,000 Abhay发流支撑、36,000原创后部短覆盖、64,000原创后部造型；数量仅记录。源Royalty Free资产与隐藏衍生几何仍本地；原创替换并不把所有保留组件改成原创或CC0。

另完成 `Renders/oppositegroom01/05_OppositeSide.png` 并实际查看：1200×1400、192 samples、不去噪。反射相机世界位置/局部X以保持正手性，不翻转像素、不改模型，前后源工程哈希相同；另一侧仍能看到较规则的冠部/后发走向与前后衔接，艺术验收未通过。

完整本地依赖存在时，以全新版本名复建（源版本参数绑定已审核输入，不能随意替换）：

```text
sculpt_shag_layer_lengths.py -- 新剪裁 sheengroom02 --shorter-crown --build-only
grow_posterior_short_coverage.py -- 新短覆盖 rootlayer03 --measured-band --draft
rebuild_posterior_surface_groom.py -- 新侧后 rootlayer06 --long-nape --soft-nape
render_editorial_pose.py -- 新近景 originalsweep03 --portrait-only --hair-detail --reference-light
validate_concert_still.py -- 新侧后
```

第一、第二行解释rootlayer03/06构建沿革；脚本当前明确绑定这些实际源名称，不能把示例的新版本直接传给后续入口。角色.blend与许可依赖不在Git，仓库不是独立完整重建包。没有新UE、动作、布料或候选Release。另查BlenderKit免费狼尾/男性/波浪发型，仅查看不适合的Radhe/Dr toxic作者预览；没有导入其资产。MetaHuman本地仍未找到可用核心groom集合，此路线未采用。原始搜索JSON可能含signed URL，保留本地。

## 2026-10-04 · 冠部隔离、自然发流替代与真实头皮补发

当前实际进度检查点为 `Exports/smoothflow02/Ember_Regent.blend`，四视角 `Renders/smoothflow02` 已逐张查看：1200×1400、192 samples、不去噪。高清近景 `Renders/editorial16/03_Portrait.png` 已查看，1800×2100、384 samples、不去噪；展示工程 `Exports/editorial16/Redline_Editorial.blend`。**目标仍进行，尚未达到参考级角色作品质量。** 19/15及全部历史版本保留。

用户允许尝试其他方法后，新增冠部/刘海/底发/后发隔离诊断，确认宽冠部来自多个重叠组件，不是单一冠部或密度问题。分束强剪裁造成侧后横向露皮；保留截面和温和剪裁仅局部改善。降低原创刘海根部也未消除宽冠部，均保存为不采用的试验。

实际获取 Abhay Pratap 的 BlenderKit 免费 `Realistic Hair`，许可 Royalty Free，非 CC0；读取9,870条真实 POLY 发丝及世界变换，拟合/剪裁/转原生CURVES。单独造型仍像中分女性波波头；修复低发根漏剪并接入21,600条原创下部刘海后，仍偏圆且接缝不自然。短底层替换也露出局部头皮，未采用这些整套发型。不是AI肖像替换，来源/衍生几何留本地，原作者预览不作为项目成果。

有效改动是重新从角色真实头皮按三角面积采样14,000条短底发，以邻近自然发流方向沿头皮传输，保留原刘海、后颈和Bystedt短支撑。随后把82束原创前发的实际中心路径重梳为78%空间三次曲线/22%原路径，保留全部发根与纤维截面。可见总数139,530条仅作结构记录；补发减少顶部露皮，重梳减轻交叉细绳感。隐藏旧导向仍是历史设计证据，不是实时连接，不能编辑它们就声称更新了烘焙发丝。

当前仍有宽冠部、侧后偏圆/偏规则、个别层次不自然，脸部/服装的雕刻和剪裁也需独立精修。两个最新工程的有限值、正半径、贴图与哈希检查通过，仅代表结构；没有全量发丝/眼睑/衣物穿插或动画验收。沿用静态几何摆姿，无新UE、动作、候选Release或社交发布。

### 实际对照及不采用的原因

| 版本 | 读图结论 |
| --- | --- |
| crowndiag01 | 六张隔离图已看；真实6160冠部/21600刘海分区，确认刘海上段与后发共同构成宽冠部，源工程未改 |
| flowgroom01 | 强沿生长路径剪裁出现侧后横向露皮，否定 |
| flowgroom02 | 保留截面、温和剪裁恢复大部分覆盖，后发略细但仍圆，未替换19 |
| flowgroom03 / spatialfringe18 | 原创控制15降低眉侧/鬓角根部与冠部升幅；四张组合草稿已看，改善有限且顶部小缝加重 |
| abhaygroom01 | 四张草稿已看；自然流向偏女性中分波波头，低根漏剪留下长侧发 |
| abhaygroom02 | 9374条按高度实际剪断，496条低根改用弧长剪裁；四张草稿已看，接入低刘海后仍偏圆、接缝明显 |
| abhayfoundation01 | 四张192 samples图已看；原始发根分布不足以替换旧短支撑，前顶和背部露皮，未采用 |
| scalpflow01 | 四张192 samples图已看；面积采样新底发补充真实覆盖，上层长发形状不变，仍有细绳感 |
| smoothflow01 / smoothflow02 | 草稿及全质量四张均看；实际空间三次路径减少交叉，全部原发根完全保留；仍非参考级作品 |
| editorial16 | 实际384 samples近景已看，无去噪；头顶覆盖和前额流向改善，脸服仍通用，未通过作品验收 |

`recomb_visible_locks.py`限定19的可见原侧后组件，拒绝重梳后的源版本，防止从隐藏旧侧后读取后产生双重可见毛发。`replace_frontal_groom.py --source-frontal-name`允许指定旧修订对象名，但新导入对象仍使用固定canonical名称。

在完整本地依赖存在时，用全新版本名按顺序重建；这些依赖含本地许可几何，GitHub不能独立重建：

```text
recomb_visible_locks.py -- 新后发试验 regionalgroom19 spatialfringe17 --preserve-width --gentle-cuts --rear-only
fit_abhay_native_hair.py -- 新自然底层 flowgroom02 --scalp-foundation
grow_scalp_support.py -- 新头皮补发 regionalgroom19 新自然底层
smooth_styling_paths.py -- 新重梳版本 新头皮补发
render_editorial_pose.py -- 新近景 新重梳版本 --portrait-only --hair-detail
validate_concert_still.py -- 新重梳版本
```

Foundation实验绑定已经检查过的flowgroom02，不能把首行的任意新版本直接替代这个源参数；首行说明flowgroom02的来源。控制15为项目原创；仅组合版本真实渲染后评价它，spatialfringe18本身只build。第三方曲线本体/几何提取、signed URL、原作者预览均不提交。

## 2026-10-04 · 密度反证、独立细束和真实剪裁试验

本轮继续实际Blender几何。当前19四张全质量检查图和15高清近景都已实际查看，**艺术验收仍未通过**。不存在工具无法运行的阻塞，瓶颈仍为原创冠部/前额流向、发束衔接与面部服装的造型水平。

| 试验 | 实际方法与查看结果 |
| --- | --- |
| spatialfringe15 / regionalgroom15 | 保持控制12和材质，fibers-per-guide从1000改600；前额20,040条。四张960×1120、64 samples、不去噪草稿已看；减轻密度，没有消除宽片。密度不是已确认的唯一原因。 |
| spatialfringe16 / regionalgroom16 | 控制13分开侧向短层和下垂长层，46导向、23,380条前额。四张草稿已看；短层轮廓变动，眉侧仍连片，未作为主检查点。 |
| spatialfringe17 / regionalgroom17 | 控制14拆分18条宽眉侧/鬓角路径成54条独立细束，保留28冠部，82导向、27,760条前额。fine-locks将根部范围改为3.5mm、截面sigma为1.15/1.10mm。四张草稿已看；分缕更明显，但交叉绳感及宽冠部仍在。 |
| regionalgroom18 | 真实沿原生长路径剪短保留的侧后整束，并重新收尖半径；与单纯抬旧末端不同。四张草稿已看，有外翻和不理想轮廓，未采用。 |
| regionalgroom19 / editorial15 | 与17相同前额几何组合，19为1200×1400、192 samples不去噪四视角；15为1800×2100、384 samples不去噪近景。全部实际查看；分缕改善，但尚未达到参考，局部冠部小缝、交叉及偏圆侧后仍需处理。 |
| anatomy01 | 在19的CC0脸部上做局部实际雕刻，眉/睫毛跟随，眼球不改。2,808个顶点发生位移；四张草稿已看，神态略变化，依旧通用数字人，未替代主检查点。 |

`author_concert_fringe.py --build-only`只保存实际几何，不渲染，清单也明确标记；随后需要组合工程实渲才能评价。原创控制13/14由`design_feathered_crown.py`、`design_independent_fringe.py`写出，脚本拒绝覆盖已有控制文件。隐藏导向仍为证据，编辑它们不会实时更新烘焙发丝。

有既有本地许可依赖时，使用全新版本名复建当前发型：

```text
author_concert_fringe.py -- 新前额版本 layercut08 --choppy-locks --reference-cut --root-patches --soft-patches --segmented-crown --fine-locks --fibers-per-guide 400 --design <绝对路径>/concert_fringe_control14.json --build-only
replace_frontal_groom.py -- 新组合版本 regionalgroom13 新前额版本 --dry-groom
render_editorial_pose.py -- 新近景版本 新组合版本 --portrait-only --hair-detail
validate_concert_still.py -- 新组合版本
```

组合替换脚本仍要求源工程中存在可见的canonical前額对象，故这里指定regionalgroom13；不能直接以19替代该源参数。19/15/anatomy01结构检查通过，仅有限值、正半径和贴图存在。既有侧后及短支撑分别保留Royalty Free/CC BY-SA，含授权几何的模型不进入Git；没有新动画/UE/候选Release。

## 2026-10-04 · 窄冠部路径与发尾释放

本轮最新真实几何 `regionalgroom14` 四视角及 `editorial14` 高清近景均已实际查看；文件结构检查通过，**仍未达到参考，目标继续**。变化是几何和材质的局部加工，没有新生成肖像、动画或UE接入。

| 实际试验 | 检查结论 |
| --- | --- |
| regionalgroom10 | tip clump从原.95改.65，加独立末端偏移与小弯；针状聚拢减轻但后方过度蓬松，不采用该幅度 |
| spatialfringe13 / 控制11 | 保留32条原路径，添加18条稀疏micro feather；短层可见，但宽冠部仍存在 |
| regionalgroom11 | 聚拢强度.85、末端偏移减半，使用新前额；比10克制，仍宽片 |
| regionalgroom12 | 上述几何与三部分毛发统一.42/.48粗糙度，全质量四视角已看；轮廓柔和，但后脑偏直 |
| regionalgroom13 | 连续高度权重的后颈S弯，保持上部头皮覆盖；全质量四视角已看，后颈有限改善 |
| spatialfringe14 / 控制12 | 用28条较窄成对路径替换14条冠部/feather路径，保留18条眉眼/鬓角路径；四视角已看，分层增加，仍规则 |
| regionalgroom14 | 在13只替换前额与匹配其粗糙度，保留侧后与短支撑；全质量四视角已看，33,400条前额发丝，不等于艺术验收 |
| editorial14 | 1800×2100、384 samples、不去噪实际近景；有真实细发丝，冠部仍有连片/规则层次，脸服仍需独立精修 |

`shape_regional_groom.py` 的新末端随机数发生器独立于既有分区/剪裁随机数，避免为了放松发尾同时改变全部旧发束位置。`--tip-clump` 只改变真实几何截面向末端聚拢强度；不是材质透明度或伪装渲染。`--nape-s-waves` 按整束中心线和连续高度权重改动，随后继续真实body间距修正。全量衣物/动画穿插仍未验证。

新前额的 `--airy-feathers` / `--segmented-crown` 只作用于控制图中明确命名的路径，分别调整其根部小块、截面与发丝数，不提高其余前额密度。控制12没有使用旧sectioned relief；隐藏路径依旧是烘焙证据而非实时驱动。少量成对发束仍会连片，根部集中/密度是后续需验证的假设，不能当作已经确证的唯一原因。

在有本地许可依赖的情况下，用**全新目录名**复建：

```text
author_concert_fringe.py -- 新前额版本 layercut08 --choppy-locks --reference-cut --root-patches --soft-patches --segmented-crown --fibers-per-guide 1000 --design Source/HairReconstruction/concert_fringe_control12.json
shape_regional_groom.py -- 新组合版本 nativeasset02 新前额版本 --scissor-layers --lean-wolf --stagger-locks --feather-tips --tip-clump 0.85 --soft-tip-spread --dry-groom --nape-s-waves
render_editorial_pose.py -- 新近景版本 新组合版本 --portrait-only --hair-detail
validate_concert_still.py -- 新组合版本
```

前额控制图是原创路径；Ddr Rcs原发片/导向线及衍生几何继续留本地，Bystedt短支撑保留CC BY-SA署名。本轮仅同步加工源码、原创控制、非几何清单和选定真实检查图，不创建候选Release。

## 2026-10-04 · 保留贴图、UV 采样转发丝与分区组合对照

用户询问瓶颈并授权更换方法。本轮完成实际几何试验及四视角检查，**没有达到参考质量**；保留 `regionalgroom08` / `editorial13` 为先前完整检查点，不把新增试验自动当作更好成品。

| 试验 | 实际结果与判断 |
| --- | --- |
| texturedgroom01 | Ddr Rcs 保留原 UV/alpha 的实发片对照；发梢更柔和，侧后仍偏圆、像波波头，未采用 |
| spatialfringe11 / regionalgroom09 | 冠部毫米起伏与五组小截面；有轻微表面变化，仍带条带/绳状感，未采用为作品 |
| spatialfringe12 | 原创控制10强化 S 转折；冠部交叉如绳且出现沟槽/空隙，否定 |
| layeredasset01 / 02 / 03 | Salman 发片实际拟合；01 压进头皮，02 太高而露两侧，03 下调但仍为短刘海/短后发，均不匹配 |
| layeredasset04 | 参数试验因追加节点缺少 Weight socket 中止；没有图片/完整模型，不能当作渲染候选 |
| layeredasset05 | 修复 socket 兼容性；显式断开粗糙度/镜面连接、修正次表面/涂层并延伸后颈；红色恢复，但宽片、局部裸露、直长发尾仍明显 |
| layerednative01 / 02 | 实际求值网格的 UV 三角形重心采样，原灰度不透明度筛选后转原生 CURVES；02 共 35,492 条，11,224 条前额发丝延伸并加入整束毫米波浪，仍像圆帽、刘海层次不足 |
| layeredhybrid01 / 02 | 选完整冠部发丝，保留原创长刘海和已有侧后/短支撑；02 对高冠部连续下调、重新修正头皮间距，四视角 1200×1400、192 samples、不去噪均已查看；顶部团簇/沟槽仍生硬，侧后仍偏直，未认定优于08 |

### 诊断事实与适用边界

原 Salman Shader 用贴图控制 Roughness 和 Specular IOR Level，单改 socket 默认值不会生效。`fit_layered_hair_asset.py --crimson-remap` 显式移除这些连接后赋值，保留原 Alpha（灰度 JPEG 色彩输出，不是文件 RGBA alpha）。源码独立检查与追加后的节点接口不完全相同，所以 Weight 只能在存在时赋值。实际更新 depsgraph 后的网格顶点范围与旧未求值 bound_box 有差别；拟合需要烘焙更新后的世界坐标。

`sample_layered_card_fibers.py` 按求值 UV 三角形插值空间位置，以原灰度图筛选发丝列；头皮贴合和更高端点发根规则均为启发式，不能称作原作者精确发根恢复。`compose_layered_crown.py` 只按整条曲线筛选，不通过删根点制造悬空发丝。头皮间距处理不代表全量衣物或动作穿插检查。

`spatialfringe11/12` 的 `authored_fringe_design.json` 和隐藏导向线保存的是加入 sectioned relief 前的规范路径；不是变形后逐点对应的实时控制。清单记录该 flag，但旧几何不会随新脚本变化。不要把规范路径声称为最终发丝的精确中心线。

本轮来源为 Salman Ramezani BlenderKit Royalty Free，非 CC0，原/衍生几何留本地；混合版本继续保留 Ddr Rcs 与 Bystedt 各自署名，详见 `THIRD_PARTY_ATELIER.md`。所有作者预览只为研究，新检查图来自实际模型。后续要改变局部冠部造型和前后衔接，不能重复通过更多发丝/更高采样冒充改善；面部和服装依然需要独立精修。

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


## 2026-10-05 · 显式主束与电影毛发适配试验（仍未通过）

稳定研究基础仍为 `Exports/napeunderlay02/Ember_Regent.blend`，本轮没有替换。先画31条完整空间主束，authoredrear01/02/03的九张真实草稿均已查看：宽根片形成棉团，薄截面传输出现尖结/硬折，头部包络又合并成平滑假发片，三版均否定。

随后改用有许可证据的原始Sintel粒子毛发，来源为Scthe混合许可容器的固定提交；只提取SintelHairOriginal，不导入其他发卡、Unity材质、NC睫毛或脚本。原文件Zstandard压缩、SHA与Git LFS一致，自动脚本关闭。旧粒子短子发缓存长度不同，第一烘焙检查报错；按每根真实连续点数分别重采样后，control01得到11,628条、control02得到57,228条。四张实际源头模渲染均已查看，它们不是项目角色成果。

sintelfit01/02/03的九张角色实渲均已查看：960×1120、Cycles/OptiX64 samples、不去噪。01/02减少旧硬块但顺直帘和圆后枕仍不合参考；03组合旧前发出现前冠衔接空隙，明确否定。各版保存原生可编辑CURVES，根投影/整根位移和离散身体保护不是实时毛发驱动或全量穿插保证。网格/UV/形态键/变换与稳定源成对检查另存，结构通过不能证明艺术通过。

**目标未完成，模型仍需打磨；不采用本轮任一版本作为新作品基础。** 这轮证实成熟资产的造型匹配比单纯增加密度重要。下一步先选与目标相近的男性中长层次毛发，核对源造型实渲与许可，再做少量针对性拟合；不要再以顺直短发或失败的程序化团簇反复扫参数。面部与服装仍未达到参考质量。源码/清单/精选检查图同步，原/衍生几何留本地；保留旧工程及六项无关文件，没有新付费、AI肖像替代、动画、UE、候选Release或社交发布。

## 2026-10-05 · 完整发丝核查、实际头框与局部梳理对照（未完成）

已确认用户下载的 Fab hairstyle.blend 在指定 Source/FabMediumLayered 目录，原文件哈希保持。逐根读取 54,764 根粒子的全部 8 个保存键，与前缓存根/尾比较，差异最多 3.73e-9m；三组长度中位数约 25.5/28.7/31.5mm，没有漏掉隐藏长尾。它仍不匹配参考的中长碎发。

按实际求值头部校正 Fab 的缩放/平移，fabfit05 发根修正中位数约 2.8mm、90%约 8.7mm，原试验分别约 4.8/21.2mm。但三分之四实渲依然是短梳发，不采用；根部贴合改善不能证明造型合格。

原创 cubic Bézier 两束小样 bezierlock01—03 均已读图，03 近景能看清细纤维；组成 44 束/22,000 根的 cubicshag01 后，四视角显示分离条带、耳后拱形和冠部空隙，明确否定。隐藏控制曲线是烘焙证据，不是实时连接。不能把两束成功迁移为完整发型成功。

转回稳定 napeunderlay02 的完整覆盖作局部试验：settledshag01 轻收侧面、统一材质；02 同几何色素对照偏橙棕，否定；03 在01基础上仅沿侧后发丝逐段保长弯向下方、加根部相干缓弯。03四张实际草稿已查看，外翘减少且覆盖保留，但冠部仍厚、后脑仍圆，是局部研究，不替换稳定WIP。五视角较高采样结果另外记录。

八个候选与稳定基础做成对静态检查，原141个网格的几何/UV/形态键/变换保持；可见原生曲线有限值、正半径和贴图可用性通过。这不是艺术验收，也不是发丝段、服装、眼睛、动作的完整碰撞保证。稳定WIP、Fab源文件及六项无关文件哈希保持。原/衍生几何留本地；同步代码、聚合记录与精选实渲，没有新付费、AI肖像替代、动画、UE接入、候选Release或社交发布。目标仍进行。

五视角复核已完成并逐张查看：`Renders/settledshagcheck03`，1200×1400 / Cycles OptiX192 samples / 不去噪，源工程 settledshag03 的文件哈希未改。侧面外翘有所降低，但冠部仍厚、后脑仍圆；另一侧也有宽束感。仍未通过参考级作品验收，不替换 napeunderlay02 稳定基础。下一步须处理冠部宽束与后枕流向，不能靠提高采样或继续加密解决。

## 2026-10-05 · 原生波浪发根重铺、生成后剪裁与材质对照（未完成）

复核历史 layercut04 的实际四视角，侧后波浪与后颈长度比近期碎束更贴近参考，因此在保留 napeunderlay02 的全部身体/衣物网格的副本中重新导入其可见原生毛发，隐藏但保留全部旧毛发。没有修改或覆盖历史工程。

nativeroot01 先重铺正X侧局部12,737根发丝的前48%到实际头皮的柔和抬升层；看图后扩大到02的28,464根前/冠部发根。完整发梢与侧后波浪保留，根部硬拱减轻，但刘海仍有宽带。测量02最高发丝发现小冠部拱起集中在负X约-0.02m处，而历史压缩集中正X。03将这个实际局部拱起收低；四视角已查看，改善有限，不能称参考级完成。

新对照 postscissor02 不再改写源导向线，在原生梳理节点完整求值后再分区剪短，仅提高插值密度并在输出设置物理半径。它没有同样的硬刘海拱起，但额头裸露、后脑圆滑，单视角即否定为目标造型。01在读取链接的Radius输入时报错，无可用工程，日志保留；修复仅移除无须修改的源半径输入，改用输出半径。

nativecompose01保留postscissor02自然冠部与侧后，加nativeroot03完整前额发丝11,092根；四张草稿已看，未发现显著头皮断缝，但冠部/后脑更圆，否定为进一步基础。不是按发丝点拼实心外壳。

nativelobe03是03的材质对照，原生方向性Hair BSDF过暗/扁平，否定；04以原Principled分支混入25%方向性分支，略减偏粉高光并保留体积，仍只是检查候选。前两次材质脚本因枚举大小写与不存在的HairInfo Tangent输出提前报错，无模型；按实际API修复，不复用失败目录。方向性分支采用未连接的默认Tangent输入，没有声称显式读取不存在的输出。

目标仍进行：当前较值得继续雕刻的候选为nativeroot03及其04材质副本，仍有前额宽束、冠部团簇、侧后层次不足。稳定备份napeunderlay02不替换，没有艺术验收、动画/UE接入、新候选Release、社交发布或付费。所有毛发仍为实际可编辑三维，未用生成肖像替代。继续处理可见造型，不能仅靠更多密度、采样或压暗来达标。源/衍生几何仅留本地；加工源码、聚合清单与精选实渲同步。

2026-10-05五视角补充复核：nativecheck04（1200×1400 / OptiX192 / 不去噪）五张均已查看，另一侧暴露了此前单视角看不出的鬓角上方明显头皮缺口，04没有通过完整造型检查。随后保存nativecoverage05，在相同完整主发型下恢复Abhay14,000、Bystedt23,657与原创后枕36,000根短底发，并统一为主发材质；没有新增实心头皮帽或重画贴图。

nativecoveragecheck05同规格五张均已查看：头皮裸露减轻，长侧后波浪/后颈保留；仍有前额宽带与冠部团簇，未达到参考级作品。当前继续雕刻候选为Exports/nativecoverage05/Ember_Regent.blend，稳定备份napeunderlay02不覆盖。七个试验成对静态文件检查通过，方向性材质03/04的可见曲线几何哈希与nativeroot03完全一致；另一个05成对检查证明主发与04、恢复短底发与稳定源的几何完全一致。原141个网格/UV/形态键/变换保持，可见原生曲线有限值、正半径和贴图可用性通过。只证明静态文件，不是艺术验收、全发丝段/服装/动画碰撞证明。六项无关文件和所有源/稳定工程哈希保持。

## 2026-10-05 · Blender版本实证与源节点梳理对照（未完成）

Fab 原 hairstyle.blend 已确认保留。安装官方便携 Blender 5.1.2 于 D:\tools\Blender，ZIP 的官方 SHA-256 校验通过，旧 4.5.9 保留。4.5.9/5.1.2 在 frame_set(1) 后读取**求值粒子**，54,764 根的全部 8 键逐字节一致，共有标量设置一致，新增 API 属性仅 is_linked_packed。两张原素材同机位实渲均查看，仍为短梳发；8位RGB平均绝对像素差约0.00487。只能排除这次粒子/设置/控制视角的跨版本解释差异，不能泛化为所有Blender功能兼容。早期01数据探针读取了未求值的零键，不能作为几何证据；修正后的02要求非零求值长度，错误探针保留本地。

现有发型新试验全部为真实几何、独立版本：nativesublayer01两组浅分层、nativesections01六组更深分层均改善有限；nativerods01近似静态杆松弛令部分刘海垂到眼前，否定；crosspart01反向梳理出现交叠宽S片，否定。没有推广到整头，也没有称为物理动画。

源节点梳理：nativedeclump01改到一个未链接Factor和三处末端散开/偏移，两个链接Factor未改，不是完整的Factor对照。02通过Math乘法保留两个上游控制轮廓，并有效缩放三个Factor至原强度的55%；03同流水线保留原强度作配对，04只将Roll从0.18降至0.03。每版一张960×1120/OptiX96/不去噪实渲均已查看，仍有冠部团簇/刘海宽片，不采用作新成品。记录参数只能说明这些源控制试验，不能证明逐项复现了历史layercut04未记录的所有运行选项。

八个工程成对静态检查保留原141个网格/UV/形态键/变换，原生曲线有限值/正半径/贴图可用；短底发几何与nativecoverage05完全一致，前四个局部改梳工程的全部主发根也逐字节一致。源节点02/03/04的主发半径相同，根与位移差异另见native_source_pairs06.json。这些不是艺术验收或完整头发段/眼睛/服装/动画碰撞验证。

**目标仍进行，当前继续雕刻候选保持nativecoverage05，稳定备份napeunderlay02不替换。** 本轮没有合格新发型、动画/UE接入、新候选Release、社交发布或付费。源/衍生几何保持本地；仅同步加工源码、聚合记录和已查看的角色实渲。Fab与Bystedt源文件、稳定模型及六项无关修改哈希保持。


## 2026-10-05 · 主枝归因与贴头刘海设计（继续打磨）

Fab hairstyle.blend 已在本机，原文件哈希保持，无须再下载或确认协议。原生源枝隔离 nativebranches07 的三张实渲已查看：主枝49,118根承担冠部/刘海宽束，装饰枝150根且前额末梢0；不能靠移除装饰枝解决。nativeaffine08整根全局仿射转移仍有宽束，未推进；旧清单通用method误提root reflow，实际head_transfer明确禁用，生成器已改成条件记录。

nativefront09按实际头皮重设计231组/11,092根刘海，所有根和未选主体保持，缓解硬拱；五视角显示太顺滑，另一侧仍有浅色底发。nativefrontwave10加入小幅相干波浪与±6mm长短分层；nativefrontwavecheck10五张1200×1400 / OptiX192 / 不去噪均实际查看，刘海更柔和、双眼清楚，侧后原波浪保留。**后续雕刻从nativefrontwave10继续；这是局部WIP，未通过作品验收，目标仍进行。** nativecoverage05和稳定napeunderlay02保留，后脑宽带、冠部宽束和另一侧浅色底发仍待解决，面部/服装也未达参考。

nativefinish11仅换Principled颜色/粗糙度的两张对照实渲偏粉，否定；全部毛发几何与wave10完全一致。nativepart12改2931根/248个实际根部分区，两个角度显示浅色分缝改善不足，否定为解决方案。其全部根和未选主体与wave10精确一致。没有通过随机重跑或材质压暗冒充形状修复。

六个工程成对静态检查保留141个网格/UV/形态键/变换、有限曲线、正半径和可用贴图；短底发均与nativecoverage05一致。09/10的全根与非刘海主体精确保持。这些检查不能证明艺术合格或完整头发段/眼睛/服装/运动碰撞安全。隐藏设计导向是烘焙证据，未实时连接。源/衍生几何和local_guide_design坐标文件仅本地；只同步源码、聚合记录、实际查看的角色渲染。六项无关文件、Fab/Bystedt源与稳定工程哈希保持；没有新付费、AI肖像替代、动画/UE接入、候选Release或社交发布。


## 2026-10-06 · 短底发归因与侧后渐变剪层（继续）

nativeids13两张真实组件分色图已查看：另一侧浅色分缝以Abhay短底发暴露为主，部分后冠还有原创后枕短支撑露出。nativeunderflow14改4179根/335个8mm根区为贴头中间层；两张实渲显示浅色区域减小，不能称完全消除。nativevisibility16用真实另一侧相机、480×560点深度/.7mm容差估计冠部可见曲线，主发2142根、Abhay451根；这是离散点归因，非连续遮挡或全量碰撞证明。局部索引仅本地。

nativecrowncut15按高发根剪17379根，三张实渲改善有限；nativecrownflow17把3593根短末梢主发下梳，两个角度顶部变平，否定。nativelayerflow18保留设计刘海，对38176根非前额主发以2618个真实根/尾流向分区剪连续75%—98%长度、收窄发尾并加小幅相干横向波浪。nativelayercheck18五张1200×1400/OptiX192/不去噪均已查看，耳后/后颈层次和发尾分离有改善，但冠部/后脑宽带、另一侧浅色分缝仍在。**后续继续从Exports/nativelayerflow18/Ember_Regent.blend雕刻，目标尚未完成；nativefrontwave10、nativeunderflow14和稳定napeunderlay02保留。**

nativepresentation18为同一模型/同灯光机位的实际1920×2240/OptiX512/OpenImageDenoise图，已查看；细发更清楚、噪点降低。去噪属于渲染处理，不能当成修复三维形状，更不是生成肖像替换模型。下一步须细分冠部宽流向、改善分缝衔接；不要重复已失败的整块下梳或仅靠提高密度/采样称完成。

14/15/17/18四个源-候选本地对照检查通过：141个网格/UV/形态键/变换精确保持，改动毛发全部根/半径/拓扑/变换、未选发丝和其他毛发组件精确保留，曲线有限/半径正/贴图可用。范围为静态文件，不是艺术合格、发丝段/眼睛/衣物/运动的全量碰撞保证。六项无关文件、稳定模型与Fab/Bystedt源哈希保持。仅源码、聚合记录和已查看实渲同步，原/衍生几何与索引不上传；没有新费用、动画/UE接入、候选Release或社交发布。


## 2026-10-07 · 刘海长度与逐根贴头对照（目标未完成）

Fab hairstyle.blend 已在指定目录，无需重下。19同侧帘发暴露额头且出现硬弧，否定；20仅在已有231组额前截面收窄/错层，改善有限；21在20上延长错落8643根/152组刘海发梢，五张中性视角及1920×2240/512样本实际近景已查看。**当前继续雕刻基础改为 Exports/nativefeather21/Ember_Regent.blend；18及稳定napeunderlay02保留。** 刘海更接近参考，冠部硬拱/宽带、另一侧浅色短底发和后脑宽带仍未解决，不能当作品完成。

22/23在不改几何/灯光/颜色输入下对照Huang .45/1/.80和1/1/1，均过暗、细丝结构变弱，否定。旧清单geometry_lighting_pigment_unchanged措辞仅能指颜色输入不变，不证明跨模型有效吸收等价；旧记录保留，未来生成器字段已澄清。24逐毛囊贴头弧线把冠部压成光滑片；25叠加头皮角度相干波浪仍为宽S片/不匀轮廓，否定，不继续仅更换振幅重试。

七个成对静态检查保留141个网格/UV/形态键/变换、全部根/半径/拓扑、未选发丝和其他毛发；22/23最大几何位移为0。检查不代表艺术验收或完整发丝段/眼睛/服装/动画碰撞安全。源/衍生几何仅本地；同步源码、聚合记录、已看实渲。六项无关文件、源文件和稳定备份哈希保持。没有新费用、AI肖像代替建模、动画/UE接入、候选Release或社交发布。


## 2026-10-07 · 分缝短底发贴伏与冠部小样（继续，未完成）

重新看组件ID，三分之四视角分缝还暴露Bystedt短底发（此前另一侧主要为Abhay，不能混为同一组件）。nativepartunder26只改中央上部分缝14025根短Bystedt发丝：最近长发根中位0.089mm/最大2.171mm，以对应主发实际流向和原短发长度决定行进，再用16个真实头皮控制点/0.8—2mm抬升贴伏。没有改主发/材料/灯光。短发最后长度不是严格保长；记录了8.27—34.67mm分布，不声称动力学模拟。

两张草稿、nativepartcheck26五张1200×1400/192/不去噪、nativepresentation26实际1920×2240/512/OpenImageDenoise近景均已查看，三分之四分缝银灰绒毛减轻，长刘海保留，未见新明显缺口；另一侧浅色区域、主发冠部宽拱/后脑宽带仍存在。**当前继续雕刻基础为 Exports/nativepartunder26/Ember_Regent.blend；21、18与稳定napeunderlay02保留。目标仍未完成，面部与服装也还需后续打磨。**

27同方法只贴伏8846根原创上后冠短底发，已看两个角度及背面，变化小，未推进。28保留完整覆盖叠三束2100根原创细发，实渲像悬空细绳，否定；测得主发最高1.88408m，小样拱顶1.898—1.904m，身体矩阵为单位矩阵、离散点接触修正0，并非坐标变换错误。29按主发离散点场贴合1.2mm偏移再平滑，虽降低悬空却出现折线/亮结，否定，不扩展全头。

26/27局部静态成对检查保留141网格/UV/形态键/变换、全部根/半径/拓扑及未改发丝；28/29加法检查证明原141网格与全部四个可见毛发组件逐字节保持。检查不等于艺术合格、全发丝段/眼睛/服装/动画碰撞验收。源与衍生几何仅本地；同步源码、聚合证据和已看实渲。六项无关文件、稳定模型、Fab/Bystedt源哈希保持，无新费用/AI肖像替代/UE接入/动画/候选Release/社交发布。


## 2026-10-07 · 后脑整根路径分束与连续截面（继续）

30先只读地按完整路径五点采样聚96组非前额主发（38176根），不再按根/尾小格分组。分组中段90%截面宽中位18.16mm、厚8.86mm，是分组统计，不等于独立测得每个视觉亮带的宽度。正式工具35复现全部ids/labels精确一致；源模型哈希保持，索引仅本地。

31对后根/后尾41组16914根收为7—9mm宽/2.8mm厚并收尾，保留原纵向散布/流向，三个草稿已看：发尾分离，后脑宽亮带仍在。32实际蓝色改过主发/红色未改主发/绿色底发分色已看两角度，确认中后宽带依旧属于已改主发，截面收窄不够。33按真实中心弧长85mm波长、6mm侧/3mm深度错相松弯，宽带有所打散，但末梢仍杂；34把新增卷曲在最后32%渐退，改善有限。

36数值诊断：这41组旧径向截面有11次相邻朝向反转、28次超过60°旋转，连续平移截面对同组的反转为0。37改为连续截面、松弯和放松尾段；截面宽度门槛重测后少了旧36组的141根，实际40组/16773根，因此不是完全隔离的朝向单变量对照。三个草稿、nativebackcheck37五张1200×1400/192/不去噪及nativepresentation37真实1920×2240/512/OpenImageDenoise近景均已查看：后脑波浪、自由发尾更清楚，刘海保留；冠部宽拱、上部宽束、另一侧浅色短底发仍在，尚未达到参考作品质量。

**继续打磨基础改为 Exports/nativebacktransport37/Ember_Regent.blend；26、21、18与稳定napeunderlay02均保留。目标仍进行。** 下一步处理上部冠/额前宽流向与分缝衔接，不能把后脑局部改善当整头完成。面部、服装仍需后续独立打磨。

31/33/34/37四个局部静态成对检查保留141网格/UV/形态键/变换、全部根/半径/拓扑、未选发丝和所有其他毛发；生成器另断言首四点保持。不是艺术验收或全发丝段/眼睛/衣物/动画碰撞证明。源/衍生几何与局部索引仅本地；仅源码、聚合记录和已查看实渲同步。六项无关文件、稳定模型和Fab/Bystedt源哈希保持，无新费用/AI肖像替代/动画/UE接入/候选Release/社交发布。


## 2026-10-07 · 冠部漏选定位与小束雕刻（目标仍进行）

38按整根路径将11092根额前发丝聚32组；39/40各改10996根/29组，三个草稿均已查看，但顶部轮廓变化小，均不采用。40直接从37生成，没有接39。41峰值探针因空集quantile失败，无有效结果；日志留本地。正式42安全处理空集并分全主发所有权：z>1.878m的2038根全部在未改非前额主发，额前与已改后脑均为0；这是几何统计。43两张实际分色又确认高发丝覆盖可见头顶拱，不能泛化为所有宽带都已归因。

44先针对漏选高冠family5的1483根做整根路径8个小组，连续截面局部收窄、降低3.5—5mm并加温和细弯；三个草稿已看，再扩大45到family5/20/33/62共3379根，仍独立从37生成。45三个草稿、nativecrowncheck45五视角1200×1400/192/不去噪和nativecrownpresentation45实际1920×2240/512/OpenImageDenoise近景均已查看。顶端硬拱有所收敛，37的侧后波浪和发尾保留；冠部仍圆且有共同宽流向、分缝短底发仍可见，尚未达到参考级作品。

**后续继续雕刻基础为 Exports/nativecrownsection45/Ember_Regent.blend；37、26、21、18与稳定napeunderlay02均保留。** 不把微小改善当达标。后续应处理可见额前宽流向与短底发衔接；不要继续无归因地更改同一刘海参数。面部/服装另需打磨。

46/47用纯Chiang明确重标色素与粗糙度，未假设跨模型颜色等价；两版各两张实渲已看，依然粉白，否定。四个局部成对静态检查保留141网格/UV/形态键/变换、根/半径/拓扑、未选发丝与其他毛发；两个材质成对检查额外证明全部可见发丝几何、灯光/世界/相机/显示设置精确不变。检查不是艺术或全发丝段/眼睛/衣物/运动碰撞验收。六项无关文件、源/稳定/37哈希保持；源与衍生几何、局部索引留本地。仅同步源码、聚合记录、已查看实渲，无新费用、AI肖像替代、动画/UE接入、候选Release或社交发布。


## 2026-10-07 · 实际机位分缝归因与另一侧额前设计（继续）

Fab hairstyle.blend 已在本机且哈希保持，无须再下载。48真实组件分色和55新增束分色均已看：54/56的负X补发多数在目标机位被遮住。49替换负X底发露出新头皮区，否定；50仅改1/3虽保住更多覆盖，仍无明显造型进步。51只读探针确认可见刘海末梢低于先前z1.800门槛；52/53收窄两个/六个宽末梢组，仅小幅改善，不采用。

57按目标三分之四相机的实际画面ROI反查所有组件。507根Abhay可见点所属发丝的发根X中位+49.89mm，409根Bystedt中位+41.61mm；因此前几轮只改负X区域不足以覆盖这个机位。此为480×560离散点深度/.7mm容差近似，没有身体遮挡或连续光线证明，不能泛化为所有视角的归因。索引仅本地。

58在正确正X ROI发根上补455根连续供体路径，实渲变化仍小；59在正X额前真实毛囊补1027根明确鬓角卷束，只有细碎变化，均不采用。60直接把6103根正X/前部主发改为10组额前轮廓，覆盖更清楚但束太齐；61独立从45将同一区域聚为30组，实际改29组/6074根并错开卷向/长度，29根的小组保留。三个草稿、nativefrontcheck61五张1200×1400/192/不去噪及nativefrontpresentation61真实1920×2240/512/OpenImageDenoise近景均已逐张看过。另一侧额前层次比45完整，双眼仍可辨，侧后波浪保留；冠部共同宽流向、浅色短底发和过长后颈仍未解决，面部/服装尚未达到参考。

**后续打磨基础改为 Exports/nativefinefront61/Ember_Regent.blend；45、37、26、21、18与稳定napeunderlay02保留。目标仍进行，不能当可发布角色作品。** 62再沿61的实际主发根路径延长1304根正X Abhay短底发，三个角度变化小，未推进。下一步优先处理冠部宽束/短底发衔接和更紧凑的侧后层次，避免重复不可见补丝。

七个局部与四个加法静态对照通过：141网格/UV/形态键/变换保持，有限曲线/正半径/贴图可用；局部版全部根/半径/拓扑/未选发丝和其他组件保持；加法版所有旧毛发精确保持、新根为实际源根子集。检查不等于艺术合格、全发丝段/眼睛/衣物/运动碰撞保证。六项无关文件、稳定/45/37模型、Fab/Bystedt源哈希保持。原/衍生几何及索引留本地，仅源码/聚合记录/已看实渲同步；无新费用、AI肖像替代、动画/UE接入、候选Release或社交发布。


## 2026-10-07 · 分层后颈剪裁与低发根漏剪修复（继续）

63首次读取探针路径误写为nativebackflow30，报文件不存在，没有生成模型；日志保留本地。实际索引在nativeflowprobe30。64只剪较高/后部主发15621根，三个实渲显示主体变短但残留几束长尾，齐边感偏重，否定。65独立从61按实际低发梢选区剪16398根，长度/层间错开更大，但长尾仍在，不采用。

66三张真实组件分色已看，残留长尾属于红色主发。67只读全主发探针定位1309根未剪且发梢低于1.665m的发丝：根Z中位1.70536m、索引3中位1.69934m、索引11中位1.68338m、尾Z中位1.60175m，均不在新额前frame里。点索引为零基，索引3/11分别是第4/12个点。它们在旧算法从索引12开始查找前就已低于部分剪切目标，导致交点条件失效；另有较低根目标高于保留起始段的问题。这里是几何统计，实际可见归因由66补足。

68独立从61保留全部真实发根和前4点，从索引4找首个交点，将目标最高限制在保留索引3下12mm，最低剩余尾弧门槛从18mm改3mm，实际剪17705根。三个草稿、nativeentrycheck68五张1200×1400/192/不去噪和nativeentrypresentation68实际1920×2240/512/OpenImageDenoise近景均已看过：衣领附近悬长尾已收掉，侧后/后颈轮廓更紧凑，额前层次保留。仍有冠部宽共同流向/浅色绒毛感，不能当参考级完成；面部服装也尚待后续。

**后续打磨基础为 Exports/nativeentrynape68/Ember_Regent.blend；61、45、37及稳定napeunderlay02保留。目标仍进行。** 下一步须实际处理冠部分束与短底发衔接；不能靠更多采样或只压暗遮盖宽束。

三个局部静态对照保留141网格/UV/形态键/变换、全部毛发根/半径/拓扑/变换、未选主发与其他组件。额前frame的实际6074根与所有主发前4点逐字节保持。68全部主发末梢最低1.65150m、低于1.640m数量0；64/65该数量分别2119/1307。此门槛仅验证主发长尾修复，不证明整头艺术质量或连续发丝段/衣物/动画碰撞。六项无关文件和保护模型/源哈希保持；仅代码/聚合证据/已看实渲同步，原/衍生几何和索引留本地，无新费用/AI肖像替代/动画/UE接入/候选Release/社交发布。

61计数说明已更正：30是目标分组数，实际29组合计6074根被重塑，另一个29根的小组按阈值保留；此前6103是选区总数，不是61实际改动数。原工程和原静态检查不变，生成器/概要措辞已修正。


## 2026-10-07 · 底发反光隔离、冠部抬升与过渡层复核（未完成）

Fab原文件已本地保存且哈希保持，无须重新下载。69只改三层底发中的实际Principled Hair粗糙度/径向粗糙度，三个实渲改善很小，未采用。原始69清单通用method误写了标准Principled参数；源中没有该节点，实际changes只有Hair Roughness .55/Radial .60，概要与生成器已更正，历史原清单本地保留。此对照未改旧Hair反射/透射分支，不能说已排除所有反光解释。

70仅把主发材质重标红色色素并换为纯Huang，三张实渲更鲜红，但形状/浅色底发未解决，未采用。71独立从68把负X上冠1647根选区聚18组，实际14组/1588根收窄和抬升6—10mm，其余59根小组保留；三个实渲只见小幅轮廓变化，未采用，没有混接70材质。72仅把三层底发已有Chiang节点直连Surface、移除有效混合中的25%旧定向分支，保留节点参数与原色素；两张实渲仍浅且绒，未采用，不泛化为所有材质都已排除。

73将4868根正X上侧Abhay底发改为沿实际主发供体的中长过渡层，三张实渲改善有限。74真实组件分色两张均看过：三分之四视角仍露出绿色Bystedt短底发和橙色原创后枕底发，另一侧则有蓝色Abhay；只是这些机位的可见归因。75独立从68重塑9067根正X原创后枕底发，再从75生成76、改16082根Bystedt短底发。75/76各三张草稿和76重新打开保存工程的1920×2240/512/OIDN实际近景均已看过：浅色梳齿/绒毛未解决，76上部分缝还露出小块肤色，不采用。105mm只是供体路径行进上限，根偏移/身体修正后的最终曲线弧长可更长；不称严格保长或物理模拟。

**没有值得替换的新造型，继续打磨基础仍为 Exports/nativeentrynape68/Ember_Regent.blend；61、45、37和稳定napeunderlay02保留。目标仍进行。** 本轮结果说明单层供体跟随/小幅抬冠不能完成分缝设计，应进一步设计主发覆盖与底发共同流向，不再把同类小参数重试当主要突破。

七个有范围的静态源-候选检查保留141网格/UV/形态键/变换、根/半径/拓扑、未选发丝和其他组件；69/70/72还独立比对材质图/槽位，证明改变仅在约定support或primary范围，网格材质和其余槽位/图精确保持，灯光/世界/相机/显示不变。71额前6074根、前4点、短后颈门槛保持。76重新打开后四个可见毛发组件保存坐标与frame1求值坐标逐字节一致，排除了该次坐标被求值覆盖的解释，不证明所有渲染后端/动态。检查不代表艺术验收或连续发丝段/服装/动画碰撞安全。六项无关文件和源/稳定工程哈希保持；仅代码、聚合证据和已看实渲同步，原/衍生几何及索引仍本地，无新费用、AI肖像替代、动画/UE接入、候选Release或社交发布。


## 2026-10-07 · 主发入根归因与完整侧发重设计（继续，未完成）

上一轮有进展：材质范围与保存求值检查明确了失败边界，本轮不重复底发材质小参数。77加载68临时隐藏全部三层底发，三张真实beauty仍见浅色侧冠梳齿，同时另一侧暴露头皮；因此此前底发ID说明这些组件确实露出，不能解释成所有浅色都属于底发。78按保存主发点0—7/7—16/16—32/32—64直接分段分色，两张均看过，目标三分之四区域主要为蓝色0—7入根段。79只读探针选22522根正X上侧主发，前8点弧长中位13.20mm、第7点最近头皮有符号点间隙中位4.73mm、半径约37μm；只是区域几何统计，不是全部可见性/连续碰撞证明。

80不再固定首4点，对21481根/362小区的点1—15做贴头切向小束，三张草稿出现密集小结，不采用。81独立从68重做16448根/80组完整侧发，保留6074根明确刘海，浅色梳齿减轻，但同高度卷束太整齐。82也独立从68采用高根短层/低根长层，三个草稿、五中性视角及512样本实际近景均看过：轮廓更错落，但Side03太阳穴上方露出更明显的稀疏肤色。83还原279根点ROI选中的68路径、84均匀还原4146根68旧路径，效果不足；85把6602根81长卷路径混入82短层，仍有稀疏，三个版本各三张草稿均看过，不采用。ROI筛选是手工观察后的离散投影近似，不宣称光线可见性。

86按实际前后毛囊区域组合：正X已改侧发中Y<-20mm的9140根使用81完整长卷，其余7308根保留82短层；没有增加总发丝密度或更换材质。三个草稿、nativefoundationcheck86五张1200×1400/192/不去噪、nativefoundationpresentation86实际1920×2240/512/OIDN近景均已查看。相对82太阳穴覆盖更完整，原梳齿侧冠明显减轻，刘海和短后颈保留；还有浅色分缝/局部薄处、头顶与额前宽平顺片、重复卷束，尚未达到参考。**后续打磨基础改为 Exports/nativefrontfoundation86/Ember_Regent.blend；68、61、45、37及稳定napeunderlay02保留。目标仍进行，不当可发布作品。** 下一步处理宽片与重复卷束，不能只提高采样或隐藏底发当完成。

七个局部成对文件检查保留141网格/UV/形态键/变换、真实根/半径/拓扑、未选主发与其他毛发，独立证明全部材质图/槽、灯光/世界/相机/显示精确不变；80保留点16—64，81/82与四个混合版本保留6074根明确刘海，主发低于1.640m的末梢均为0。85/86另独立比对供体文件，选中保存路径逐字节等于81。首4点保持只是前几轮的方法边界，本轮实际毛囊仍保持，允许改入根方向。检查不是艺术验收或连续发丝段/眼睛/服装/动画碰撞保证。六项无关修改、源与保护工程哈希保持；源码/聚合证据/已看实渲同步，原/衍生几何本地，无新费用、神经重建/AI肖像替代、动画/UE接入、候选Release或社交发布。


## 2026-10-07 · 上冠分层抬升与局部卷环修正（继续，未完成）

Fab hairstyle.blend 已在本机，不需再次下载/接受协议。87读取86实际主发分区做两张分色：6074根明确刘海为红、16448根已改侧发为蓝、9306根其余上冠为绿、17440根其余主发为橙；两个机位中宽上部同时属于蓝/绿，不能只继续改底发。分色临时隐藏底发，未保存源工程，不代表最终发色。

88从86对23410根上部主发按150个毛囊区做连续截面分束/5—14mm宽弧抬升，保留明确刘海和点44—64。三草稿与512样本实际近景已看：宽片有层次，但出现分缝硬拱/突丝，不采用。89只读离散点诊断：新转角>85度且较原增加>30度、Z>1.860m的上部发丝27根；峰>1.900m为0。这不能解释所有视觉硬束或证明连续曲线安全，索引仅本地。

90独立从86按点0/8/16/24/40整根前中段流向聚150组，实际146组/23385根改动，4个小组共25根保持；最大位移20.832mm，88为40.690mm。三草稿、五中性视角及512样本近景均已看：上部层次更明确，硬折线比88减轻；另一侧有过度拱起的卷环。两版实际选区不同25根，不能说严格隔离分组方式单变量。91也独立从86按原中心导向累计转角100—180度降低额外抬升/侧摆到35%，61组强度<.9，三个实渲仅小幅变化，不采用。

92从90按实际另一侧画面椭圆/向上位移阈值，8138根还原86完整路径，三个实渲侧后卷环减轻，分缝硬拱仍在。93再从92按正面分缝椭圆还原857根，三实渲正面硬拱减少，但有小簇突起。94直接从90结合两机位：8995根初选，按精确复现的整根流向组修正为55组/9816根完整还原86，13569根90抬升路径保留；避免在同束里只剩几根高丝。ROI只是手工观察后的离散投影筛选，不是光线可见性证明。

94三草稿、nativecoherentcheck94五张1200×1400/192/不去噪、nativecoherentpresentation94实际1920×2240/512/OIDN近景均已查看。比86上部更分层，比90突出的卷环/分缝硬拱收敛，侧面覆盖、短后颈、刘海保留；仍有宽厚额前束、重复弯曲、小簇侧冠突起、浅色分缝/后冠，脸和服装也未到参考。**后续继续基础为 Exports/nativecoherentrelief94/Ember_Regent.blend；86、68及稳定napeunderlay02保留。目标仍进行，不发布为完成作品。** 下一步应定位剩余侧冠突起实际组件/流向并处理宽厚额前层次，避免只改抬升数值或继续整片还原。

六个静态成对文件对照通过：141网格/UV/形态键/变换、真实毛囊/半径/拓扑、未改主发与其余三毛发组件、全部材质图/槽与灯光/世界/相机/显示精确保持，6074根明确刘海和短后颈门槛保持。92/93/94额外独立证明选中完整路径逐字节等于86供体。生成器保留全部点44—64；不把静态检查当艺术或连续发丝段/服装/运动碰撞验收。六项无关修改、源/保护模型哈希保持。仅同步代码、聚合证据和已看实渲，源/衍生几何、索引、日志仍本地。无新费用/AI肖像或神经重建替代/动画/UE接入/候选Release/社交发布。


## 2026-10-07 · 冠部中心导向放松与后冠短底发修剪（继续，未完成）

Fab文件已在Source/FabMediumLayered/hairstyle.blend，源哈希保持，无需下载。95三个真实分色定位到保留90抬升family的侧冠小峰；96精确复现86的150整根流向组，对94保留的91组/13569根减去70%新增正法向中心导向位移，保留组内截面收缩、侧摆、真实根、44—64点及6074根明确刘海。三个实渲已看：小突起消退、冠部更顺。

97两个真实分色确认后冠浅色绒毛包含原创后枕底发。98从96修剪7881根原创底发，沿当前主发近根走向做0.25—0.65mm贴头短层，原中位50.744mm缩到5.208mm；控制行进上限不是最终几何弧长严格上限。三个草稿、五中性角度及1920×2240/512/OIDN实际近景均已查看，后冠银灰绒毛明显消退，仍有窄肤色分缝。99进一步处理14782根Bystedt底发，三个实渲收益小，未采用。

100从98将上前部原流向组横向分成三小束，收窄38%，错开1.8mm侧摆及0.5—2.3mm高度；三个实渲变化细微，额前宽束/浅斑仍在，不采用。没有靠新材质、加采样或AI肖像替代造型。

**继续打磨基础改为Exports/nativeshortveil98/Ember_Regent.blend；94、86、68及稳定napeunderlay02保留。目标仍进行。** 厚宽额前束、重复弯曲、额前浅色分缝还未到参考，面部/服装也未达标。下一步应重新设计可见额前主导发束的弧线与层间轮廓，避免重复微量同束收窄或短底发参数。96的分色保留90family指的是来源归属，实际导向已改变，不能说仍是精确90几何。

四个局部静态文件对照通过：141网格/UV/形态键/变换、根/半径/拓扑、未选丝与其他毛发、全部材质/灯光保持；主发编辑96/100还保留6074根刘海与短后颈门槛。离散点修正不代表连续碰撞或艺术验收。六项无关修改及保护工程/源哈希保持。代码、聚合记录和已查看实渲同步；原/衍生几何、逐丝索引与日志仅本地，无新费用、神经重建、动画/UE接入、候选Release或社交发布。


## 2026-10-07 · 额前整束重设计失败边界与新几何上的红色色素（继续）

上一轮96/98冠部/后冠改善为实质进展。本轮不继续微量收窄；101从98对15257根上前部主发重建完整65点切向立方弧线，64目标毛囊组跨偏分缝组织，三张实渲显示大盖子式过齐流向，否定。102也独立从98，仅处理6350根高中央冠发、36目标组，做前落长短错位；三张实渲仍偏圆、分缝有浅色峰，不采用。两版没有混入后续主工程。

103将已有70的主发纯Huang/重新标定红色色素方案复用到已改善的98几何；与先前68上的70对照区分。原75%Chiang/25%定向混合替换为纯Huang，线性色素RGBA(.11,.005,.007,1)至(.25,.013,.015,1)，Roughness .32、Random .12、Reflection .55、Transmission1、Secondary .85。没有声称跨模型吸收参数等价。三个草稿、五中性视角与1920×2240/512/OIDN真实近景均已查看：红色更贴近参考，主发部分刺眼灰白带明显减轻，仍有较浅的分缝/底发，额前宽片和重复侧弯仍在。

**继续基础为Exports/nativecrimsonflow103/Ember_Regent.blend；98、94、86及稳定napeunderlay02保留。目标未完成。** 103是材质改善，绝不当成几何造型已达标；下一步处理宽额前弧线与小束交错，避免再次将整块上冠做成同一方向的光滑盖子。面部/服装仍需后续打磨。

101/102局部静态对照和103材质范围对照通过：141网格/UV/形态键/变换，毛囊/半径/拓扑、6074根明确刘海、未选发丝/其余毛发保持；101/102材质灯光精确保持。103全部可见毛发保存几何逐字节保持，身体/网格/三层底发材质图槽位与灯光/相机/显示精确不变。103首次校验命令错误传了不存在的unused属性，失败无报告；查明后传已有native_layered_root_lofts，完整材质对照通过，没有重做生成。检查不是艺术或连续碰撞验收。

六项无关修改、Fab/Bystedt源与所有保护工程哈希保持。原/衍生几何、逐丝索引和日志仅本地；同步源码、聚合报告与已查看实渲，无新费用、AI肖像替代/神经重建、动画/UE接入、候选Release或社交发布。


## 2026-10-07 · 真实刘海交错重塑（继续，未完成）

上一轮103红发材质改善已保存同步。本轮104以真实毛囊/整根相似流向选择十个锚点目标中的八小组/572根做稀疏顶部翘束，三张实渲仍有细小悬拱，不采用，不增加发丝或重复旧脱根补发。

这次不把旧61的6074根刘海继续冻结为艺术要求。105独立从103，按实际全路径聚54目标组，8539根重塑中6038根来自旧61刘海、2501根来自负X额前，36根小组旧刘海保留。增加9—14mm交错弯曲、4mm末梢回摆、40%横截面收窄和5—23mm抬梢；三个实渲额前偏短，不采用。106也直接从103生成，同一8539根选区保留交错弧线，但取消设计上的抬梢。真实身体离散修正仍可能移动某个梢，不能称逐点末梢高度严格不变。

106三个草稿、五张1200×1400/192/不去噪中性角度和1920×2240/512/OIDN保存工程实渲均已查看。长刘海保住，额前交错/弯曲比103清楚，两眼可辨，侧后覆盖保持；仍有冠部/额前宽片、重复侧弯、部分贴额薄片、浅色分缝，脸/服装未达到参考。

**继续基础为Exports/nativelongfringe106/Ember_Regent.blend；103、98、94、86与稳定napeunderlay02保留。目标未完成。** 后续优先处理宽冠主导弧线与刘海的立体截面、贴额薄片；不要再次把整块上冠拉成同一方向的盖子或把稀疏悬拱当蓬松完成。native_front_frame_sculpture属性只保留旧61选区归属，106其中6038根几何已改变，不能再称精确旧61造型。

104/105/106三次局部静态成对检查通过：141网格/UV/形态键/变换、真实根/半径/拓扑、未选主发与所有其他毛发、全部材质图/槽/灯光保持。校验器新增独立--fringe-profile，明确允许旧刘海变化，实际重读106证明6038旧刘海+2501其他主发变化，全部主发梢低于1.640m为0；原--tip-profile仍要求旧选区精确保持，默认行为不变。这些检查不证明连续发丝段/眼睛/服装/动画碰撞或艺术达标。

六项无关修改、Fab/Bystedt源及保护工程哈希保持。原/衍生几何、索引、日志仅本地；同步源码/聚合报告/已看实渲，无新费用、神经重建/AI肖像替代、动画/UE接入、候选Release或社交发布。
