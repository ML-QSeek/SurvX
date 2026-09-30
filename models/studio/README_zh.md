Studio 目标层（G）

G1：让 SurvX 的一切机制，都能通过 SurvX Studio 来实现。

Studio 结构层（S）

管理机制——Studio 自身的操作管理构件集合，含 6 个模块：交互、上下文、调用、编排、反馈、AI 调用。

沙盒机制——为运行调试提供安全隔离的执行环境。

中间件——Studio 的通信通道，形态可选服务/微服务方式，如 HTTP + WebSocket。

Studio 约束层（O）

O1：Studio 不实现任何功能。所有功能先在 Engine 中实现，Studio 只调用。

O2：Studio 的函数与 Engine 的函数职责不重叠，重叠与否由 AI 校验，结论落 _llm 表。

O3：Studio 只包含功能调用 + 交互逻辑，不再有第三类内容。

Studio Ego

不做。

Studio 环境（Env）目标层（G）

G1：让 Studio 充分、有效、流畅地运行，发挥其作用。

Studio 环境（Env）结构层（S）

中间服务（FastAPI）——承载 Studio 的 HTTP + WebSocket 通信。

容器编排（K3s）——为沙盒机制提供容器级隔离底座。

Web 浏览器——Studio 运行所需的浏览器环境。

AI 大模型——Studio 编程能力所依赖的外部模型资源。

编程语言——Studio 运行与编程活动所依赖的语言环境，含 Python、JavaScript、HTML、CSS。

被开发项目——Studio 操作的外部项目，是独立实体，在 Studio 视角下构成其外部环境的一部分。

Engine——引擎实体，被 Studio 引用。





















已读完 SurvX Studio 设计文档（草案）。我把它与你前面四份基础文档对照，梳理出当前定位、已定机制、与范式的对应关系、以及待续点，供明天「Studio + 前端框架」专题直接接着用。

一、Studio 在 SurvX 范式中的定位
维度	Studio 的取值	范式依据
实体类型	Cat（Field Matter）	是问题本体，不是 Ego
分层	S-C-R-O-F 五层	未启用 G/L，因为不做 Ego
Ego	不做	无自主性，行为由外部触发
Energy	未在草案中显式声明	按范式必须有专属数据流，待补
Env	有，独立声明 [Cat]<envname>	中间服务、容器编排、浏览器、LLM、语言环境、被开发项目、Engine
角色	声明体，不是执行体	只声明结构与能力，不主动执行
与 Engine 关系	解耦，但优先复用	O1 强制：功能先在 Engine 实现，Studio 只调用
这与 core-context_zh.md 的「组合式实例架构」一致：Studio 作为 Cat，需要配套 Env；但由于不做 Ego，它属于纯 Field 实例，对应 modeling-flow_zh.md 步骤 1–7 的静态业务建模阶段产物——可机械性解决问题，无需推演。

二、Studio 本体（Cat）逐层对照
G 目标层
G1：让 SurvX 的一切机制，都能通过 SurvX Studio 来实现。

符合范式：G 是外部输入目标，是推演唯一起点。此处 Studio 无 Ego，G 仅作为声明性目标存在，不驱动内部推演。

S 结构层
三大机制：

管理机制：6 模块 — 交互、上下文、调用、编排、反馈、AI 调用。

沙盒机制：可选构件，容器级隔离。

通信层：候选层，可能取消。

注：S 层通常定义「构件、模块、组成单元」。此处把「管理机制 / 沙盒机制 / 通信层」作为 S 的顶层构件，符合语法。6 模块内部组织已挂起，待开发时定。

C 能力层
草案未显式列出 C 层内容，但由 O3 约束「Studio 只包含功能调用 + 交互逻辑」可推出：C 层即功能调用 Q + 交互逻辑 Q 的集合。建议明天补一张 C 层构件清单，否则按 syntax_zh.md 强制约定「写了哪层，哪层就不能空」，C 层不能留白。

R 外部关系层
草案第六节「已定的 Q（协作关系）」实质就是 R 层内容：

Q1 管理机制 → 通信层

Q2 沙盒 → 通信层

Q3 FastAPI → HTML / AI 接口

Q4 通信层 → FastAPI

Q5 拉起 FastAPI 的函数型 Q

Q6 FastAPI → 通信层

方向约定「按谁属于谁、谁指向谁写，不按运行时主动/被动写」——这正是 core-context_zh.md 对 Field.R = 外部接口关系 的定位：只存跨实体外部连接、交互接口、调用关系，不存认知、不推理。

注意：Q3/Q4/Q6 涉及 FastAPI，而 FastAPI 在草案里归 Env。跨 Cat↔Env 的交互链路，按 modeling-flow_zh.md 补充规范，应统一录入双方 Relation 外部关系层，不存入 Ego 认知图谱（此处无 Ego，天然满足）。

O 约束层
O1：Studio 不实现任何功能，所有功能先在 Engine 实现，Studio 只调用。

O2：Studio 与 Engine 函数职责不重叠，由 AI 校验，结论落 _llm 表。

O3：Studio 只包含功能调用 + 交互逻辑，无第三类内容。

O2 明确要求落 _llm 表，与 syntax_zh.md 2.14 节「AI 协作（_llm）」一致：只存理由，不存结果，记录协作历史。

F 特征层
main 入口，可为空。

启动逻辑由 FastAPI 反向拉取通信层服务 Q 完成。

承载多套可选方案：直连 LLM / 走网关、用沙盒 / 不用沙盒、保留通信层 / 不保留。

F 层「多分支执行路径、场景适配策略」的定位吻合。

三、Studio 环境（Env）对照
草案把 Env 的 G/S/F 都写了，但未写 C/R/O：

层	草案内容	缺口
G	G1：让 Studio 充分、有效、流畅运行	—
S	FastAPI、容器编排、浏览器、AI 大模型、编程语言、被开发项目、Engine	—
C	未写	缺：Env 可提供的资源供给、数据服务、运行支撑能力
R	未写	缺：Env 与内部实体、外部系统的交互链路、反馈通道
O	未写	缺：资源上限、环境规则、全局边界条件
F	main 入口：FastAPI 等常驻服务的定义与启动入口	偏薄，可再补动态特性
按 modeling-flow_zh.md 步骤 11，Env 五层都要规划。明天若继续 Studio 主线，建议把 Env 的 C/R/O 补齐。

四、沙盒机制
定位：可选构件，防环境被搞坏，不防安全攻击。

功能：接收脚本 → 系统命令执行 → 返回日志。

形态：通用 Pod / Docker 容器 + 容器内 FastAPI（HTTP/WebSocket）。

边界：容器边界隔离，不靠内部权限。

内部结构：子 Matter（S/C/R/O/F），暂不展开。

这与 modeling-flow_zh.md 步骤 7 后的「按需分解子问题」一致：沙盒作为子问题，若已有现成实现则停止拆解，仅在上层定义 Relation、Capability；若没有，递归建模生成子 Field。草案说「暂不展开」，即当前判定为可复用组件，先挂起。

递归强约束提醒：递归建模仅生成子 Field 业务实体，不重复创建子 Ego、子环境。

五、对外交互与展现机制（明天重点）
核心设计：模块自己声明「怎么被展现」。

模块侧：每个模块 / 函数把「对外交互形式」看作自身属性，声明尺寸、展现形式、最小尺寸、最大拉伸限度等，落在参数表。

框架侧：一个独立 Q，作为轻量前端框架，读各模块声明的展现参数，在遵循各模块自身需求的前提下，把需要同页展示的东西尽量排到一起。

对应范式：

展现属性 = 模块的参数 → 落 _parameter 表，key 形如 ModuleId-Presentation_s_x。

布局 = 一个独立 Q → 注册为 q:<q_id>，可被引用在 Matter 的 C 能力层，或作为关系表达。

这属于 F 特征层 的多套可选方案承载，也涉及 R 外部关系层（模块 ↔ 前端框架的交互链路）。

明天展开时，建议按 q-iio-schema_zh.md 四段式（Lang / I-Import / I-Internals / O-Output）描述这个布局 Q，因为它是复杂 Q。

六、FastAPI 启动机制（运行时序 vs 推演流程）
草案第七节描述的是运行时序：

管理机制各模块写成函数型 Q，带字段标明「可挂载」。

通信层有一批服务形态 Q，包装成 FastAPI 可加载形式。

Studio 主程序多进程启动 FastAPI，管理生命周期。

FastAPI 启动后反向拉取通信层服务形态 Q，动态加载成路由。

对照 modeling-flow_zh.md 实用补充说明第 1 条：

推演流程是分析设计思考流程，不等同于程序运行时序；程序真实运行时序，完全由 Energy 数据变动驱动。

所以第七节是运行时序，而建模推演时我们仍按 G→S→C→R→O→F 的声明式顺序落表。两者不冲突，但不要在建模阶段把运行时序混进结构声明。

七、与四份基础文档的合规性速查
检查项	结论
是否混淆两类 R	否。Studio 无 Ego，只有 Field.R（外部接口）
是否把 Energy 当实体	草案未声明 Energy，需补；补时须记「只有数据，无结构无能力」
是否等同看待同名分层	否。Studio 是 Cat，其 S/C/O/F 服务业务执行，非思考推演
是否让 Field 自主推演	否。明确不做 Ego
环境是否具备自我意识	否。Env 只提供资源与规则
命名是否合规	Q1–Q6 是文档编号，不是实体 ID；实际落地需转为 [A-Za-z][A-Za-z0-9]*，多词驼峰首字母大写
分层是否留白	C 层（Cat）与 C/R/O 层（Env）目前留白，按强制约定不可投产
八、明天接着用的锚点
Studio 文档草案已成型：大机制定住，细节留白。

前端框架 = 那个「独立布局 Q」：读模块展现参数做布局，今天定雏形，明天展开。

两者放一起讨论：前端框架本就是 Studio 展现机制的一部分。

明天可优先处理：

Cat 的 C 层构件清单（功能调用 Q + 交互逻辑 Q 的具体划分）。

Env 的 C/R/O 补齐。

布局 Q 的 q-iio-schema_zh.md 四段式描述。

模块展现参数在 _parameter 表中的 key 规范（如 ModuleId-Presentation_s_x）。

Studio 专属 Energy（{Cat}<energyname>）的声明。

Q1–Q6 落地为合法实体 ID 与 _relation 表记录。

我已就绪，明天可直接从上述任一锚点继续。

