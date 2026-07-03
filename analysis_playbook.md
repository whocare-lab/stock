# 事件研究法分析操作手冊
# Analysis Playbook — Event Study Z-Score

> 作者：石頭哥 iiStone | 元智大學 DBA  
> 最後更新：2026-07-03  
> 規格書：https://raw.githubusercontent.com/whocare-lab/stock/main/event_study_zscore_v2.md

---

## 一、這份文件是什麼

這是我用 Perplexity Computer 對中美晶（5483.TWO）執行完整事件研究法分析後，整理出來的操作步驟記錄。目的是下次分析其他股票時，不必從頭摸索，直接照著步驟走。

**兩次分析成果已驗證可復現，適用於任何台灣上市/上櫃股票。**

---

## 二、分析規格（必讀）

### 時間區間定義（v2.0，勿更動）

| 區間 | 代號 | 交易日範圍 | 長度 | 用途 |
|---|---|---|---|---|
| 估計期 Estimation Period | EP | t = −55 ∼ −16 | 40天 | OLS 市場模型參數估計 |
| 清洗間隔 Cleanse Gap | CG | t = −15 ∼ −11 | 5天 | 防止估計期被事件資訊污染 |
| 事件期 Event Window | EW | t = −15 ∼ +15 | 30天 | 計算異常報酬 AR |
| 事件日 | ED | t = 0 | 1天 | 月營收公布日 |

> ⚠️ **重要：EP 與 EW 不可重疊，中間必須有 CG 隔開。這是 v2.0 最核心的修正。**

### 關鍵公式

```
# Step 1：市場模型 OLS（在 EP 執行）
R_it = α_i + β_i × R_mt + ε_it

# Step 2：異常報酬（在 EW 執行）
AR_it = R_it（實際）− (α̂_i + β̂_i × R_mt)

# Step 3：累積異常報酬（CAR）
CAR(−15,−1) → 洩漏期
CAR(0,+15)  → 反應期
CAR(−15,+15)→ 整體

# Step 4：Z-Score
Z = CAR(a,b) / [σ_ε × √(b−a+1)]
σ_ε = √[Σε²/(T_est−2)]，T_est = 40

# 顯著水準
|Z| > 1.96 → * (p<0.05)
|Z| > 2.58 → ** (p<0.01)
|Z| > 3.29 → *** (p<0.001)
```

---

## 三、分析流程（逐步說明）

### Step A：準備事件日清單

**月營收事件日規則：**
- 台灣上市公司每月 10 日前公布月營收（若遇假日則順延至下一個交易日）
- 實際交易日需用台灣大盤 `^TWII` 的交易日曆校正

```python
import pandas as pd
import yfinance as yf

# 取得台灣交易日曆
td = yf.download("^TWII", start="起始日", end="結束日", progress=False).index

def get_announce_date(year, month, td):
    target = pd.Timestamp(f"{year}-{month:02d}-10")
    candidates = td[td >= target]
    month_end = pd.Timestamp(f"{year}-{month:02d}-01") + pd.offsets.MonthEnd(0)
    candidates = candidates[candidates <= month_end]
    return candidates[0] if len(candidates) else None
```

### Step B：下載股價與大盤資料

```python
# 大盤代號：^TWII（台灣加權指數）
# 上市股票：{代號}.TW（例如 2330.TW 台積電）
# 上櫃股票：{代號}.TWO（例如 5483.TWO 中美晶）

# 需要足夠長的資料：
# 最早事件日往前推 55 個交易日（約 3 個月）
# 以 2023/01 起的事件為例，從 2022-06-01 開始抓

stock = yf.download("5483.TWO", start="2022-06-01", end="今天", progress=False)
taiex = yf.download("^TWII",    start="2022-06-01", end="今天", progress=False)

# 計算日報酬率（一定要 .squeeze() 避免 Multi-Index 問題）
stock_ret = stock['Close'].squeeze().pct_change().dropna()
taiex_ret = taiex['Close'].squeeze().pct_change().dropna()

# 對齊交易日
common = stock_ret.index.intersection(taiex_ret.index)
stock_ret = stock_ret.loc[common]
taiex_ret = taiex_ret.loc[common]
```

> ⚠️ **常見錯誤：不加 `.squeeze()` 會導致 `TypeError: unsupported format string passed to Series.__format__`**

### Step C：單一事件分析

```python
import statsmodels.api as sm
import numpy as np

def run_event_study(stock_ret, taiex_ret, event_date_str):
    dates = stock_ret.index
    t0_idx = dates.get_loc(dates[dates <= pd.Timestamp(event_date_str)][-1])

    # 檢查資料是否足夠
    if t0_idx - 55 < 0 or t0_idx + 15 >= len(dates):
        return None  # 跳過資料不足的事件

    # OLS 市場模型（EP：t=-55~-16，共40天）
    ep = list(range(t0_idx - 55, t0_idx - 15))
    Ri = stock_ret.iloc[ep].values.astype(float)
    Rm = taiex_ret.iloc[ep].values.astype(float)
    result = sm.OLS(Ri, sm.add_constant(Rm)).fit()
    alpha   = float(result.params[0])
    beta    = float(result.params[1])
    sigma_e = float(np.sqrt(result.mse_resid))

    # AR 計算（EW：t=-15~+15）
    AR = {}
    for t in range(-15, 16):
        idx = t0_idx + t
        ri = float(stock_ret.iloc[idx])
        rm = float(taiex_ret.iloc[idx])
        AR[t] = ri - (alpha + beta * rm)

    # 標準化 AR（Patell）
    SAR = {t: AR[t] / sigma_e for t in AR}

    # 分段 CAR
    CAR_l = sum(AR[t] for t in range(-15, 0))   # 洩漏期
    CAR_r = sum(AR[t] for t in range(0, 16))    # 反應期
    CAR_t = sum(AR[t] for t in range(-15, 16))  # 整體

    return {
        'AR': AR, 'SAR': SAR,
        'CAR_l': CAR_l, 'CAR_r': CAR_r, 'CAR_t': CAR_t,
        'alpha': alpha, 'beta': beta, 'sigma_e': sigma_e, 'r2': float(result.rsquared)
    }
```

### Step D：橫截面平均（N ≥ 30 事件）

```python
from scipy import stats

# 收集所有事件結果
results = [run_event_study(stock_ret, taiex_ret, ev['date']) for ev in events]
results = [r for r in results if r]  # 過濾 None

N = len(results)
t_range = list(range(-15, 16))

# 計算 AAR / CAAR
AAR  = {t: np.mean([r['AR'][t] for r in results]) for t in t_range}
CAAR = {}
run = 0.0
for t in t_range:
    run += AAR[t]; CAAR[t] = run

# BMP Cross-sectional t-test（最常用）
def bmp_t(a, b, results):
    CARs = [sum(r['AR'][t] for t in range(a, b+1)) for r in results]
    t_stat, p_val = stats.ttest_1samp(CARs, 0)
    sig = '***' if p_val<.001 else '**' if p_val<.01 else '*' if p_val<.05 else 'n.s.'
    return t_stat, p_val, sig, np.mean(CARs), CARs

# Patell Z-test（標準化 AR，更嚴格）
def patell_z(a, b, results):
    L = b - a + 1
    SARs = [sum(r['SAR'][t] for t in range(a, b+1)) / np.sqrt(L) for r in results]
    Z = np.sum(SARs) / np.sqrt(N)
    p_val = 2 * (1 - stats.norm.cdf(abs(Z)))
    sig = '***' if p_val<.001 else '**' if p_val<.01 else '*' if p_val<.05 else 'n.s.'
    return Z, p_val, sig

# 執行分段檢定
t_l, p_l, s_l, m_l, CARs_l = bmp_t(-15, -1,  results)
t_r, p_r, s_r, m_r, CARs_r = bmp_t(  0, 15,  results)
t_t, p_t, s_t, m_t, CARs_t = bmp_t(-15, 15,  results)
Z_l, pz_l, sz_l = patell_z(-15, -1,  results)
Z_r, pz_r, sz_r = patell_z(  0, 15,  results)
```

### Step E：分組分析（超預期 vs 低於預期）

```python
# 分組依據：月營收 YoY 年增率
# Beat：YoY > 0%（正成長，市場通常視為超預期）
# Miss：YoY ≤ 0%（負成長或持平）

# 取得 YoY 資料：從玩股網、Yahoo 股市或 GlobalWafers 官網手動整理
# URL：https://www.wantgoo.com/stock/5483/financial-statements/monthly-revenue

def classify_yoy(yoy):
    if yoy > 10:   return 'Strong_Beat'
    if yoy > 0:    return 'Mild_Beat'
    if yoy >= -10: return 'Mild_Miss'
    return 'Strong_Miss'

# 分組
beat_results = [r for r in all_results if r['yoy'] > 0]
miss_results = [r for r in all_results if r['yoy'] <= 0]

# 分別跑 BMP t-test
beat_t_r, beat_p_r, beat_s_r, beat_m_r, beat_CARs_r = bmp_t(0, 15, beat_results)
miss_t_r, miss_p_r, miss_s_r, miss_m_r, miss_CARs_r = bmp_t(0, 15, miss_results)

# 組間差異（Welch's t-test，不假設等方差）
def diff_t_test(CARs_a, CARs_b):
    t_stat, p_val = stats.ttest_ind(CARs_a, CARs_b, equal_var=False)
    diff = np.mean(CARs_a) - np.mean(CARs_b)
    sig = '***' if p_val<.001 else '**' if p_val<.01 else '*' if p_val<.05 else 'n.s.'
    return t_stat, p_val, diff, sig

t_diff, p_diff, diff, sig_diff = diff_t_test(beat_CARs_r, miss_CARs_r)
```

---

## 四、中美晶 5483 實際分析結果（2023/01~2026/06）

### 4.1 全樣本橫截面（N=42）

| 區間 | CAAR | BMP t | Patell Z | 結論 |
|---|---|---|---|---|
| 洩漏期 CAR(−15,−1) | −1.29% | −0.98 (n.s.) | −1.13 (n.s.) | 不顯著 |
| 反應期 CAR(0,+15) | +0.31% | +0.23 (n.s.) | −0.04 (n.s.) | 不顯著 |
| 整體 CAR(−15,+15) | −0.99% | −0.46 (n.s.) | — | 不顯著 |
| **單日** t=−5 | AAR=−0.655% | −2.10 (*) | — | **唯一顯著** |

**結論：全樣本支持市場半強式效率假說，無系統性異常報酬。**

### 4.2 分組分析（Beat vs Miss）

| 分組 | N | CAAR(−15,−1) | 統計 | CAAR(0,+15) | 統計 |
|---|---|---|---|---|---|
| **Beat（YoY>0%）** | 18 | **−3.87%** | **t=−2.23 (*) Z=−2.54 (*)** | +2.49% | n.s. |
| Miss（YoY≤0%） | 24 | +0.64% | n.s. | −1.34% | n.s. |
| **組間差異** | — | **Δ=−4.52%** | **Welch t=−1.79 (p=0.08)** | Δ=+3.83% | p=0.16 |

**核心發現：Beat 組在事件前 15 天有顯著負異常報酬（被錯殺），是識別進場時機的關鍵訊號。**

---

## 五、買進時機判斷邏輯

```python
def buy_signal(Z_leakage, Z_reaction, CAR_leakage, CAR_reaction):
    SIG = 1.96  # p < 0.05
    l_sig = abs(Z_leakage)  > SIG
    r_sig = abs(Z_reaction) > SIG

    if CAR_leakage > 0 and l_sig and not r_sig:
        return "AVOID：事件前漲完，不追"
    elif CAR_leakage <= 0 and CAR_reaction > 0 and r_sig:
        return "BUY_AFTER：事件後進場"
    elif CAR_leakage < 0 and CAR_reaction > 0 and r_sig:
        return "STRONG_BUY_AFTER：事件前錯殺，事件後最佳"
    elif CAR_leakage > 0 and CAR_reaction > 0 and r_sig:
        return "CAUTION：前後皆漲，追高風險"
    else:
        return "NO_SIGNAL：無顯著訊號"
```

---

## 六、下次分析新股票的完整 Checklist

```
□ 確認股票代號格式
    上市：{代號}.TW（如 2330.TW）
    上櫃：{代號}.TWO（如 5483.TWO）

□ 確認需要多久的資料
    最早事件日往前推 55 交易日 + 緩衝 = 約從事件前 4 個月起抓

□ 取得月營收資料（YoY）
    玩股網：https://www.wantgoo.com/stock/{代號}/financial-statements/monthly-revenue
    Yahoo 股市：https://tw.stock.yahoo.com/quote/{代號}/revenue

□ 建立事件日清單（每月10日/次一交易日）
□ 對每個事件跑 run_event_study()
□ 過濾 None（資料不足的事件）
□ 全樣本橫截面：bmp_t() + patell_z()
□ 分組：按 YoY > 0 vs ≤ 0 分成 Beat/Miss
□ 分組各自跑 bmp_t() + patell_z()
□ 組間差異：diff_t_test()（Welch's t-test）
□ 輸出：CAAR 曲線圖、箱型圖、YoY vs CAR 散佈圖
```

---

## 七、AI 提示詞（Perplexity / Gemini 可直接使用）

### 單次事件分析

```
請閱讀規格書：https://raw.githubusercontent.com/whocare-lab/stock/main/event_study_zscore_v2.md

對股票 [代號] 的月營收公布日 [YYYY-MM-DD] 執行事件研究法分析。
輸出：
1. 估計期 OLS 市場模型：α, β, σ_ε, R²
2. 洩漏期 CAR(−15,−1) 與 Z-Score（顯著性）
3. 反應期 CAR(0,+15) 與 Z-Score
4. 整體 CAR(−15,+15) 與 Z-Score
5. 買進建議（AVOID/BUY_AFTER/STRONG_BUY_AFTER/CAUTION/NO_SIGNAL）
請以繁體中文輸出，並解釋每個數字的意涵。
```

### 分組分析（N≥30 事件）

```
請閱讀分析手冊：https://raw.githubusercontent.com/whocare-lab/stock/main/analysis_playbook.md

對股票 [代號] 執行完整橫截面事件研究法：
1. 取得 2023~今 所有月營收公布日（每月 10 日/次一交易日）
2. 下載 [代號] 與 ^TWII 的歷史日報酬率
3. 對每個事件跑 OLS 市場模型 + AR 計算
4. 全樣本橫截面：CAAR + BMP t-test + Patell Z
5. 分組（Beat: YoY>0% vs Miss: YoY≤0%）各別 CAAR 與統計檢定
6. 組間差異 Welch t-test
輸出圖表：CAAR 曲線、箱型圖、YoY vs CAR_r 散佈圖。
```

### Hermes Agent 指令（Telegram）

```
請從 GitHub 讀取分析手冊：
https://raw.githubusercontent.com/whocare-lab/stock/main/analysis_playbook.md

對 [股票代號] 執行分組事件研究法分析：
- 事件範圍：最近 36 個月的月營收公布日
- 分組依據：YoY 年增率正負
- 輸出：Beat 組與 Miss 組的 CAAR 與 t-test 結果
- 最後給出買進訊號建議
```

---

## 八、常見錯誤與解決方式

| 錯誤訊息 | 原因 | 解法 |
|---|---|---|
| `TypeError: unsupported format string passed to Series` | `yfinance` 回傳 Multi-Index DataFrame | 在 `.pct_change()` 前加 `.squeeze()` |
| `possibly delisted; no timezone found` | 股票代號錯誤 | 上市用 `.TW`，上櫃用 `.TWO` |
| `IndexError: index 0 is out of bounds` | 資料期間太短 | 往前多拉 3 個月的資料 |
| EP 與 EW 重疊 | 估計期設定錯誤 | EP 必須是 `t=-55~-16`，EW 是 `t=-15~+15` |
| Z-Score 永遠不顯著 | 樣本數太少或 β 太高 | N ≥ 30 事件；β 高表示 σ_ε 大，門檻高是正常的 |

---

## 九、資料來源與參考文獻

- **規格書**：https://github.com/whocare-lab/stock/blob/main/event_study_zscore_v2.md
- **玩股網月營收**：https://www.wantgoo.com/stock/5483/financial-statements/monthly-revenue
- **Yahoo 股市**：https://tw.stock.yahoo.com/quote/5483.TWO/revenue
- **GlobalWafers 官網**：https://www.sas-globalwafers.com/en/investor/financial-information_en/

### 學術引用
- Ball, R., & Brown, P. (1968). An empirical evaluation of accounting income numbers. *Journal of Accounting Research*, 6(2), 159-178.
- Fama, E. F., Fisher, L., Jensen, M. C., & Roll, R. (1969). The adjustment of stock prices to new information. *International Economic Review*, 10(1), 1-21.
- MacKinlay, A. C. (1997). Event studies in economics and finance. *Journal of Economic Literature*, 35(1), 13-39.
- Patell, J. M. (1976). Corporate forecasts of earnings per share and stock price behavior. *Journal of Accounting Research*, 14(2), 246-276.
- Boehmer, E., Musumeci, J., & Poulsen, A. B. (1991). Event-study methodology under conditions of event-induced variance. *Journal of Financial Economics*, 30(2), 253-272. （BMP t-test 來源）

---

*本手冊由石頭哥（iiStone）使用 Perplexity Computer + Kimi AI 協作整理，2026-07-03*  
*GitHub：https://github.com/whocare-lab/stock*
