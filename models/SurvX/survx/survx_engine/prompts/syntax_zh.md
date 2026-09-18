# SurvX 范式语法规范（抽取版：仅语法相关章节）
> 文档定位：Matter / Ego / F 实体描述语法，用于蓝图定义，属于描述层语法，不是宿主编程语言。
> 用途：人工编写、AI生成Matter蓝图；蓝图最终编译映射到底层三张物理表 `_parameter` / `_constraint` / `_relation`。

## 1. 核心语法总原则
1. 所有实体都拥有全局唯一ID，ID一经分配永久不变；引用实体**必须使用预注册ID**，禁止裸字符串直接引用（L符号表征层除外）。
2. 语法分为：实体声明语法、分层描述语法、关系语法、约束表达式语法、F构件语法、契约语法、Ego自指符号语法。
3. 语法只生成**结构化蓝图**，蓝图不直接执行；蓝图送入引擎校验，校验通过后落地存入底层数据表，由Energy驱动引擎执行。
4. 支持两种书写模式：
   - 完整声明模式：完整写出S/C/R/O/F(/G/L)分层，适合Matter/Ego正式实体定义
   - 精简F模式：仅定义输入输出契约与求值逻辑，适合轻量F单元

## 2. 实体声明基础语法
```
<entity_type> <entity_id> [ "optional human readable name" ] {
    <分层块>
}
```
- entity_type：`F` / `Matter` / `Ego`
- entity_id：全局唯一注册ID，字母数字下划线，不可空格
- human readable name：可选，仅AI阅读/文档展示，**不参与引擎计算**

示例：
```
Matter mat_vol_filter "波动率筛选实体" {
    ...分层内容...
}
```

## 3. Field五层分层语法（S-C-R-O-F）
Matter（Field）内部由5个块组成，块可省略，但S结构块必须存在。
```
Matter <id> {
    Structure {
        // S：结构层，定义子构件、嵌套实体、内部F列表
        // 语法：子实体引用，绑定到当前实体作用域
        sub <child_type> <child_ref_id>;
    }
    Capability {
        // C：能力层，构件组合、协作规则、调用顺序
        use <f_id>;
        compose [f_a, f_b] -> out_id;
    }
    Relation {
        // R：关系层，主体subject -> effect客体
        link subject:<id> -> effect:<id> [relation_tag];
    }
    Ordinance {
        // O：约束层，约束表达式
        rule <constraint_id>: <constraint_expr>;
    }
    Feature {
        // F：特征层，元特征、性能、时效
        attr <key> = <literal_or_ref>;
    }
}
```

## 4. Ego七层分层语法（S-C-R-O-F-G-L）
Ego继承Field五层，新增G目标层、L表征层；G目标层必选，L表征层可选。
```
Ego <id> {
    Structure { ... }
    Capability { ... }
    Relation { ... }
    Ordinance { ... }
    Feature { ... }
    Goal {
        // G：目标层，多目标、权重、优化方向
        objective <g_id> weight=<float>: <expression>;
    }
    Symbol {
        // L：表征层（自认知符号层）
        belief <symbol_id> = <expr>;
    }
}
```

## 5. F构件语法（最小功能单元）
F是最小单元，支持轻量表达式、复合聚合、神经网络F。
```
F <f_id> [ "F名称" ] {
    contract {
        // 六维输入输出契约定义
        input(...)
        output(...)
    }
    eval: <expression>;
}
```
- `eval`：求值表达式，支持字面量、ID引用、数学算子、条件判断
- 复合F：内部可调用其他F，引擎递归求值并拦截无限递归
- 神经网络F：eval指向模型权重参数ID，输入实体ID向量，输出标量/向量

## 6. 六维契约语法（contract）
```
contract {
    // 1.数据类型（结构态）
    input T(<schema_def>): <name>;
    output T(<schema_def>): <name>;

    // 2.数值范围（值态）
    range <var> in [low, high];
    range <var> in (low, high);
    range <var> in [low, high);

    // 3.状态标识（逻辑态）
    status [ok, fail, pending];

    // 4.时间与频率（时序态）
    tick_freq = <number>;
    timeout = <seconds>;

    // 5.环境交互（环境态）
    source = <entity_id>;
    sink = <entity_id>;

    // 6.元数据（描述态）
    meta note = "human comment";
    meta version = "x.y.z";
}
```

## 7. 约束表达式语法（Ordinance rule）
引擎归一化算子：全部转为基础`<`算子，支持区间表达式。
支持符号：`()` `[]` `(]` `[)`
```
// 写法示例
rule r1: val > 0.05;
rule r2: val <= 1.0;
rule r3: val in [0.01, 0.95];
rule r4: (A < T+ε) AND (-A < -T+ε);
```
引擎内部自动转换：
- `A ≤ T` → `A < T + ε`
- `A > T` → `-A < -T`
- `A ≥ T` → `-A < -T + ε`
- `A == T` → `(A < T+ε) AND (-A < -T+ε)`

## 8. Relation 关系语法
```
link subject:<id> -> effect:<id> [tag];
```
- subject：关系主体
- effect：关系客体
- tag：关系标签（call / depend / associate / causal）
> 关系本身不固定语义，语义由配套F构件解释。

## 9. 引用规约
1. 跨表引用前缀：
   - `param:<id>` 参数表
   - `constraint:<id>` 约束表
   - `rel:<id>` 关系表
2. 作用域：`context_path` 控制作用域，下层可覆盖上层定义
3. value字段两种类型：
   - 字面量：数值、字符串、布尔
   - F引用：`f:<f_id>`，运行时动态求值

## 10. 生命周期与版本标记语法
```
attr active = true; // true参与tick；false休眠，数据保留
attr version = <integer>;
```
- 节点不物理删除，active标记休眠
- version自增，更新生成新版本，旧版本永久保留

## 11. 工作流语法（演变式 / 补全式）
### 演变式工作流
```
workflow evolve <wf_id> {
    target <ego_id>;
    search_space within ordinance:<constraint_set>;
    score by goal:<goal_set>;
    select best;
    apply state_update;
}
```
### 补全式工作流
```
workflow complete <wf_id> {
    contract <contract_id>;
    gap detect;
    generate f/matter;
    validate by ordinance;
    register entity;
}
```

## 12. 语法编译规则
1. 顶层蓝图语法 → 解析抽象语法树AST
2. AST校验（引用存在性、结构合法性、约束校验）
3. 编译映射写入 `_parameter` / `_constraint` / `_relation` 三张物理表
4. 元信息字段（meta/note）**不参与引擎tick计算、约束校验**，仅用于AI阅读和文档
5. 蓝图编译只读原实体；修改时深度拷贝生成新副本，带新版本号
```

要不要我再精简一版，只保留**最小可用语法子集**（删掉工作流、注释描述，只留语法定义+极简示例），方便你做语法解析器原型？
