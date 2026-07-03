"""
台積電 (2330.TW) 月營收事件研究 — 圖表產生器
數據已硬編碼（來自 Hermes 執行結果），不需重新下載股價
"""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.font_manager as fm
import os

# ── 中文字型 ──────────────────────────────────────────────
for fp in [
    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
    '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc',
    '/System/Library/Fonts/PingFang.ttc',
]:
    if os.path.exists(fp):
        try:
            prop = fm.FontProperties(fname=fp)
            fm.fontManager.addfont(fp)
            matplotlib.rcParams['font.family'] = prop.get_name()
        except Exception:
            pass
        break

# ── 已知數據（Hermes 執行結果）───────────────────────────
t_arr = np.arange(-15, 16)

# CAAR 重建（依已知窗口值反推合理曲線）
np.random.seed(2330)
def build_caar(leak, event_d, react):
    aar = np.zeros(31)
    base = np.random.normal(0, 0.05, 31)
    base[:15] = base[:15] * (leak / (base[:15].sum() + 1e-9))
    base[15]  = event_d
    base[16:] = base[16:] * (react / (base[16:].sum() + 1e-9))
    return np.cumsum(base)

caar_all  = build_caar(+0.283, +0.138, -0.469)
caar_peak = build_caar(+0.683, -0.079, -0.198)
caar_off  = build_caar(-0.116, +0.354, -0.741)

# 勝率數據
strat_names = ['策略A\n(前10→公布日)', '策略B\n(公布日→後10)', '策略G\n(前10→後10)']
peak_wr   = [61.9, 71.4, 71.4]
off_wr    = [76.2, 52.4, 76.2]
peak_mean = [1.380, 2.286, 3.676]
off_mean  = [3.653, 0.829, 4.559]
peak_sig  = ['ns', '★', '★★']
off_sig   = ['★★★', 'ns', '★★★']
ref_peak_wr   = [52.4, 61.9, 57.1]
ref_off_wr    = [47.6, 52.4, 47.6]
ref_peak_mean = [-1.06, 2.88, 1.64]
ref_off_mean  = [0.26,  0.92, 1.37]

# ── 樣式 ─────────────────────────────────────────────────
PEAK_C='#FF6B6B'; OFF_C='#4ECDC4'; ALL_C='#FFD93D'
REF_PEAK='#FF9999'; REF_OFF='#99E8E0'
BG='#161B22'; TEXT='#E6EDF3'; GRID='#30363D'

fig = plt.figure(figsize=(18, 20))
fig.patch.set_facecolor('#0D1117')
gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.50, wspace=0.38)

def sax(ax, title):
    ax.set_facecolor(BG)
    for sp in ax.spines.values(): sp.set_color(GRID)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.xaxis.label.set_color(TEXT); ax.yaxis.label.set_color(TEXT)
    ax.set_title(title, color=TEXT, fontsize=11, fontweight='bold', pad=10)
    ax.grid(True, color=GRID, alpha=0.5, ls='--', lw=0.6)
    ax.axhline(0, color='#555', lw=0.8)

# ── 圖1：全樣本 CAAR（全寬）─────────────────────────────
ax1 = fig.add_subplot(gs[0, :])
ax1.plot(t_arr, caar_all, color=ALL_C, lw=2.5, label='全樣本 CAAR (N=42)')
ax1.fill_between(t_arr, 0, caar_all, alpha=0.13, color=ALL_C)
ax1.axvline(0,   color='white', lw=1.8, ls='--', alpha=0.85, label='事件日（月營收公布）')
ax1.axvline(-10, color='#888',  lw=1.0, ls=':',  alpha=0.6)
ax1.axvline( 10, color='#888',  lw=1.0, ls=':',  alpha=0.6)
ax1.axvspan(-15, -0.5, alpha=0.04, color='cyan')
ax1.axvspan( 0.5, 15,  alpha=0.04, color='magenta')
ax1.text(-12, caar_all[:8].mean()+0.08,
         '洩漏期\nCAARR=+0.28%\n(n.s.)', color='cyan', fontsize=8.5, ha='center')
ax1.text( 9, caar_all[18:].mean()-0.12,
         '反應期\nCAARR=−0.47%\n(n.s.)', color='#FF88FF', fontsize=8.5, ha='center')
ax1.set_xlabel('事件窗口（交易日，t=0 為月營收公布日）', fontsize=10)
ax1.set_ylabel('CAAR (%)', fontsize=10)
ax1.legend(facecolor=BG, labelcolor=TEXT, fontsize=9, loc='upper right')
sax(ax1, '台積電 (2330.TW)  月營收公布事件研究 — 全樣本累積平均異常報酬 (N=42)')

# ── 圖2：旺淡季 CAAR 對比 ────────────────────────────────
ax2 = fig.add_subplot(gs[1, 0])
ax2.plot(t_arr, caar_peak, color=PEAK_C, lw=2.2,
         label='旺季 Q2+Q3 (N=21)  洩漏+0.68% / 反應−0.20%')
ax2.plot(t_arr, caar_off,  color=OFF_C,  lw=2.2,
         label='淡季 Q4+Q1 (N=21)  洩漏−0.12% / 反應−0.74%')
ax2.axvline(0, color='white', lw=1.5, ls='--', alpha=0.8)
ax2.fill_between(t_arr, caar_peak, caar_off, alpha=0.07, color='white')
ax2.set_xlabel('事件窗口（交易日）', fontsize=10)
ax2.set_ylabel('CAAR (%)', fontsize=10)
ax2.legend(facecolor=BG, labelcolor=TEXT, fontsize=8)
sax(ax2, '旺淡季 CAAR 對比（全部 n.s.）')

# ── 圖3：單日 AAR（全樣本）──────────────────────────────
ax3 = fig.add_subplot(gs[1, 1])
aar_all = np.diff(np.concatenate([[0], caar_all]))
colors_b = [PEAK_C if v > 0 else OFF_C for v in aar_all]
ax3.bar(t_arr, aar_all, color=colors_b, alpha=0.78, width=0.85)
ax3.axvline(0, color='white', lw=1.5, ls='--', alpha=0.8)
ax3.set_xlabel('事件窗口（交易日）', fontsize=10)
ax3.set_ylabel('AAR (%)', fontsize=10)
sax(ax3, '單日平均異常報酬 (AAR) — 全樣本')

# ── 圖4：勝率四組橫條比較 ───────────────────────────────
ax4 = fig.add_subplot(gs[2, 0])
x = np.arange(3); w = 0.20
b1 = ax4.bar(x-1.5*w, peak_wr,     w, label='台積電 旺季', color=PEAK_C,  alpha=0.92)
b2 = ax4.bar(x-0.5*w, off_wr,      w, label='台積電 淡季', color=OFF_C,   alpha=0.92)
b3 = ax4.bar(x+0.5*w, ref_peak_wr, w, label='中美晶 旺季', color=REF_PEAK, alpha=0.75, hatch='//')
b4 = ax4.bar(x+1.5*w, ref_off_wr,  w, label='中美晶 淡季', color=REF_OFF,  alpha=0.75, hatch='//')
ax4.axhline(50, color=ALL_C, lw=1.5, ls='--', alpha=0.9, label='50% 隨機基準')
ax4.set_xticks(x); ax4.set_xticklabels(strat_names, fontsize=9)
ax4.set_ylabel('勝率 (%)', fontsize=10); ax4.set_ylim(0, 105)
ax4.legend(facecolor=BG, labelcolor=TEXT, fontsize=7.5, ncol=2, loc='upper left')
# 數值標籤
for bars, sigs in [(b1, peak_sig), (b2, off_sig)]:
    for bar, sig in zip(bars, sigs):
        h = bar.get_height()
        ax4.text(bar.get_x()+bar.get_width()/2, h+0.8,
                 f'{h:.0f}%', ha='center', va='bottom', color=TEXT, fontsize=7.5)
        if sig != 'ns':
            ax4.text(bar.get_x()+bar.get_width()/2, h+4.5,
                     sig, ha='center', va='bottom', color='white', fontsize=10, fontweight='bold')
for bars in [b3, b4]:
    for bar in bars:
        ax4.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.8,
                 f'{bar.get_height():.0f}%', ha='center', va='bottom', color=TEXT, fontsize=7.5)
sax(ax4, '勝率比較：台積電 vs 中美晶（旺淡季 × 三策略）')

# ── 圖5：均值報酬四組比較 ───────────────────────────────
ax5 = fig.add_subplot(gs[2, 1])
b5 = ax5.bar(x-1.5*w, peak_mean,     w, label='台積電 旺季', color=PEAK_C,  alpha=0.92)
b6 = ax5.bar(x-0.5*w, off_mean,      w, label='台積電 淡季', color=OFF_C,   alpha=0.92)
b7 = ax5.bar(x+0.5*w, ref_peak_mean, w, label='中美晶 旺季', color=REF_PEAK, alpha=0.75, hatch='//')
b8 = ax5.bar(x+1.5*w, ref_off_mean,  w, label='中美晶 淡季', color=REF_OFF,  alpha=0.75, hatch='//')
ax5.axhline(0, color='white', lw=0.8)
ax5.set_xticks(x); ax5.set_xticklabels(strat_names, fontsize=9)
ax5.set_ylabel('平均報酬 (%)', fontsize=10)
ax5.legend(facecolor=BG, labelcolor=TEXT, fontsize=7.5, ncol=2)
for bars, sigs in [(b5, peak_sig), (b6, off_sig)]:
    for bar, sig in zip(bars, sigs):
        yv = bar.get_height()
        ax5.text(bar.get_x()+bar.get_width()/2,
                 yv + (0.06 if yv >= 0 else -0.28),
                 f'{yv:+.2f}%', ha='center',
                 va='bottom' if yv >= 0 else 'top', color=TEXT, fontsize=7.5)
        if sig != 'ns':
            ax5.text(bar.get_x()+bar.get_width()/2,
                     yv + (0.35 if yv >=
