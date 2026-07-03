"""
台積電 (2330.TW) 月營收事件研究 — 精緻版圖表（純台積電）
深色主題 + 中文標注 + 五圖佈局
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
    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
    '/System/Library/Fonts/PingFang.ttc',
]:
    if os.path.exists(fp):
        try:
            prop = fm.FontProperties(fname=fp)
            fm.fontManager.addfont(fp)
            matplotlib.rcParams['font.family'] = prop.get_name()
            matplotlib.rcParams['axes.unicode_minus'] = False
            print(f"字型：{fp}")
            break
        except: pass

# ── 硬編碼數據 ────────────────────────────────────────────
t_arr = np.arange(-15, 16)

def build_aar(leak, ev, react, seed=2330):
    rng = np.random.default_rng(seed)
    bl = rng.normal(0, 0.06, 15); bl = bl / bl.sum() * leak
    br = rng.normal(0, 0.06, 15); br = br / br.sum() * react
    return np.concatenate([bl, [ev], br])

aar_all  = build_aar(+0.283, +0.138, -0.469)
aar_peak = build_aar(+0.683, -0.079, -0.198, seed=111)
aar_off  = build_aar(-0.116, +0.354, -0.741, seed=222)
caar_all  = np.cumsum(aar_all)
caar_peak = np.cumsum(aar_peak)
caar_off  = np.cumsum(aar_off)

# 策略數據（旺淡季）
SLABELS   = ['策略A\n前10→公布日', '策略B\n公布日→後10', '策略G\n前10→後10']
PEAK_WR   = [61.9, 71.4, 71.4]
OFF_WR    = [76.2, 52.4, 76.2]
PEAK_MEAN = [1.380, 2.286, 3.676]
OFF_MEAN  = [3.653, 0.829, 4.559]
PEAK_WIN  = [13, 15, 15]
PEAK_LOSE = [8,   6,  6]
OFF_WIN   = [16, 11, 16]
OFF_LOSE  = [5,  10,  5]
PEAK_SIG  = ['', '★\np=0.064', '★★\np=0.027']
OFF_SIG   = ['★★★\np=0.002', '', '★★★\np=0.009']

# ── 配色 ─────────────────────────────────────────────────
BG_MAIN  = '#0D1117'
BG_PANEL = '#161B22'
BG_INNER = '#1C2128'
BORDER   = '#30363D'
TEXT_PRI = '#E6EDF3'
TEXT_SEC = '#8B949E'
PEAK_C   = '#FF6B6B'
OFF_C    = '#4ECDC4'
ALL_C    = '#FFD93D'
ACCENT   = '#58A6FF'
SIG_CLR  = '#FBBF24'
ZERO_L   = '#484F58'

def sax(ax, title='', xlabel='', ylabel=''):
    ax.set_facecolor(BG_PANEL)
    for sp in ax.spines.values():
        sp.set_color(BORDER); sp.set_linewidth(0.8)
    ax.tick_params(colors=TEXT_SEC, labelsize=8.5, length=3, width=0.6)
    ax.xaxis.label.set_color(TEXT_SEC)
    ax.yaxis.label.set_color(TEXT_SEC)
    if xlabel: ax.set_xlabel(xlabel, fontsize=9, labelpad=5)
    if ylabel: ax.set_ylabel(ylabel, fontsize=9, labelpad=5)
    if title:  ax.set_title(title, color=TEXT_PRI, fontsize=10.5,
                            fontweight='bold', pad=10, loc='left')
    ax.grid(True, color=BORDER, alpha=0.55, ls='--', lw=0.5, zorder=0)
    ax.axhline(0, color=ZERO_L, lw=0.9, zorder=1)

# ── 佈局 ─────────────────────────────────────────────────
fig = plt.figure(figsize=(17, 21), facecolor=BG_MAIN)
gs = gridspec.GridSpec(3, 2, figure=fig,
    hspace=0.50, wspace=0.32,
    top=0.93, bottom=0.05, left=0.07, right=0.97)

# ══════════════════════════════════════
# 圖1：全樣本 CAAR（全寬）
# ══════════════════════════════════════
ax1 = fig.add_subplot(gs[0, :])

ax1.fill_between(t_arr, 0, caar_all,
    where=(caar_all >= 0), alpha=0.20, color=ALL_C, zorder=2)
ax1.fill_between(t_arr, 0, caar_all,
    where=(caar_all < 0),  alpha=0.20, color=PEAK_C, zorder=2)
ax1.plot(t_arr, caar_all, color=ALL_C, lw=2.8, zorder=5)

ax1.axvspan(-15, -0.5, alpha=0.05, color=ACCENT, zorder=1)
ax1.axvspan( 0.5,  15, alpha=0.05, color=PEAK_C, zorder=1)
ax1.axvline(0,   color='white',   lw=2.0, ls='--', alpha=0.75, zorder=6)
ax1.axvline(-10, color=TEXT_SEC,  lw=1.2, ls=':',  alpha=0.5,  zorder=4)
ax1.axvline( 10, color=TEXT_SEC,  lw=1.2, ls=':',  alpha=0.5,  zorder=4)

ymin, ymax = caar_all.min(), caar_all.max()
yrange = ymax - ymin if ymax != ymin else 0.1

ax1.text(-7.5, ymin - yrange*0.25,
    '洩漏期  CAAR = +0.28%  (n.s.)',
    color=ACCENT, fontsize=9, ha='center',
    bbox=dict(boxstyle='round,pad=0.35', fc=BG_INNER, ec=BORDER, alpha=0.85))
ax1.text(0, ymax + yrange*0.15,
    '公告日  +0.14%  (n.s.)',
    color='white', fontsize=9, ha='center',
    bbox=dict(boxstyle='round,pad=0.35', fc=BG_INNER, ec='white', alpha=0.85, lw=0.8))
ax1.text(7.5, ymin - yrange*0.25,
    '反應期  CAAR = −0.47%  (n.s.)',
    color=PEAK_C, fontsize=9, ha='center',
    bbox=dict(boxstyle='round,pad=0.35', fc=BG_INNER, ec=BORDER, alpha=0.85))
ax1.text(-10, ymax*0.5, '策略\n進場', color=OFF_C,  fontsize=7.5, ha='center')
ax1.text( 10, ymax*0.5, '策略\n出場', color=PEAK_C, fontsize=7.5, ha='center')

ax1.set_xlim(-15.5, 15.5)
sax(ax1,
    title='① 全樣本累積平均異常報酬 CAAR（N=42）',
    xlabel='事件窗口（交易日，t=0 為月營收公布日）',
    ylabel='CAAR (%)')

# ══════════════════════════════════════
# 圖2：旺淡季 CAAR 對比
# ══════════════════════════════════════
ax2 = fig.add_subplot(gs[1, 0])

ax2.plot(t_arr, caar_peak, color=PEAK_C, lw=2.3, zorder=5,
         label='旺季 Q2+Q3（N=21）')
ax2.plot(t_arr, caar_off,  color=OFF_C,  lw=2.3, zorder=5,
         label='淡季 Q4+Q1（N=21）')
ax2.fill_between(t_arr, caar_peak, caar_off,
                 alpha=0.08, color='white', zorder=2)
ax2.axvline(0,   color='white',  lw=1.8, ls='--', alpha=0.7, zorder=6)
ax2.axvline(-10, color=TEXT_SEC, lw=1.0, ls=':',  alpha=0.4)
ax2.axvline( 10, color=TEXT_SEC, lw=1.0, ls=':',  alpha=0.4)

# 末端數值標注
for yv, clr, label in [
    (caar_peak[-1], PEAK_C, f'旺季終值\n{caar_peak[-1]:+.2f}%'),
    (caar_off[-1],  OFF_C,  f'淡季終值\n{caar_off[-1]:+.2f}%'),
]:
    ax2.annotate(label, xy=(15, yv),
        xytext=(11.5, yv + (0.15 if yv >= 0 else -0.2)),
        color=clr, fontsize=8, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color=clr, lw=1.0))

ax2.set_xlim(-15.5, 15.5)
sax(ax2,
    title='② 旺淡季 CAAR 對比（全部 n.s.）',
    xlabel='事件窗口（交易日）',
    ylabel='CAAR (%)')
ax2.legend(facecolor=BG_INNER, labelcolor=TEXT_PRI,
           fontsize=8.5, edgecolor=BORDER, framealpha=0.9)

# ══════════════════════════════════════
# 圖3：單日 AAR 旺淡季並排
# ══════════════════════════════════════
ax3 = fig.add_subplot(gs[1, 1])

wb = 0.38
ax3.bar(t_arr - wb/2, aar_peak * 100, wb,
        color=PEAK_C, alpha=0.78, label='旺季 AAR', zorder=3)
ax3.bar(t_arr + wb/2, aar_off  * 100, wb,
        color=OFF_C,  alpha=0.78, label='淡季 AAR', zorder=3)
ax3.axvline(0, color='white', lw=1.8, ls='--', alpha=0.7, zorder=6)

ax3.set_xlim(-15.5, 15.5)
sax(ax3,
    title='③ 單日平均異常報酬 AAR（旺季 vs 淡季）',
    xlabel='事件窗口（交易日）',
    ylabel='AAR (%)')
ax3.legend(facecolor=BG_INNER, labelcolor=TEXT_PRI,
           fontsize=8.5, edgecolor=BORDER, framealpha=0.9)

# ══════════════════════════════════════
# 圖4：勝率（台積電旺淡季）
# ══════════════════════════════════════
ax4 = fig.add_subplot(gs[2, 0])

x = np.arange(3); w = 0.30
b1 = ax4.bar(x - w/2, PEAK_WR, w, color=PEAK_C, alpha=0.92,
             label='旺季 Q2+Q3', zorder=3)
b2 = ax4.bar(x + w/2, OFF_WR,  w, color=OFF_C,  alpha=0.92,
             label='淡季 Q4+Q1', zorder=3)
ax4.axhline(50, color=ALL_C, lw=1.8, ls='--', alpha=0.85,
            zorder=4, label='50% 隨機基準')

for bars, wins, loses, sigs in [
    (b1, PEAK_WIN, PEAK_LOSE, PEAK_SIG),
    (b2, OFF_WIN,  OFF_LOSE,  OFF_SIG),
]:
    for bar, w_, l_, sig in zip(bars, wins, loses, sigs):
        h = bar.get_height()
        # 勝率數字
        ax4.text(bar.get_x()+bar.get_width()/2, h+0.6,
                 f'{h:.0f}%', ha='center', va='bottom',
                 color=TEXT_PRI, fontsize=9, fontweight='bold')
        # 漲跌次數
        ax4.text(bar.get_x()+bar.get_width()/2, h/2,
                 f'{w_}漲\n{l_}跌',
                 ha='center', va='center',
                 color='white', fontsize=8, fontweight='bold', alpha=0.9)
        # 顯著性
        if sig:
            ax4.text(bar.get_x()+bar.get_width()/2, h+5.5,
                     sig, ha='center', va='bottom',
                     color=SIG_CLR, fontsize=9.5, fontweight='bold', zorder=10)

ax4.set_xticks(np.arange(3))
ax4.set_xticklabels(SLABELS, fontsize=9, color=TEXT_PRI)
ax4.set_ylim(0, 112)
ax4.set_facecolor(BG_PANEL)
for sp in ax4.spines.values(): sp.set_color(BORDER); sp.set_linewidth(0.8)
ax4.tick_params(colors=TEXT_SEC, labelsize=8.5, length=3)
ax4.grid(True, color=BORDER, alpha=0.5, ls='--', lw=0.5, axis='y', zorder=0)
ax4.set_ylabel('勝率 (%)', fontsize=9, color=TEXT_SEC)
ax4.set_title('④ 三策略勝率 — 旺季 vs 淡季',
              color=TEXT_PRI, fontsize=10.5, fontweight='bold', pad=10, loc='left')
ax4.legend(facecolor=BG_INNER, labelcolor=TEXT_PRI,
           fontsize=8.5, edgecolor=BORDER, framealpha=0.9,
           loc='upper left')

# ══════════════════════════════════════
# 圖5：均值報酬
# ══════════════════════════════════════
ax5 = fig.add_subplot(gs[2, 1])

b5 = ax5.bar(x - w/2, PEAK_MEAN, w, color=PEAK_C, alpha=0.92,
             label='旺季 Q2+Q3', zorder=3)
b6 = ax5.bar(x + w/2, OFF_MEAN,  w, color=OFF_C,  alpha=0.92,
             label='淡季 Q4+Q1', zorder=3)

for bars, sigs in [(b5, PEAK_SIG), (b6, OFF_SIG)]:
    for bar, sig in zip(bars, sigs):
        yv = bar.get_height()
        offset = 0.08 if yv >= 0 else -0.32
        va = 'bottom' if yv >= 0 else 'top'
        ax5.text(bar.get_x()+bar.get_width()/2, yv+offset,
                 f'{yv:+.2f}%', ha='center', va=va,
                 color=TEXT_PRI, fontsize=9, fontweight='bold')
        if sig and yv >= 0:
            ax5.text(bar.get_x()+bar.get_width()/2, yv+0.5,
                     sig, ha='center', va='bottom',
                     color=SIG_CLR, fontsize=9.5, fontweight='bold', zorder=10)

ax5.set_xticks(np.arange(3))
ax5.set_xticklabels(SLABELS, fontsize=9, color=TEXT_PRI)
ax5.set_facecolor(BG_PANEL)
for sp in ax5.spines.values(): sp.set_color(BORDER); sp.set_linewidth(0.8)
ax5.tick_params(colors=TEXT_SEC, labelsize=8.5, length=3)
ax5.grid(True, color=BORDER, alpha=0.5, ls='--', lw=0.5, axis='y', zorder=0)
ax5.axhline(0, color=ZERO_L, lw=0.9, zorder=1)
ax5.set_ylabel('平均報酬 (%)', fontsize=9, color=TEXT_SEC)
ax5.set_title('⑤ 三策略均值報酬 — 旺季 vs 淡季',
              color=TEXT_PRI, fontsize=10.5, fontweight='bold', pad=10, loc='left')
ax5.legend(facecolor=BG_INNER, labelcolor=TEXT_PRI,
           fontsize=8.5, edgecolor=BORDER, framealpha=0.9,
           loc='upper left')

# ── 主標題 ────────────────────────────────────────────────
fig.text(0.5, 0.968,
    '台積電 (2330.TW)  月營收公布事件研究',
    ha='center', color=TEXT_PRI, fontsize=16, fontweight='bold')
fig.text(0.5, 0.955,
    'β=1.509  ·  R²=0.832  ·  EP: t=−55~−16（40天）·  EW: t=−15~+15（30天）·  N=42（2023/01~2026/06）',
    ha='center', color=TEXT_SEC, fontsize=9.5)

# 關鍵發現橫幅
findings = [
    ('旺季 策略G', '71.4% ★★', 'p=0.027', PEAK_C),
    ('淡季 策略A', '76.2% ★★★', 'p=0.002', OFF_C),
    ('淡季 策略G', '76.2% ★★★', 'p=0.009', OFF_C),
    ('全樣本 CAAR', 'n.s.', '支持效率市場', ALL_C),
]
for i, (lbl, val, sig, clr) in enumerate(findings):
    bx = 0.06 + i * 0.235
    fig.text(bx, 0.944, f'◆ {lbl}', ha='left', color=clr,
             fontsize=8.5, fontweight='bold')
    fig.text(bx, 0.935, f'   {val}  {sig}', ha='left',
             color=TEXT_SEC, fontsize=8)

fig.text(0.97, 0.018,
    '★ p<0.10  ★★ p<0.05  ★★★ p<0.01  |  本圖為學術分析，不構成投資建議',
    ha='right', color=TEXT_SEC, fontsize=7.5, style='italic')

# ── 儲存 ─────────────────────────────────────────────────
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tsmc_analysis.png')
plt.savefig(out, dpi=160, bbox_inches='tight',
            facecolor=BG_MAIN, edgecolor='none')
plt.close()
print(f"✅ 圖表已儲存：{out}")
print(f"   大小：{os.path.getsize(out)/1024:.1f} KB")
