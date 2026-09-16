# SurvX 示例项目（examples）

examples 目录存放 SurvX 的演示 Demo。
**所有示例仅用于演示范式概念，不作为正式可交付系统。**
正式研究载体、行业解决方案放在 `solutions/` 目录（humans、molin）。

SurvX 是一套实体元建模范式，用来对带有目标、约束、状态、相互作用的实体进行建模。
这些 Demo 由浅入深，逐步验证 SurvX 核心能力以及 survx-frontend-web 前端子范式能力。

## 命名约定
- 文件夹目录：下划线 snake_case `_`
- 蓝图内部字段（Energy、relation 等）：短横 kebab-case `-`

## Demo 清单（按开发难度排序）

### 基础示例（无Ego，验证基础蓝图与状态流转）
1. **hello_world**
    SurvX 最小入门示例。一个最简单的Meta实体，只有基础Goal、Energy字段。
    启动网关后，自动加载蓝图，生成基础交互面板，可读写实体状态。
    验证能力：最基础的蓝图加载、实例初始化、网关通信、前端子范式基础渲染。

2. **simple_counter**
    最小 SurvX 演示示例。计数器实体，支持增减操作。
    约束：数值不能小于0。
    验证能力：Meta蓝图声明、Energy读写、基础业务约束校验、网关事件循环、自动生成前端面板。

3. **sensor_sim**
    仿真传感器实体。按照固定节拍自动更新指标状态。
    验证能力：实体自主状态更新、周期事件、越界告警、WebSocket实时状态推送。

### 进阶示例（多实体、works灰度、前端子范式）
3. **multi_entity_link**
    多个Meta实体共存，互相读取状态、产生事件交互。
    验证能力：Relation关系层、跨实体事件通信、多实体共存。

4. **works_gray_demo**
    演示works机制与实例灰度发布。
    准备两套行为逻辑蓝图，对部分实例做逻辑升级、回滚。
    验证能力：works版本管理、实例灰度迭代。

5. **dynamic_form_view**
    survx-frontend-web 前端子范式演示Demo。
    UI布局、控件全部在Meta蓝图的relation中声明。修改蓝图，界面自动重组，无需修改前端代码。
    验证能力：蓝图驱动动态界面组装、双向交互。

6. **view_combine_workspace**
    实体面板自由组合工作区。
    用户可以拖拽、缩放、自由摆放各个实体面板；自定义布局可保存为视图实体，下次打开自动恢复。
    验证能力：多面板动态组合、用户自定义工作视图。

7. **ai_town**
    轻量化多智能体仿真小镇。多个居民实体在世界实体中感知、交互，搭配 render2d_web 2D可视化。
    验证能力：多实体共存、全局世界实体、2D画布可视化。

8. **ai_town_3d**
    可选进阶演示Demo。基于 render3d_web 实现小镇3D可视化。
    图形渲染工作量大，仅作为展示效果，非主干验证内容。

### 高级示例（带Ego，验证XGI核心能力）
9. **ego_self_monitor**
    基础Ego自检实体。实体具备G/L/R/O必需四层，可以读取自身蓝图与状态，持续自查约束。
    验证能力：Ego自我指征、实体自省。

10. **ego_adaptive_threshold**
    带受控自适应能力的Ego实体。可以在业务约束边界内，自主调整自身参数。
    验证能力：受控自演化、参数自适应调整。

### 可选CLI示例
**demo_cli_only**
不启动前端，仅通过脚本+网关操作实体。
用来证明 SurvX 可以脱离前端子范式独立运行。

## 开发推荐顺序
simple_counter → sensor_sim → multi_entity_link → works_gray_demo → dynamic_form_view → view_combine_workspace → ai_town → ego_self_monitor → ego_adaptive_threshold →（可选 ai_town_3d / demo_cli_only）

## 边界说明
- `examples/`：Demo，用于演示范式特性。不追求健壮性，不用于正式研究与业务交付。
- `solutions/`：正式解决方案 humans、molin。用于长期研究、真实行业数据落地。
