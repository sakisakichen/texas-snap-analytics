# SNAP Analytics Platform V2 — Production Notes

**Module:** Module 3 — Analytics Modeling / Gold Layer  
**Version:** v1  
**Topics:** Dashboard Design Process + KPI Governance

## Part 1 — Dashboard Design Process

| Production Topic | Production Thinking | Why | SNAP Example | Interview Answer |
|---|---|---|---|---|
| Decision-first Design | 從 user 要做的 decision 往回推，而不是從 available data / charts 開始 | 避免 dashboard 只是 information display | Leadership 要判斷哪些 counties 值得明年 resource planning 關注 | “I start with the decision the user needs to make, then work backward to the questions, metrics, and data required.” |
| Audience & Decision Context | Executive / Manager / Analyst 的 responsibility、time horizon、detail needs 不同 | One-size-fits-all 容易 information overload 或 low adoption | Leadership 看 strategic signals；Analyst 做 RCA | “I identify the audience and decision context before deciding the level of detail.” |
| Business Questions before Metrics | Metric 應該因為回答 business question 而存在 | 避免「有欄位就做 KPI」 | Demand → Need Context → Performance | “Every metric should answer a specific business question.” |
| Focused & Trusted Metrics | Consistency over completeness | KPI 太多或定義鬆散會降低 trust | v1 只保留少量 decision-relevant metrics | “I prefer a smaller set of trusted, consistently defined metrics.” |
| Interpretation > Inspection | 提供 benchmark、context、comparison、exception，而不是只顯示 raw number | User 不應自行 reverse-engineer meaning | Timeliness 92% + official 95% benchmark | “I design for interpretation so users understand what changed and why it matters.” |
| Information Hierarchy | Summary signal → context → detail | 讓 user 快速判斷是否需要深入 | Demand → Need → Performance → investigate | “I structure dashboards from high-level signals to supporting context and detail.” |
| Signal vs. Investigation | Leadership 看 signal；Analyst 做 deeper investigation | 避免 Strategic Dashboard 變成 RCA workspace | Leadership flag county；Analyst 看 monthly drivers | “Leadership needs the signal; analysts need the investigation.” |
| Prototype before Full Build | 先 mockup / PoC 再 full build | 提早驗證 requirements、降低返工 | SNAP dashboard layout 先對照 BQ | “I validate the proposed design before investing in the full build.” |
| Stakeholder Review / UAT | Technical correctness 不等於 business correctness | 確認 meaning、workflow、usability | Business SME review metric meaning | “Before release, I validate both data correctness and business usability.” |
| Adoption is part of Design | Publish ≠ project done | Low adoption 可能代表 workflow mismatch | Monitor whether users still export data manually | “I treat adoption as part of dashboard success.” |
| Dashboard is a Living System | Usage、feedback、definitions、priorities 都會變 | 保持 dashboard trustworthy | Metric definition change → update model + dashboard | “Publishing isn't the end; I monitor usage, feedback, and definition changes.” |

### Dashboard Design Mental Model

`Business Problem / Decision → Stakeholders & Users → Business Questions → Trusted Metrics → Prototype / Design → Summary / Context / Drill-down → Review / UAT → Release → Adoption / Feedback → Iterate`

---

## Part 2 — KPI Governance

| Production Topic | Production Thinking | Why | SNAP Example | Interview / Production Note |
|---|---|---|---|---|
| Business Objective → KPI | KPI 從 business objective / decision 反推 | 避免從 available data 開始選 KPI | Resource planning → Demand / Need / Performance | “I start with the business objective before defining the metric.” |
| Business Meaning First | 寫公式前先定義 metric 代表什麼 | Technically correct 不代表 business-correct | SNAP Demand = incoming applications | Business meaning before calculation |
| Explicit Metric Definition | 定義 formula、grain、time window、filters、inclusions/exclusions、source | 讓 metric 可重現、可 review | Timeliness 要明確 numerator / denominator / period | Metric definition should be reproducible |
| Grain | 明確定義 observation level：What does one row represent? | Grain 不一致會造成 aggregation / comparison 錯誤 | Intended Gold grain = County × Reporting Month | Always clarify grain before aggregation |
| Business Alignment | 不同 team 數字不同時先比較 purpose / definition，不先假設有人錯 | 不同數字可能回答不同問題 | Finance vs Product Active Customer | Resolve meaning before resolving SQL |
| Consistency ≠ One Metric for Everyone | 不同 purpose 可以有不同 metric，但名稱與定義必須清楚 | 避免 false standardization | Revenue-active vs product-active customer | Same definition should produce the same result everywhere |
| Metric Ownership | Business Owner / Steward 管 meaning/accountability；Analytics/Data 管 translation/implementation/validation | Analytics 不應自行決定 business truth | Program SME confirms meaning; Analytics implements | Separate business ownership from technical implementation |
| Centralized Metric Logic | Shared KPI 不應每個 BI report 重算 | 避免 metric drift | Timeliness logic in Gold / semantic layer | Define once, use everywhere |
| Business Glossary | Shared terms需要 centrally curated definitions | Formula一致但 terminology 不一致仍會誤解 | Application / Household / Recipient | Shared language is part of governance |
| Testing & Validation | 驗證 implementation 是否符合 approved definition | Centralized wrong logic is still wrong | Compare Gold metric to source/sample cases | Governance includes trust, not just documentation |
| Version Control | Metric/model logic changes should be traceable | 知道誰改什麼、為什麼 | Git-manage Gold metric logic | Treat metric logic like production code |
| Change Management | Definition change → review → implementation → test → downstream update | 避免不同 dashboard 使用不同版本 | Timeliness rule change propagates downstream | Publishing a metric isn't the end of governance |
| Governance Model Depends on Organization | 不一定每家公司都需要 Metric Council | 避免 over-engineering | Side project 模擬 clear owner，不假裝有 enterprise council | Governance should fit organizational scale |

### KPI Governance Mental Model

`Business Objective → Business Meaning → Metric Definition → Business Alignment → Owner / Steward → Central Implementation → Testing → BI / Dashboard → Change Management`

### Core Principle

> **Business Governance defines what the metric means. Technical Governance ensures that meaning is implemented consistently everywhere.**

### Interview Scenario — Conflicting Metric Numbers

**Scenario:** Finance reports Active Customers = 12,400; Product reports Active Customers = 15,800.

Production response:

`Business Purpose → Definition → Grain → Formula → Time Window → Filters → Inclusion/Exclusion → Source → Stakeholder Alignment → Ownership → Central Implementation → Validation → Downstream Update → Change Governance`

Do not assume one number is wrong. Determine whether the teams need one shared enterprise definition or two legitimately different metrics for different business purposes.

---

## Current SNAP Application

- Primary user: Program Leadership
- Dashboard type: Strategic
- Decision: Which counties warrant leadership attention for next-year resource planning?
- BQ1 Demand → Annual SNAP Application Volume
- BQ2 Need Context → Applications per 1,000 Residents + Poverty Rate
- BQ3 Performance → Application Processing Timeliness Rate + official 95% FNS benchmark
- Avoid unsupported composite priority scores
- Leadership needs the signal; analysts need the investigation



| Production Topic                        | Production Thinking                                              | Why                                                         | SNAP Example                                                                   | Interview Use                          |
| --------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------------------ | -------------------------------------- |
| Semi-structured Excel Parsing           | Parse by **business section/header**, not fixed row position     | Excel layout可能改變，row number 不可靠                             | 同一 Timeliness sheet 有 Applications + Redeterminations 兩張 logical tables        | Messy source / transformation          |
| Human-readable vs Machine-readable Data | Production source 不一定是 tidy table                                | Excel 常為人閱讀設計                                               | Title、兩張 tables、TOTAL、notes 都在同一 sheet                                         | Real-world data cleaning               |
| Schema Drift Detection                  | Human 定義 expected schema；pipeline 自動驗證所有 files                   | 不可能人工逐檔檢查                                                   | 每月自動確認 `Region / Disposed / Timely / Percent`                                  | Pipeline health                        |
| TOTAL Reconciliation                    | TOTAL 可作 validation control，但不應成為 analytical row                 | 可檢查 extraction completeness，同時避免 downstream double counting | `SUM(detail)` ↔ source `TOTAL`                                                 | Data validation                        |
| Source Metadata vs Analytical Records   | Notes/definitions 不進 Silver analytical rows，但 Bronze 保留原始 source | 排除非 record 資訊又不丟 source evidence                            | Timeliness table 下方 definitions                                                | Bronze vs Silver responsibility        |
| Critical Metadata Cross-check           | 同一重要 attribute 有兩個 source signals 時，可 derive + reconcile         | 防止 filename/title mismatch                                  | filename month ↔ Excel title month                                             | Data reliability                       |
| Categorical Identifier                  | 不要看到數字就轉 numeric                                                 | Identifier 不具有數學意義                                          | Region `"01"`、`"02/09"` 維持 string                                              | Type design                            |
| Undocumented Source Categories          | **Preserve → Flag → Document → Control downstream usage**        | 不知道不能等於刪除，也不能猜                                              | `CCC`, `DATA INT`, `MEPD`, `PERFORMANC`, `ST OFFICE`, `VIC`, `UNKNOWN`         | Ambiguous source handling              |
| Necessary Standardization               | Transformation 必須解決明確問題，不為 cosmetic consistency 而改               | 避免 unnecessary transformation                               | 不刻意把 `Applications` 改成 `Application`                                           | Transformation judgment                |
| Explicit Measure Naming                 | Column name 應表達 business role                                    | 避免 ambiguous downstream usage                               | `Disposed → disposed_count`; `Timely → timely_count`                           | Data modeling                          |
| Source Metric vs Governed Metric        | Source-provided metric 與 analytical metric 分開                    | Source percentage 要驗證，不能直接當 governed KPI                    | `Percent → source_percent`; 後面與 `timely_count / disposed_count` reconciliation | Metric governance                      |
| Pipeline Health                         | Job success ≠ healthy pipeline                                   | 還要檢查 completeness、schema、DQ、downstream readiness            | schema drift / missing section / validation gate                               | **Pipeline Health interview question** |
