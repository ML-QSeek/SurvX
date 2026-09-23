# SurvX 语法规范（syntax_zh.md）
> 本文档分两部分：
> 第一部分：语法规则描述（怎么写才合法）
> 第二部分：分块写法（每种块具体长什么样）
> 存储规则、运行规则、校验规则见 design.md。

---

# 第一部分：语法规则描述
## 1.1 整体结构公式
```
Instance = Cat + (Cat)<egoname> + [Cat]<envname> + {Cat}<energyname>
```
**补充说明**
- `+` 不代表字符串拼接，代表实例组件组合关系；
- 集合写法 `[Cat1,Cat2,Cat3]<envname>` 表示多个实体归属同一个 Env 环境，在 Matter 表中各自使用独立路径 Key。

## 1.2 顶层标记规范
`()` / `[]` / `{}` 为蓝图顶层固定语义标记，属于字典字符串 Key，非程序变量，可合法存入字典与数据库文本字段。
- `(Cat)`：Ego 主体实体标记
- `[Cat]`：Env 环境实体标记
- `{Cat}`：Energy 能量参数实体标记

## 1.3 原生简写规范（系统默认基座）
- `(Cat)base` 简写为 `()Cat`
- `[Cat]base` 简写为 `[]Cat`
- `{Cat}base` 简写为 `{}Cat`

在仿真项目中，`[Cat]`和 `{Cat}`支持多实体集合写法，`[Cat1,Cat2,Cat3]<envname>`、`{Cat1,Cat2,Cat3}<energyname>`，即：
```
Instance = Cat1 + (Cat1)<egoname> + Cat2 + (Cat2)<egoname> + Cat3 + (Cat3)<egoname> + [Cat1,Cat2,Cat3]<envname> + {Cat1,Cat2,Cat3}<energyname>
```

## 1.4 两大类
顶层分两大类：**Matter** 与 **Energy**。

**Matter**
- Cat、(Cat)<egoname>、[Cat]<envname> 都属于 Matter，三者语法相同

**Energy**
- 不按分层结构组织
- 按数据类型分块存储
- 存参数快照、约束快照、时序经历

## 1.5 Q 的语法地位
Q 是表征关系的基本单元，可以是代码，也可以是模型。
Q 引用分两种
- `q:<q_id>`：引用已注册的 Q
- ``q:```xxx``` ``：内联代码块，直接写表达式/代码

## 1.6 hoc / dbfs 约定
- **hoc**：临时脚本态。
- **dbfs**：正式持久态。

之后文中所有 `hoc` 和 `dbfs` 都按此约定简写，不再展开。

### 1.6.1 hoc（临时脚本态）
所有 Matter 实体、Energy 结构通过 Python 字典声明描述，无数据库依赖，支持快速迭代、原型验证、小规模实例调试。
- Matter：顶层是一个大字典，所有子 matter 都以长 key 和 value 的格式，显式写在这个字典中。
> 示例示意（仅用来理解，不是完整语法）
```python
Instance = {
    "Cat": {...},
    "(Cat)<egoname>": {...},
    "[Cat]<envname>": {...},
    "{Cat}<energyname>": {...}
}
```
- Energy：按表分，每张表一个字典。
- Q：直接以函数形式写在脚本中。

### 1.6.2 dbfs（正式持久态）
采用多介质分离存储架构，实现结构、功能、数据解耦：
- Matter 结构化定义：持久化至 SQLite。
- Q 功能逻辑：独立文件系统存储，与数据库元数据建立映射。
- Energy 时序数据、参数/阈值快照：存储至 DuckDB，支撑时序查询、状态回放、演化追溯。

## 1.7 关键字表
**实体类型**：`Matter` `Ego` `Field` `Entity` `Q`

**分层块**：`Structure` `Capability` `Relation` `Ordinance` `Feature` `Goal` `Symbol`

**分层标签释义**
- S = Structure 结构层
- C = Capability 能力层
- R = Relation 关系层
- O = Ordinance 约束层
- F = Feature 特征层
- G = Goal 目标层
- L = Symbol 符号层

**保留字段**：无

**特殊 key**
以下特殊 key 为各表通用：
- `_tick`：记录当前 tick，格式 `YYYYMMDDHHMMSS`，如 `20260918224522`

## 1.8 命名规则
### 1.8.1 实体 ID
格式：`[A-Za-z][A-Za-z0-9]*`
适用于所有实体：Matter、Ego、Env
适用于所有记录：参数、约束、关系
适用于所有构件：Q
Q 允许无语义，可用 q + 随机数/自增数


### 1.8.2 符号禁用与专属规则

`_` 和 `-` 为引擎专属分隔符，不进入任何名字内部。

**禁用范围**
- 实体名（Matter、Ego、Env、Energy 的名字）
- 路径 key 的各段（分层标签、局部ID）
- 所有记录 ID、构件 ID、Q ID

**专属位置**
- `_`：仅用于路径 key 的分层分隔符
  格式：`父路径_分层标签_局部ID`
  示例：`SurvXStudio_s_1`、`Cat_c_1`
- `-`：仅用于参数表、约束表、关系表 key 的 id0-id1 拼接
  格式：`id0-id1`
  示例：`Cat-Phys_s_1`、`CatFood-Cat`

**命名要求**
- 只能用 ASCII 字母、数字
- 首字符为字母
- 多词用驼峰命名，首字母大写
  示例：`SurvXStudio`、`CatFood`、`Phys`

**非法示例**
- `survx_studio`：实体名含 `_`
- `survx-studio`：实体名含 `-`
- `survx studio`：含空格
- `survxstudio`：合法，但不推荐，可读性差

**合法示例**
- `SurvXStudio_s_1`：实体名 `SurvXStudio`，`_` 为分层分隔符
- `Cat-Phys_s_1`：`-` 为拼接符，`_` 为分层分隔符

### 1.8.3 key 格式与 ID 规则
- 分层节点以路径 key 作为字典 key
- 路径 key 格式：`父路径_分层标签_局部ID`
- 局部 ID 分两类：
  - 自增数字：普通节点，同一父路径、同一层内从 1 开始依次编号
  - 系统保留关键字：特殊用途节点，用关键字代替数字
- 父路径 + 当前层 + 局部 ID 三者组合，保证全局唯一

示例：
```
root_s_1_s          # 自增数字
root_s_2_s          # 自增数字
root_s_self_s       # 系统保留关键字
root_s_meta_s       # 系统保留关键字
```

### 1.8.4 版本号规则
- hoc：脚本级版本号，写在脚本头部，节点不单独带 `version`
- dbfs：节点级版本号，每个节点自带 `version`
- 格式：`YYYYMMDDHHMMSS`
- 示例：`20260918224522`

**版本存储强制约定**
修改 Matter 节点、参数、约束记录时，采用**新增版本行**方式，不原地覆盖；系统自动取最大 `version` 记录作为当前最新有效记录。

示例：
```
root_s_1_s  version=20260918224522
root_s_1_s  version=20260919093000
```

## 1.9 引用规则
1. 所有引用必须指向已注册 ID，禁止裸字符串（L 层除外）。
2. 跨表引用必须带前缀。
3. `value` 支持字面量或 Q 引用两种类型。

## 1.10 value 写法
value 是节点内容的核心取值，只允许三种类型：

### 1. 数字
- 整数：`1`
- 浮点：`0.05`、`1.5e-3`

### 2. Q 引用
- 格式：`q:<q_id>`
- 示例：`q:q3f8a2`

### 3. 内联 Q
- 格式：``q:```xxx``` ``
- 只允许简单函数表达式或关系比较
- 示例：``q:```val <= 200``` ``

**强制规则**
- **value 一律不嵌套字典。** 所有节点平铺，层级信息只由 key 承载。
- 字面量只允许数字。
- 内联 Q 仅允许简单关系比较、基础算术表达式；**循环、分支等复杂逻辑禁止内联书写**，复杂逻辑必须封装为独立注册 Q 函数。

---

# 第二部分：分块写法
## 2.1 Matter 
### 总体介绍
Matter 是实例的问题本体结构，承载 Field、Ego、Env 三类实体的七层定义。以 key-value 方式声明。属于核心运行块。

### hoc
1. 顶层一个字典，字典名 = Matter 名。比如 Cat = { ... }。
2. 字典里每个 key 是路径 key，格式：父路径_分层标签_局部ID
3. 每层先写节点本身，再决定要不要展开
   - 只写节点本身：`"Cat_s_1": "heart"`
   - 要展开内部结构：`"Cat_s_1_s_1": "ventricle"`
4. value 直接写内容，不嵌套字典

```python
Cat = {
    "Cat_s_1": "heart",
    "Cat_s_1_s_1": "ventricle",
    "Cat_s_1_s_2": "atrium",
    "Cat_s_2": "lung",
    "Cat_c_1": "q:q97594"
}
```
5. 不需要写全五层/七层，按需要写。写了哪层，哪层就不能空。
6. 版本号在脚本头部，节点不单独带

### dbfs
Matter 落点为一张 SQLite 表，所有 Matter 节点统一存这张表，不分表。
- 库文件：`<mattername>.db`
- 表名：`<mattername>`

**字段**
- key：TEXT，路径 key，如 Cat_s_1
- value：TEXT，节点内容，字面量或 Q 引用
- version：TEXT，版本号，格式 YYYYMMDDHHMMSS

**建表语句**
```sql
CREATE TABLE Cat (
    key     TEXT,
    value   TEXT,
    version TEXT
);
```

所有 Matter 节点统一存 `<mattername>` 表，靠 key 第一段的实体名区分类型：
- Cat_...：问题本体
- ()Cat_...：Ego
- []Cat_...：Env

**示例数据**
```sql
INSERT INTO Cat (key, value, version) VALUES
('Cat_s_1', 'heart', '20260918224522'),
('Cat_s_1_s_1', 'ventricle', '20260918224522'),
('Cat_s_1_s_2', 'atrium', '20260918224522'),
('Cat_s_2', 'lung', '20260918224522'),
('Cat_c_1', 'q:q787876', '20260918224522'),
('()Cat_g_1', 'g_eat_full', '20260918224522'),
('[]Cat_s_1', 'indoor', '20260918224522');
```

### 特殊设定
主体节点允许 value 为空字符串，表示无额外结构内容

### 强制约定
- value 一律不嵌套字典
- 不需要写全五层/七层，按需要写
- 结构必须可查，必须有根结构
- key 第一段的实体名必须与顶层字典名一致
- 操作按表分离，一次只写一张表，不写跨表批量 API
- 同一张表可以一次 INSERT 多行，但不能把多张表合并进同一次写入
- 新增实体结构时，必须同时添加参数表记录，至少参数表；建议参数表、约束表、关系表同时添加，实体才成立
- 后续可以对该实体再增删改参数、关系、约束

---

## 2.2 参数表(_parameter)
### 总体介绍
参数表存储实体的参数、属性、配置。属于核心运行块。
参数表还用于给 Energy 记录做定义，比如某个参数的可信度、置信度等指标。

### hoc
字典。先给 Matter 表，再给参数表，看得到引用关系。

```python
# Matter 表
matter = {
    "Cat": "",
    "Phys_s_1": "height",
    "Phys_s_2": "weight"
}
# 参数表
_parameter = {
    "Cat-Phys_s_1": [
        [30, 1, "20260101000000"],
        [32, 1, "20260601000000"],
        [35, 1, "20261201000000"]
    ],
    "Cat-Phys_s_2": [
        [4.5, 2, "20260101000000"]
    ]
}
```
- key：id0-id1，id0 和 id1 都是 Matter 表里的路径 key，用横线 - 拼接
- value：list of list，每个子 list 三个元素
  1. 参数值
  2. idx，全局自增序号
  3. 版本号

### dbfs
共用一个 `_parameter` 表。

**字段**
- id0：TEXT，主体或参数记录引用
- id1：TEXT，语义或指标
- value：TEXT，参数值
- idx：INTEGER，全局自增序号
- version：TEXT，版本号，格式 YYYYMMDDHHMMSS

**建表语句**
```sql
CREATE TABLE _parameter (
    id0      TEXT,
    id1      TEXT,
    value    TEXT,
    idx      INTEGER,
    version  TEXT
);
```

**示例数据**
```sql
INSERT INTO _parameter (id0, id1, value, idx, version) VALUES
('Cat', 'Phys_s_1', '30', 1, '20260101000000'),
('Cat', 'Phys_s_1', '32', 1, '20260601000000'),
('Cat', 'Phys_s_1', '35', 1, '20261201000000'),
('Cat', 'Phys_s_2', '4.5', 2, '20260101000000');
```

### 特殊设定
- key 由两个 Matter 路径 key 拼接，保证语义不孤立
- idx 全局自增，分配给新对象；同一对象更新时 idx 不变
- version 标识同一对象在不同时间点的取值
- 同一条参数可有多版本记录，按 version 排序，取最大值为最新

**两种声明方式**
1. **主体 + 语义**：`('Cat', 'Phys_s_1', '30', 1, '20260101000000')` 表示 Cat 的身高是 30。
2. **参数 + 指标**：`('param_1', 'confidence', '0.6', 2, '20260101000000')` 表示第 1 条参数（Cat 的身高）的置信度是 0.6。

> 补充约定：`param_1` 这类前缀派生 ID，支持引擎自动生成或手动书写，**前缀仅为引用层标识，不存入数据表原始记录**。

### 强制约定
- 新增实体结构时，必须同时添加参数表记录，至少参数表
- idx 分配后不变
- 同一对象更新时，idx 不变，只有 value 和 version 变

---

## 2.3 约束表（_constraint）
### 总体介绍
约束表存储实体的约束、阈值、规则。属于核心运行块。
结构跟参数表一致，但 value 存的是约束表达式或 Q 引用。

### hoc
字典。先给 Matter 表，再给约束表。

```python
# Matter 表
matter = {
    "Cat": "",
    "Phys_s_1": "height",
    "Phys_s_2": "weight"
}
# 约束表
_constraint = {
    "Cat-Phys_s_1": [
        ["q:```val <= 200```", 1, "20260101000000"],
        ["q:q3f8a2", 1, "20260101000001"]
    ]
}
```
- key：id0-id1，id0 和 id1 都是 Matter 表里的路径 key，用横线 - 拼接
- value：list of list，每个子 list 三个元素
  1. 约束表达式或 Q 引用
  2. idx，全局自增序号
  3. 版本号
- 同一个对象更新时，idx 不变，只有 version 变
- 不同约束用不同 idx

### dbfs
共用一个 `_constraint` 表。

**字段**
- id0：TEXT，主体或约束记录引用
- id1：TEXT，语义或指标
- value：TEXT，约束表达式或 Q 引用
- idx：INTEGER，全局自增序号
- version：TEXT，版本号，格式 YYYYMMDDHHMMSS

**建表语句**
```sql
CREATE TABLE _constraint (
    id0      TEXT,
    id1      TEXT,
    value    TEXT,
    idx      INTEGER,
    version  TEXT
);
```

**示例数据**
```sql
INSERT INTO _constraint (id0, id1, value, idx, version) VALUES
('Cat', 'Phys_s_1', 'q:```val <= 200```', 1, '20260101000000'),
('Cat', 'Phys_s_1', 'q:q3f8a2', 1, '20260101000001');
```

### 特殊设定
- key 由两个 Matter 路径 key 拼接，保证语义不孤立
- idx 全局自增，分配给新对象；同一对象更新时 idx 不变
- version 标识同一对象在不同时间点的取值
- 同一条约束可有多版本记录，按 version 排序，取最大值为最新
- value 支持两种：内联 Q、引用 Q
- 约束执行后必须返回结果：True / False / 差值

**两种声明方式**
1. **约束参数**：`('Cat', 'Phys_s_1', 'q:```val <= 200```', 1, '20260101000000')` 表示：Cat 的身高这个参数，约束值是 ≤ 200。
2. **约束 + 指标**：`('constraint_1', 'severity', 'q:```val > 0.8```', 3, '20260101000000')` 表示：第 1 条约束的严重程度判断是 val > 0.8。

> 补充约定：`constraint_1` 这类前缀派生 ID，支持引擎自动生成或手动书写，**前缀仅为引用层标识，不存入数据表原始记录**。

### 强制约定
- 新增实体结构时，建议同时添加约束表记录
- idx 分配后不变
- 同一对象更新时，idx 不变，只有 value 和 version 变
- 约束的 value 只允许两种：内联 Q、引用 Q

---

## 2.4 关系表（_relation）
### 总体介绍
关系表存储实体之间的关系、连接、依赖。属于核心运行块。
结构跟参数表、约束表一致，但 value 存的是关系表达式或 Q 引用。两两关系用 Q 函数表达，内联 Q 只写简单表达式。
关系表既表达内部关系（同一主体内部构件之间，对应功能层），也表达外部关系（不同主体之间，对应关系层）。

### hoc
字典。先给 Matter 表，再给参数表，再给关系表。

**内部关系示例：猫的前腿和后腿**
```python
# Matter 表
matter = {
    "Cat": "",
    "Cat_s_1": "前腿",
    "Cat_s_2": "后腿"
}
# 关系表
_relation = {
    "Cat_s_1-Cat_s_2": [
        ["q:q3f8a2", 1, "20260101000000"]
    ]
}
```

**外部关系示例：猫粮和猫的体重**
```python
# Matter 表
matter = {
    "Cat": "",
    "Phys_s_2": "weight",
    "CatFood": ""
}
# 参数表
_parameter = {
    "Cat-Phys_s_2": [[4.5, 1, "20260101000000"]]
}
# 关系表
_relation = {
    "CatFood-param_1": [
        ["q:q7b2c", 1, "20260101000000"]
    ]
}
```

- key：id0-id1，两个都是可引用 ID，用横线 - 拼接
- id0、id1 可以是：Matter 路径 key、参数记录引用
- value：list of list，每个子 list 三个元素
  1. 关系表达式或 Q 引用
  2. idx，关系表内自增
  3. 版本号
- 同一个对象更新时，idx 不变，只有 version 变
- 不同关系用不同 idx

### dbfs
共用一个 `_relation` 表。

**字段**
- id0：TEXT，主体或关系记录引用
- id1：TEXT，语义或指标
- value：TEXT，关系表达式或 Q 引用
- idx：INTEGER，关系表内自增序号
- version：TEXT，版本号，格式 YYYYMMDDHHMMSS

**建表语句**
```sql
CREATE TABLE _relation (
    id0      TEXT,
    id1      TEXT,
    value    TEXT,
    idx      INTEGER,
    version  TEXT
);
```

**示例数据**
```sql
-- 内部关系
INSERT INTO _relation (id0, id1, value, idx, version) VALUES
('Cat_s_1', 'Cat_s_2', 'q:q3f8a2', 1, '20260918224522');
-- 外部关系
INSERT INTO _relation (id0, id1, value, idx, version) VALUES
('CatFood', 'param_1', 'q:q7b2c', 2, '20260918224522');
```

### 特殊设定
- key 由两个可引用 ID 拼接，保证语义不孤立
- idx 关系表内自增，分配给新对象；同一对象更新时 idx 不变
- version 标识同一对象在不同时间点的取值
- 同一条关系可有多版本记录，按 version 排序，取最大值为最新
- value 支持两种：内联 Q、引用 Q
- 两两关系用 Q 函数表达，内联 Q 只写简单表达式
- 关系表既表达内部关系，也表达外部关系

> 补充约定：`rel_1` 这类前缀派生 ID，支持引擎自动生成或手动书写，**前缀仅为引用层标识，不存入数据表原始记录**。

**两种声明方式**
1. **关系函数**：`('Cat_s_1', 'Cat_s_2', 'q:q3f8a2', 1, '20260918224522')` 表示：前腿和后腿之间的关系，由 Q 函数描述。
2. **简单表达式**：`('Cat_s_1', 'Cat_s_2', 'q:```ratio=0.15```', 1, '20260918224523')` 表示：前腿和后腿之间的比例是 0.15。
3. **关系 + 指标**：`('rel_1', 'strength', 'q:```0.9```', 3, '20260918224522')` 表示：第 1 条关系的强度是 0.9。

**内外关系区分**
- 两个 id 都在同一主体内部 → 内部关系
- 两个 id 分属不同主体 → 外部关系

### 强制约定
- idx 分配后不变
- 同一对象更新时，idx 不变，只有 value 和 version 变
- 关系的 value 只允许两种：内联 Q、引用 Q
- 两两关系用 Q 函数，内联 Q 只写简单表达式

---

## 2.5 状态（_state）
### 总体介绍
状态表存储当前 tick 窗口的全量变量，是引擎实时计算的唯一数据源。tick 结束后数据归档分流，窗口刷新重置。属于核心运行块。
状态表是引擎运行时内存中的表，由引擎自动维护，不经过人工声明，因此不分 hoc / dbfs 形态。

**字段**
- `_tick`：特殊 key，记录当前 tick
- 路径 key：与 Matter / Energy 中的 key 一致
- value：当前 tick 的值

### 特殊设定
- 一个实例**支持存在多个 Ego 主体**，**多个 Ego 对应多套独立状态表**
- 问题本体 + 其所属 Ego 共用一张状态表
- Env 单独一张状态表

### 强制约定
无

---

## 2.6 序列(_sequence)
### 总体介绍
序列表存储需要持续追踪的时序核心指标。这些指标由状态表计算得出，或直接从状态表取得，按 _tick 时间序列逐条追加存储，供后续趋势分析、时序回溯使用。属于核心运行块。
数据来源：状态表上一个窗口的数据，累积存下来。

### hoc
字典。
```python
sequence = {
    "_tick": "20260918224522",
    "Cat_c_1": 0.05,
    "()Cat_g_1": 0.8
}
```

### dbfs
存入数据库，按 _tick 逐条追加。

**字段**
- _tick：TEXT，记录当前 tick，格式 YYYYMMDDHHMMSS
- key：TEXT，与 Matter / Energy 中的 key 一致
- value：TEXT，当前 tick 的值

**建表语句**
```sql
CREATE TABLE sequence (
    _tick   TEXT,
    key     TEXT,
    value   TEXT
);
```

**示例数据**
```sql
INSERT INTO sequence (_tick, key, value) VALUES
('20260918224522', 'Cat_c_1', '0.05'),
('20260918224522', '()Cat_g_1', '0.8'),
('20260918224523', 'Cat_c_1', '0.06'),
('20260918224523', '()Cat_g_1', '0.8');
```

### 特殊设定
- 特殊 key _tick 通用
- 数据来源：状态表上一个窗口的数据，累积存下来

### 强制约定
无

---

## 2.7 经历(_experience)
### 总体介绍
经历表是状态表的历史归档。每个 tick 的状态表快照平移到经历表中，按 _tick 逐条存储，用于历史回溯。属于核心运行块。
经历表不是主要业务表，是被查表，结构可以复杂一点。后续可扩展，容纳意图、反馈等快照，通过 _TYPE 区分。

### hoc
三层嵌套字典。
```python
_experience = {
    "Cat": {
        "20260918224523": {
            "_state": {}
        }
    },
    "[]Cat": {
        "20260918224523": {
            "_state": {}
        }
    }
}
```
- 第一层 key：主体名，Cat / []Cat
- 第二层 key：_tick
- 第三层 key：_TYPE，如 _state / _intent / _feedback
- 最内层：对应类型的内容
- 一个 tick 下，一条记录只有一个 _TYPE

### dbfs
共用一个 `_experience` 表。

**字段**
- _from：TEXT，主体名，如 Cat / []Cat
- _tick：TEXT，记录当前 tick，格式 YYYYMMDDHHMMSS
- _type：TEXT，类型，如 _state / _intent / _feedback
- _value：TEXT，内容

**建表语句**
```sql
CREATE TABLE _experience (
    _from   TEXT,
    _tick   TEXT,
    _type   TEXT,
    _value  TEXT
);
```

**示例数据**
```sql
INSERT INTO _experience (_from, _tick, _type, _value) VALUES
('Cat', '20260918224523', '_state', '{}'),
('Cat', '20260918224524', '_intent', '{}'),
('[]Cat', '20260918224523', '_state', '{}');
```

### 特殊设定
- 不是主要业务表，是被查表，结构可以复杂一点,通过 _TYPE 区分记录类型，支持后续扩展
- 与状态表的区别：状态表是当前 tick，经历表是历史 tick
- 与序列表的区别：序列表一行一个 key，经历表一个 tick 一条记录
- 一个 tick 下，一条记录只有一个 _TYPE

### 强制约定
无

---

## 2.8 注册(_register)
### 总体介绍
注册表是全局 key-value 映射中心，用于解读 key、查找标签、反查信息。通过简单的 key 查询获取 value，得到对应信息。属于核心运行块。

> 补充定位：注册表是 XGI 符号层核心词典，支撑 `_language` 表符号↔自然语言双向翻译。

### hoc
字典。
```python
_register = {
    "Cat": "猫",
    "()Cat": "猫的自我",
    "[]Cat": "猫的环境",
    "q3438437": "健康度计算"
}
```

### dbfs
共用一个 `_register` 表。

**字段**
- key：TEXT，实体 ID
- value：TEXT，实体标签

**建表语句**
```sql
CREATE TABLE _register (
    key     TEXT,
    value   TEXT
);
```

**示例数据**
```sql
INSERT INTO _register (key, value) VALUES
('Cat', '猫'),
('()Cat', '猫的自我'),
('[]Cat', '猫的环境'),
('q3438437', '健康度计算');
```

### 特殊设定
无

### 强制约定
无

---

## 2.9 意图(_intent)
### 总体介绍
意图表存储 Ego 基于目标筛选、约束求解得到的可行路径与执行意图。属于 Ego 专属认知表。
_tick 引用状态表中的 tick，表示这个意图是基于哪个状态产生的。一个状态下，主体可以产生多个意图，对应多个目标。多目标最终综合成一条可执行路径，用特殊 key `_plan` 标记。

> 补充规则：多目标合并、冲突消解逻辑由**引擎**原生处理。

### hoc
嵌套字典。
```python
_intent = {
    "Cat": {
        "20260918224523": {
            "g_find_food": "outdoor -> search -> eat",
            "g_avoid_danger": "indoor -> stay",
            "_plan": "outdoor -> search -> eat -> return"
        }
    }
}
```
- 第一层 key：主体名，如 Cat
- 第二层 key：_tick，引用状态表中的 tick
- 第三层 key：目标 ID，或多个目标综合后的 _plan
- value：意图内容

### dbfs
共用一个 `_intent` 表。

**字段**
- _from：TEXT，主体名
- _tick：TEXT，引用状态表中的 tick
- key：TEXT，目标 ID 或 _plan
- value：TEXT，意图内容

**建表语句**
```sql
CREATE TABLE _intent (
    _from   TEXT,
    _tick   TEXT,
    key     TEXT,
    value   TEXT
);
```

**示例数据**
```sql
INSERT INTO _intent (_from, _tick, key, value) VALUES
('Cat', '20260918224523', 'g_find_food', 'outdoor -> search -> eat'),
('Cat', '20260918224523', 'g_avoid_danger', 'indoor -> stay'),
('Cat', '20260918224523', '_plan', 'outdoor -> search -> eat -> return');
```

### 特殊设定
- 仅 Ego 拥有
- _tick 引用状态表中的 tick
- 一个状态下可以产生多个意图，对应多个目标
- 多目标综合成一条可执行路径，用特殊 key _plan 标记
- 与经历表机制一致，共用一张表，靠 _from 区分主体

### 强制约定
无

---

## 2.10 反馈(_feedback)
### 总体介绍
反馈表存储意图执行全过程的实时反馈数据，用于认知迭代、目标修正。属于 Ego 专属认知表。
_tick 对应意图表中的 _tick，实际上也是上一个状态表中的 tick。反馈表只对应 _plan 一条，因为最终执行的只有综合后的那一条路径。

### hoc
嵌套字典。
```python
_feedback = {
    "Cat": {
        "20260918224523": "success"
    }
}
```
- 第一层 key：主体名，如 Cat
- 第二层 key：_tick，对应意图表中的 _tick
- value：反馈内容

### dbfs
共用一个 `_feedback` 表。

**字段**
- _from：TEXT，主体名
- _tick：TEXT，对应意图表中的 _tick
- value：TEXT，反馈内容

**建表语句**
```sql
CREATE TABLE _feedback (
    _from   TEXT,
    _tick   TEXT,
    value   TEXT
);
```

**示例数据**
```sql
INSERT INTO _feedback (_from, _tick, value) VALUES
('Cat', '20260918224523', 'success');
```

### 特殊设定
- 仅 Ego 拥有
- _tick 对应意图表中的 _tick
- 一条反馈对应一条 _plan，不会有多条
- 与经历表机制一致，共用一张表，靠 _from 区分主体

### 强制约定
无

---

## 2.11 语言(_language)
### 总体介绍
语言表支撑符号层与参数约束解析，存储短句范式、符号表征、特征组合、习惯表达。属于 Ego 专属认知表。
用于 L 符号层与自然语言之间的双向翻译。

### hoc
字典。
```python
_language = {
    "sym_risk": "风险等级",
    "sym_profit": "收益水平",
    "g_find_food": "寻找食物",
    "g_avoid_danger": "躲避危险"
}
```

### dbfs
共用一个 `_language` 表。

**字段**
- key：TEXT，符号 ID
- value：TEXT，自然语言表达

**建表语句**
```sql
CREATE TABLE _language (
    key     TEXT,
    value   TEXT
);
```

**示例数据**
```sql
INSERT INTO _language (key, value) VALUES
('sym_risk', '风险等级'),
('sym_profit', '收益水平'),
('g_find_food', '寻找食物'),
('g_avoid_danger', '躲避危险');
```

### 特殊设定
- 仅 Ego 拥有
- 负责符号与自然语言的双向翻译
- 不参与内部推演计算

### 强制约定
无

---

## 2.12 训练数据(_train)
### 总体介绍
训练数据表聚合系统内全表数据与外部数据，为模型训练、Ego 总结反思、认知升级提供数据源。属于 Ego 专属认知表。
数据从其他数据表中总结出来，用于特殊项目的专属训练。

### hoc
嵌套字典。
```python
_train = {
    "ego_reflect": {
        "20260918224523": {
            "state": {},
            "intent": {},
            "feedback": {}
        }
    }
}
```
- 第一层 key：_target，训练目标或用途
- 第二层 key：_tick
- 第三层 key：数据来源或类型
- value：数据内容

### dbfs
共用一个 `_train` 表。

**字段**
- _target：TEXT，训练目标或用途
- _tick：TEXT，记录当前 tick
- key：TEXT，数据来源或类型
- value：TEXT，数据内容

**建表语句**
```sql
CREATE TABLE _train (
    _target  TEXT,
    _tick    TEXT,
    key      TEXT,
    value    TEXT
);
```

**示例数据**
```sql
INSERT INTO _train (_target, _tick, key, value) VALUES
('ego_reflect', '20260918224523', 'state', '{}'),
('ego_reflect', '20260918224523', 'intent', '{}'),
('ego_reflect', '20260918224523', 'feedback', '{}');
```

### 特殊设定
- 聚合系统内全表数据 + 外部数据
- _target 标记训练目标或用途
- 用于模型训练、Ego 总结反思、认知升级

### 强制约定
无

---

## 2.13 报告总结(_report)
### 总体介绍
报告总结表是系统综合观测面板，不参与底层 tick 流转与引擎核心运算。用于聚合全表核心指标供人机观测，支撑 Ego 虚拟推演，存储假想实验观测结果，区分真实运行数据与虚拟推演数据。
属于上层观测非基础表。

### hoc
嵌套字典。
```python
_report = {
    "real": {
        "20260918224523": {
            "state": {},
            "intent": {},
            "feedback": {}
        }
    },
    "virtual": {
        "20260918224523": {
            "state": {},
            "intent": {},
            "feedback": {}
        }
    }
}
```
- 第一层 key：数据类型，real / virtual
- 第二层 key：_tick
- 第三层 key：观测来源或类型
- value：观测内容

### dbfs
共用一个 `_report` 表。

**字段**
- _type：TEXT，数据类型，real / virtual
- _tick：TEXT，记录当前 tick
- key：TEXT，观测来源或类型
- value：TEXT，观测内容

**建表语句**
```sql
CREATE TABLE _report (
    _type   TEXT,
    _tick   TEXT,
    key     TEXT,
    value   TEXT
);
```

**示例数据**
```sql
INSERT INTO _report (_type, _tick, key, value) VALUES
('real', '20260918224523', 'state', '{}'),
('real', '20260918224523', 'intent', '{}'),
('virtual', '20260918224523', 'state', '{}');
```

### 特殊设定
- 不参与底层 tick 流转与引擎核心运算
- 区分真实运行数据与虚拟推演数据
- 支撑 Ego 虚拟推演（脑海试运行）

**数据类型说明**
- real：真实运行数据
- virtual：虚拟推演数据

### 强制约定
无

---

## 2.14 AI 协作（_llm）
### 总体介绍
AI 协作表记录人机协作过程中，特定 ID 的 prompt 与决策理由。属于上层观测非基础表。
用于追溯协作历史、复盘决策依据、支撑后续迭代。

### hoc
嵌套字典。
```python
_llm = {
    "prompt_001": {
        "version": "20260918224522",
        "prompt": "...",
        "reason": "..."
    }
}
```

### dbfs
共用一个 `_llm` 表。

**字段**
- id：TEXT，协作记录 ID
- version：TEXT，版本号，格式 YYYYMMDDHHMMSS
- prompt：TEXT，用户输入的 prompt
- reason：TEXT，决策理由

**建表语句**
```sql
CREATE TABLE _llm (
    id       TEXT,
    version  TEXT,
    prompt   TEXT,
    reason   TEXT
);
```

**示例数据**
```sql
INSERT INTO _llm (id, version, prompt, reason) VALUES
('prompt_001', '20260918224522', '...', '...');
```

### 特殊设定
- 不参与引擎计算
- 只存理由，不存结果
- 记录协作历史，支撑复盘与迭代

### 强制约定
无

---

## 2.15 FORGE（_forge）
### 总体介绍
FORGE 表是操作记录表，记录 FORGE 增量防护模块与 GOV 存量改造模块的全量操作痕迹。属于上层观测非基础表。
用于追溯每次变更的规则校验、评审结果、决策依据、治理进度，支撑工程纪律的常态化审计。

### 为什么没有 hoc
FORGE 表是引擎内部操作记录，由引擎自动写入，不经过人工声明，因此不分 hoc / dbfs 形态。

### dbfs
共用一个 `_forge` 表。

**字段**
- id：TEXT，操作记录 ID
- _tick：TEXT，记录当前 tick
- _module：TEXT，模块，FORGE / GOV
- _action：TEXT，动作，如 Fortify / Observe / Refine / Gather / Enforce / Gauge / Outline / Verify
- _target：TEXT，操作目标
- _result：TEXT，操作结果
- _reason：TEXT，操作理由

**建表语句**
```sql
CREATE TABLE _forge (
    id       TEXT,
    _tick    TEXT,
    _module  TEXT,
    _action  TEXT,
    _target  TEXT,
    _result  TEXT,
    _reason  TEXT
);
```

**示例数据**
```sql
INSERT INTO _forge (id, _tick, _module, _action, _target, _result, _reason) VALUES
('op_001', '20260918224523', 'FORGE', 'Fortify', '...', '...', '...');
```

### 特殊设定
- 不参与引擎计算
- 记录 FORGE / GOV 两个模块的操作痕迹
- 支撑常态化审计与追溯

**模块动作定义**
- FORGE：增量防护模块，动作包含 Fortify / Observe / Refine / Gather / Enforce
- GOV：存量改造模块，动作包含 Gauge / Outline / Verify

### 强制约定
无

---

# 第三部分：Q 函数写法
## 总体介绍
Q 是表征关系的基本单元，可以是代码，也可以是模型。有独立编号，单独存储。不属于 Matter，也不属于 Energy。

### hoc
直接以函数形式写在脚本中。
```python
def q3f8a2():
    # prompt: 根据血氧和损耗计算健康度
    # reason: 血氧是主要指标，损耗是修正项
    return blood_oxygen - loss
```
- 函数头不声明参数
- 参数是全局变量，运行时由引擎注入
- prompts 和 reason 以注释形式写在函数内部
- 不写 return 也可以，看 Q 的用途

### dbfs
作为独立脚本文件存储，与数据库元数据建立映射。
```python
# q3f8a2.py
def q3f8a2():
    # prompt: 根据血氧和损耗计算健康度
    # reason: 血氧是主要指标，损耗是修正项
    return blood_oxygen - loss
```
同时入 _llm 表留痕：
```sql
INSERT INTO _llm (id, version, prompt, reason) VALUES
('q3f8a2', '20260918224522', '根据血氧和损耗计算健康度', '血氧是主要指标，损耗是修正项');
```

### 引用方式
- 格式：`q:<q_id>`
- 示例：`q:q3f8a2`

### 可被引用的位置
- Matter 的 C 能力层
- 参数 value
- 约束表达式
- Ego 的推演、评估、迭代
- Energy 的状态更新、时序计算

### 版本管理
- hoc：无版本管理
- dbfs：Q 本身不自带版本号，版本信息写在注册表的 value 里
- 升级时，在注册表里查哪些 Q 可以升级

```python
_register = {
    "q3f8a2": {
        "label": "健康度计算",
        "version": "20260918224522"
    }
}
```

### 特殊设定
- 函数名是 q + 随机数，无语义，意义在注册表里
- 函数头不声明参数，参数从全局变量取
- prompts 和 reason 以注释形式写在函数内部
- dbfs 下同时入 _llm 表

### 强制约定
- 函数统一格式为 `def qxxxxxx():`，不额外添加下划线
- 必须写 prompts 和 reason 注释

# 第四部分：编码原则
本部分不绑定具体语言，适用于 Python、JS、Rust 及后续任何实现语言。
以下原则为强制约束，不是风格建议。违反即视为实现不合规。
一、以结构为先，不以语法炫技为先
代码首先服务于结构表达。能直白写清结构、关系、约束的写法优先；能少用语言特性就少用。不为了“高级”引入装饰器、元类、宏、隐式转换等技巧。

二、核心只依赖标准库
引擎核心、实例结构定义、注册机制、脚手架工具，一律只使用语言标准库。禁止引入第三方包。

三、第三方依赖按需就近引入
业务能力所需的第三方包，必须在具体功能单元内按需引入，就近使用、就近释放。禁止污染全局，禁止渗透进结构定义。 换源、换库时，只改对应功能单元，不动其他部分。

四、依赖失败就地兜底
功能单元内引入依赖时，自行处理缺失、版本不符、初始化失败等情况，给出明确提示，不把异常抛到上层调用链。

五、可读优先于简洁
一行一条、显式声明、固定位置，优先于合并、循环生成、动态拼接。结构要能被人和 AI 直接读出来，而不是先运行一遍才知道写了什么。

六、声明与逻辑分离
结构、参数、约束、关系用声明式写法；动作、计算、推理用函数式写法。两者禁止混写，禁止互相嵌套。

七、命名服从语义，不服从长度
实体、命令、表名保留完整语义，不以缩短为美。局部缩写仅限函数内部临时变量。

八、少魔法，多老实代码
能用普通字典解决的，不用类；能用普通函数解决的，不用装饰器；能用显式 key 解决的，不用动态拼。禁止为了“高级”牺牲可预测性。

九、语言可替换，原则不替换
本原则不绑定 Python。 后续使用 JS、Rust 或其他语言时，同样遵循：结构优先、核心无第三方依赖、依赖就近、失败兜底、可读优先。违反即视为实现不合规。

十、为落库和迁移留路
写法上尽量贴近目标存储形态。扁平 key 对应数据库行，显式字段对应表列，版本字段对应版本行。避免写出难以压平、难以迁移的结构。