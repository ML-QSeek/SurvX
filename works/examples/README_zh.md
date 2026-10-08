# SurvX 示例项目（examples）

examples 目录存放 SurvX 的演示 Demo。
**所有示例仅用于演示范式概念，不作为正式可交付系统。**
正式研究载体、行业解决方案放在 `solutions/` 目录（humans、molin）。

SurvX 是一套实体元建模范式，用来对带有目标、约束、状态、相互作用的实体进行建模。
这些 Demo 由浅入深，逐步验证 SurvX 核心能力以及 survx-frontend-web 前端子范式能力。

## 命名约定

| 层级 | 风格 | 示例 |
|------|------|------|
| Demo 标识（name） | PascalCase | `HelloWorld`、`SimpleCounter` |
| Demo 展示标题（title） | 中文，可含专有名词 | `简单计数器`、`Works 灰度演示` |
| 蓝图内部字段（Energy、relation 等） | 短横 kebab-case `-` | `goal-type`、`energy-value` |
| 前端子范式名 | 短横 kebab-case `-` | `survx-frontend-web` |

> 注意：`design_zh.md` 中的系统表名（`_parameter`、`_constraint` 等）使用下划线前缀，
> 属于存储层约定，与本文件的蓝图字段命名不冲突。

## Demo 清单（按开发难度排序）

### 基础示例（无 Ego，验证基础蓝图与状态流转）

1. **HelloWorld**
    SurvX 最小入门示例。一个最简单的 Field 实体，只有基础 Goal、Energy 字段。
    启动实例运行时后，自动加载蓝图，生成基础交互面板，可读写实体状态。
    验证能力：最基础的蓝图加载、实例初始化、引擎通信、前端子范式基础渲染。

2. **SimpleCounter**
    最小 SurvX 演示示例。计数器实体，支持增减操作。
    约束：数值不能小于 0。
    验证能力：Field 蓝图声明、Energy 读写、基础业务约束校验、引擎事件循环、自动生成前端面板。

3. **SensorSim**
    仿真传感器实体。按照固定节拍自动更新指标状态。
    验证能力：实体自主状态更新、周期事件、越界告警、WebSocket 实时状态推送。

### 进阶示例（多实体、works 灰度、前端子范式）

4. **MultiEntityLink**
    多个 Field 实体共存，互相读取状态、产生事件交互。
    验证能力：Relation 关系层、跨实体事件通信、多实体共存。

5. **WorksGrayDemo**
    演示 works 机制与实例灰度发布。
    准备两套行为逻辑蓝图，对部分实例做逻辑升级、回滚。
    验证能力：works 版本管理、实例灰度迭代。

6. **DynamicFormView**
    survx-frontend-web 前端子范式演示 Demo。
    UI 布局、控件全部在 Field 蓝图的 relation 中声明。修改蓝图，界面自动重组，无需修改前端代码。
    验证能力：蓝图驱动动态界面组装、双向交互。

7. **ViewCombineWorkspace**
    实体面板自由组合工作区。
    用户可以拖拽、缩放、自由摆放各个实体面板；自定义布局可保存为视图实体，下次打开自动恢复。
    验证能力：多面板动态组合、用户自定义工作视图。

8. **AITown**
    轻量化多智能体仿真小镇。多个居民实体在环境实体中感知、交互，搭配 render2d_web 2D 可视化。
    验证能力：多实体共存、全局环境实体、2D 画布可视化。

### 高级示例（带 Ego，验证 XGI 核心能力）

9. **EgoSelfMonitor**
    基础 Ego 自检实体。实体具备 G/L/R/O 必需四层，可以读取自身蓝图与状态，持续自查约束。
    验证能力：Ego 自我指征、实体自省。

10. **EgoAdaptiveThreshold**
    带受控自适应能力的 Ego 实体。可以在业务约束边界内，自主调整自身参数。
    验证能力：受控自演化、参数自适应调整。

### 可选 CLI 示例

**DemoCliOnly**
不启动前端，仅通过脚本 + 引擎操作实体。
用来证明 SurvX 可以脱离前端子范式独立运行。

## 开发推荐顺序

HelloWorld → SimpleCounter → SensorSim → MultiEntityLink → WorksGrayDemo →
DynamicFormView → ViewCombineWorkspace → AITown → EgoSelfMonitor →
EgoAdaptiveThreshold →（可选 DemoCliOnly）

## 边界说明

- `examples/`：Demo，用于演示范式特性。不追求健壮性，不用于正式研究与业务交付。
- `solutions/`：正式解决方案 humans、molin。用于长期研究、真实行业数据落地。