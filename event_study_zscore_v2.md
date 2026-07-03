# Event Study Z-Score Specification v2.0
# 事件研究法 Z-Score 計算規格書（修正版）

> 作者：石頭哥 | 元智大學 DBA | 更新日期：2026-07-03

---

## 1. 時間區間定義

| 區間名稱 | 代號 | 交易日範圍 | 長度 | 用途 |
|---|---|---|---|---|
| Estimation Period | EP | t = -55 ~ -16 | 40 days | 估計市場模型參數 α, β |
| Cleanse Gap | CG | t = -15 ~ -11 | 5 days | 清洗間隔，避免前瞻偏差 |
| Event Window | EW | t = -15 ~ +15 | 30 days | 觀察異常報酬 |
| Event Day | ED | t = 0 | 1 day | 事件日（營收公布日）|

**重要約束：EP 與 EW 不可重疊，中間必須有 CG 隔開。**

---

## 2. 時間軸示意圖

```
t = -55       t = -16  t = -15       t = 0        t = +15
  |<----  EP (40天) ---->|  |<----- EW (30天) ----->|
                         |CG|       Event Day ↑
                      (5天緩衝)
```

---

## 3. 核心概念修正（舊版 vs 新版）

| 項目 | 舊版（錯誤） | 新版（正確） |
|---|---|---|
| 估計期 | 事件前 15 天 | 事件前 55~16 天（40 天） |
| 與事件期關係 | 重疊 | 中間隔 5 天清洗間隔 |
| Z-Score 比較對象 | 事件前 vs 事件後報酬 | 實際報酬 vs 模型預測報酬 |
| 買進判斷依據 | 無明確邏輯 | 分段 CAR 顯著性比較 |
| 市場模型 | 未建立 | OLS 估計 α, β |

---

## 4. 計算公式

### Step 1：市場模型（估計期 OLS）

```
R_it = α_i + β_i * R_mt + ε_it    (t ∈ Estimation Period: -55 ~ -16)

where:
  R_it  = 個股 i 在 t 日的報酬率
  R_mt  = 大盤指數在 t 日的報酬率（如台灣加權指數 TAIEX）
  α_i, β_i = OLS 估計參數
```

### Step 2：異常報酬率 AR（事件期）

```
AR_it = R_it_actual - (α̂_i + β̂_i * R_mt)    (t ∈ Event Window: -15 ~ +15)
```

### Step 3：累積異常報酬 CAR

```
CAR_i(a,b) = Σ AR_it    (t 從 a 到 b)

CAR_i(-15,-1)  = Σ AR_it  (t = -15 ~ -1)   ← 洩漏期
CAR_i(0,+15)   = Σ AR_it  (t = 0 ~ +15)    ← 反應期
CAR_i(-15,+15) = Σ AR_it  (t = -15 ~ +15)  ← 整體事件期
```

### Step 4：Z-Score 檢定

```
Z = CAR_i(a,b) / σ_CAR

where:
  σ_CAR = σ_ε * √(b - a + 1)
  σ_ε   = 估計期殘差的標準差 = sqrt( Σ ε_it² / (T_est - 2) )
  T_est = 估計期長度 = 40
```

### Step 5：顯著性判斷

```
|Z| > 1.96  →  5% 顯著水準  (*)
|Z| > 2.58  →  1% 顯著水準  (**)
|Z| > 3.29  →  0.1% 顯著水準 (***)
```

---

## 5. Python 實作程式碼

### 5.1 估計期市場模型（僅在 EP 執行）

```python
import statsmodels.api as sm
import numpy as np

# 估計期資料：t = -55 ~ -16
for each_stock_i in stock_list:
    R_i = 個股報酬率序列  # (40 days)
    R_m = 大盤指數報酬率序列  # (40 days)

    # OLS 迴歸
    model = sm.OLS(R_i, sm.add_constant(R_m))
    result = model.fit()

    alpha_i = result.params[0]          # 截距
    beta_i  = result.params[1]          # 斜率
    sigma_e = np.sqrt(result.mse_resid) # 殘差標準差
```

### 5.2 異常報酬率計算（EW 全區間）

```python
# 事件期資料：t = -15 ~ +15
AR = {}
for t in range(-15, 16):
    R_actual = 個股實際報酬率[t]
    R_market = 大盤實際報酬率[t]

    # 預測正常報酬
    R_normal = alpha_i + beta_i * R_market

    # 異常報酬
    AR[t] = R_actual - R_normal
```

### 5.3 分段 CAR 與 Z-Score 計算

```python
# 分段累積異常報酬
CAR_leakage  = sum(AR[t] for t in range(-15, 0))    # CAR(-15, -1)
CAR_reaction = sum(AR[t] for t in range(0, 16))     # CAR(0, +15)
CAR_total    = sum(AR[t] for t in range(-15, 16))   # CAR(-15, +15)

# Z-Score 計算函數
def calculate_Z(CAR, start_day, end_day, sigma_e):
    window_length = end_day - start_day + 1
    sigma_CAR = sigma_e * np.sqrt(window_length)
    Z = CAR / sigma_CAR
    return Z

# 各段 Z-Score
Z_leakage  = calculate_Z(CAR_leakage,  -15, -1,  sigma_e)
Z_reaction = calculate_Z(CAR_reaction,   0, +15, sigma_e)
Z_total    = calculate_Z(CAR_total,    -15, +15, sigma_e)
```

### 5.4 買進時機判斷邏輯

```python
def buy_timing_decision(Z_leakage, Z_reaction, CAR_leakage, CAR_reaction):
    """
    根據分段 CAR 與 Z-Score 判斷事件前買或事件後買
    """
    SIG_LEVEL = 1.96  # 5% 顯著水準

    leakage_significant  = abs(Z_leakage)  > SIG_LEVEL
    reaction_significant = abs(Z_reaction) > SIG_LEVEL

    if CAR_leakage > 0 and leakage_significant and not reaction_significant:
        return "AVOID: 事件前已洩漏漲完，事件後無延續，不建議進場"

    elif CAR_leakage <= 0 and CAR_reaction > 0 and reaction_significant:
        return "BUY_AFTER: 事件前無洩漏，事件後顯著上漲，事件後進場"

    elif CAR_leakage > 0 and CAR_reaction > 0 and reaction_significant:
        return "CAUTION: 事件前後皆漲，但事件前已漲一波，事件後風險較高"

    elif CAR_leakage < 0 and CAR_reaction > 0 and reaction_significant:
        return "STRONG_BUY_AFTER: 事件前被錯殺，事件後反彈，事件後進場最佳"

    else:
        return "NO_SIGNAL: 無顯著異常報酬，不建議以此事件為交易依據"
```

---

## 6. 四種情境判斷

| 情境 | CAR(-15,-1) | CAR(0,+15) | 判斷結果 |
|---|---|---|---|
| A（洩漏嚴重） | > 0 顯著 | ≈ 0 不顯著 | 事件前已漲完，不建議進場 |
| B（純事件後反應） | ≈ 0 | > 0 顯著 | 事件後進場，最有利 |
| C（前後皆漲） | > 0 顯著 | > 0 顯著 | 事件後可進但風險較高 |
| D（事件前錯殺） | < 0 | > 0 顯著 | 事件後反彈，最佳進場點 |

---

## 7. 輸出格式規格

對每個事件（營收公布），輸出以下欄位：

| 欄位 | 說明 |
|---|---|
| stock_id | 股票代號 |
| event_date | 事件日 |
| CAR(-15,-1) | 洩漏期累積異常報酬 |
| Z(-15,-1) | 洩漏期 Z-Score |
| CAR(0,+15) | 反應期累積異常報酬 |
| Z(0,+15) | 反應期 Z-Score |
| CAR(-15,+15) | 總事件期累積異常報酬 |
| Z(-15,+15) | 總事件期 Z-Score |
| buy_signal | 買進時機建議（AVOID / BUY_AFTER / CAUTION / STRONG_BUY_AFTER / NO_SIGNAL）|
| significance | 顯著性標記（* p<0.05, ** p<0.01, *** p<0.001）|

---

## 8. 執行流程摘要（給 Hermes Agent）

```
Step 1: 抓取個股與大盤歷史報酬率資料
Step 2: 劃分 Estimation Period (t=-55~-16) 與 Event Window (t=-15~+15)
Step 3: 用 EP 資料跑 OLS 市場模型 → 得 alpha, beta, sigma_e
Step 4: 用 alpha, beta 預測 EW 內每一天的正常報酬
Step 5: 計算每一天的 AR = 實際報酬 - 正常報酬
Step 6: 分段累積 CAR(-15,-1), CAR(0,+15), CAR(-15,+15)
Step 7: 計算各段 Z-Score
Step 8: 執行 buy_timing_decision() 輸出買進建議
Step 9: 彙整成表格輸出
```

---

## 9. 注意事項

1. 估計期長度 40 天偏短，建議樣本數（事件數）至少 30 個以上
2. 若個股流動性低，可考慮改用市場調整模型（Market-Adjusted Model）取代 OLS
3. 大盤指數建議用台灣加權指數（TAIEX）或產業指數
4. 事件日定義需明確：營收公布日為「公告日」或「交易日次日」
5. 需排除事件期間有其他重大公告（如配股、法說會）的干擾

---

## 10. 一句話總結

> **Z-Score 檢定的是「實際報酬是否顯著偏離正常模型預測」，不是比較事件前後誰漲得多。要判斷事件前買還是事件後買，關鍵看 CAR(−15,−1) 與 CAR(0,+15) 哪一段顯著為正——洩漏期漲代表提前進場已來不及，反應期漲代表事件後還有機會。**

---

## 11. 實務判斷預設（給 Hermes / Prompt 使用）

當分析的是**單一事件日**（例如營收公告）時，實務上可改用更直接的前後窗口比較：

- **事件前窗口：** T-10 ~ T-1
- **事件後窗口：** T+1 ~ T+10
- **比較重點：** 哪一段 CAR 較強、較顯著，決定事件前買或事件後買

### 判斷原則

1. **前窗 CAR 顯著為正**：表示訊息可能已提前反應，事件前進場優勢下降。
2. **後窗 CAR 顯著為正，前窗未明顯洩漏**：事件後進場較有利。
3. **兩窗都不顯著**：視為 no signal，不建議只靠這個事件下單。
4. **Z-Score 只作為顯著性檢查**：主角仍是 CAR 與前後窗口比較，不是單獨看 z-score 大小。

---

*本規格書由 Kimi AI + Perplexity AI 協作整理，供 Hermes Agent 讀取執行。*
