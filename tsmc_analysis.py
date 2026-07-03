"""
台積電 (2330.TW) 月營收事件研究分析
規格書 v2.0：EP t=-55~-16 (40天), EW t=-15~+15 (30天)
季節分組：旺季 Q2+Q3 (4~9月) vs 淡季 Q4+Q1 (1~3月+10~12月)
三策略：A(t=-10→t=0), B(t=0→t=+10), G(t=-10→t=+10)
輸出：tsmc_result.txt（純文字數字，供 Hermes agent 回傳）
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
import yfinance as yf
from scipy import stats
import sys, os

out_lines = []
def p(*args):
    line = " ".join(str(a) for a in args)
    print(line)
    out_lines.append(line)

p("📥 下載台積電 & 加權指數...")
sr_raw = yf.download("2330.TW", start="2022-06-01", end="2026-07-05", progress=False, auto_adjust=True)
tr_raw = yf.download("^TWII",   start="2022-06-01", end="2026-07-05", progress=False, auto_adjust=True)

stock_close = sr_raw['Close'].squeeze()
index_close = tr_raw['Close'].squeeze()
sr = stock_close.pct_change().dropna()
tr = index_close.pct_change().dropna()
td = pd.DatetimeIndex(sorted(tr.index))
p(f"交易日數: {len(td)}, 台積電資料: {len(sr)}")

def get_ann(y, m):
    t  = pd.Timestamp(f"{y}-{m:02d}-10")
    me = pd.Timestamp(f"{y}-{m:02d}-01") + pd.offsets.MonthEnd(0)
    c  = td[(td >= t) & (td <= me)]
    return c[0] if len(c) else None

events = []
for y in [2023, 2024, 2025, 2026]:
    months = range(1,13) if y < 2026 else range(1,7)
    for m in months:
        d = get_ann(y, m)
        if d is not None:
            season = 'peak' if m in [4,5,6,7,8,9] else 'off'
            events.append({'date':d,'year':y,'month':m,'season':season})

events_df = pd.DataFrame(events)
p(f"事件數 N={len(events_df)}, 旺季={sum(events_df.season=='peak')}, 淡季={sum(events_df.season=='off')}")
p("=== 事件日列表 ===")
for _, r in events_df.iterrows():
    p(f"  {r['date'].strftime('%Y-%m-%d')} M{r['month']:02d} [{r['season']}]")

def run_event(ev_date):
    idx = td.searchsorted(ev_date)
    if idx >= len(td): return None
    ep_s, ep_e = idx-55, idx-16
    if ep_s < 0 or ep_e >= len(td): return None
    ep_dates = td[ep_s:ep_e+1]
    ep_sr = sr.reindex(ep_dates).dropna()
    ep_tr = tr.reindex(ep_dates).dropna()
    common = ep_sr.index.intersection(ep_tr.index)
    if len(common) < 20: return None
    slope, intercept, r, p_, se = stats.linregress(ep_tr.loc[common].values, ep_sr.loc[common].values)
    ars = {}
    for t_off in range(-15, 16):
        i = idx + t_off
        if 0 <= i < len(td):
            d = td[i]; a = sr.get(d, np.nan); mk = tr.get(d, np.nan)
            ars[t_off] = (a-(intercept+slope*mk)) if not(np.isnan(a) or np.isnan(mk)) else np.nan
    return {'ar':ars,'beta':slope,'r2':r**2}

results = []
for _, row in events_df.iterrows():
    res = run_event(row['date'])
    if res:
        res['season']=row['season']; res['month']=row['month']
        res['year']=row['year'];     res['ev_date']=row['date']
        results.append(res)
p(f"有效事件數: {len(results)}")
p(f"平均 beta={np.mean([r['beta'] for r in results]):.4f}, 平均 R2={np.mean([r['r2'] for r in results]):.4f}")

t_range = list(range(-15,16))
ar_rows = []
for res in results:
    row_data = {'ev_date':res['ev_date'],'season':res['season']}
    for t in t_range: row_data[t] = res['ar'].get(t, np.nan)
    ar_rows.append(row_data)
ar_df = pd.DataFrame(ar_rows).set_index('ev_date')
ar_num = ar_df[t_range].astype(float)
season_s = ar_df['season']
peak_mask = (season_s=='peak').values
off_mask  = (season_s=='off').values

def caar_report(mat, label):
    n = len(mat)
    windows = {'leak(-15,-1)':list(range(-15,0)),'event(0)':[0],'react(+1,+15)':list(range(1,16))}
    p(f"--- {label} n={n} ---")
    for wn, tidx in windows.items():
        car_v = mat[tidx].sum(axis=1).dropna()
        mean = car_v.mean(); se = car_v.std()/np.sqrt(len(car_v)) if len(car_v)>1 else np.nan
        t_ = mean/se if se and se>0 else np.nan
        pv = 2*(1-stats.t.cdf(abs(t_),df=len(car_v)-1)) if not np.isnan(t_) else np.nan
        sig='***' if pv<0.01 else('**' if pv<0.05 else('*' if pv<0.10 else 'ns'))
        p(f"  {wn}: CAAR={mean*100:+.3f}% t={t_:+.3f} p={pv:.4f} {sig}")

p("=== CAAR 分析 ===")
caar_report(ar_num, "全樣本(N=42)")
caar_report(ar_num[peak_mask], "旺季Q2+Q3")
caar_report(ar_num[off_mask],  "淡季Q4+Q1")

p("=== 策略勝率 ===")
def strat_wr(t_buy, t_sell, label, sf=None):
    rets=[]
    for res in results:
        if sf and res['season']!=sf: continue
        idx=td.searchsorted(res['ev_date']); i_b,i_s=idx+t_buy,idx+t_sell
        if i_b<0 or i_s>=len(td) or i_b>=i_s: continue
        pb=stock_close.get(td[i_b],np.nan); ps=stock_close.get(td[i_s],np.nan)
        if np.isnan(pb) or np.isnan(ps) or pb==0: continue
        rets.append((ps-pb)/pb)
    if not rets: return
    rets=np.array(rets); wins=(rets>0).sum(); n=len(rets); mean=rets.mean()
    se=rets.std()/np.sqrt(n) if n>1 else np.nan
    t_=mean/se if se and se>0 else np.nan
    pv=2*(1-stats.t.cdf(abs(t_),df=n-1)) if not np.isnan(t_) else np.nan
    sig='***' if pv<0.01 else('**' if pv<0.05 else('*' if pv<0.10 else 'ns'))
    p(f"  {label}: n={n} 勝率={wins/n*100:.1f}%({wins}漲/{n-wins}跌) 均值={mean*100:+.3f}% t={t_:+.3f} p={pv:.4f} {sig}")

for sf,sl in [('peak','旺季'),('off','淡季')]:
    p(f"-- {sl} --")
    strat_wr(-10, 0,  f"{sl} 策略A(t=-10→0)", sf)
    strat_wr(  0,10,  f"{sl} 策略B(t=0→+10)", sf)
    strat_wr(-10,10,  f"{sl} 策略G(t=-10→+10)",sf)

p("=== 完成 ✅ ===")

# 儲存結果
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tsmc_result.txt")
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))
print(f"結果已儲存：{out_path}")
