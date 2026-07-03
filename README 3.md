# 石頭哥個案研究模擬 v1.2

> **網站：** https://whocare-lab.github.io/stock/  
> **作者：** 石頭哥｜27年科技業主管．元智大學 DBA博士生  
> **Threads：** https://www.threads.com/@iistone_1

---

## 這是什麼？

這是一個**論文個案研究模擬工具**，將石頭哥在 Python 中開發的股票分析模組（`institutional_investors.py` + `main_event_study.py`），轉化為可直接貼到 ChatGPT 的提示詞（Prompt）。

這份內容屬於元智大學 DBA 博士班課程延伸的知識性學習與程式驗證範例，主要用來理解事件研究法與籌碼分析邏輯，**無關於股票的真實投資建議**。

讓沒有 Python 環境的人，也能體驗學術級的籌碼分析與事件研究邏輯。

---

## 三大分析模組

| 分頁 | 功能說明 | 對應 Python 模組 |
|------|---------|-----------------|
| 🎯 **買點雷達** | 外資異常買超檢測、綜合籌碼快篩、逃命訊號 | `institutional_investors.py` |
| ⚔️ **同業對決** | 同業批次比較、相對強勢訊號 | `institutional_investors.py` + `group_analysis.py` |
| 📅 **事件獵殺** | 營收公佈事件研究、資訊洩漏檢測、高股息 ETF 選擇 | `main_event_study.py` + `scenarios.py` |

---

## 8 組提示詞一覽

### 🎯 買點雷達（3 組）
1. **外資有沒有偷偷買？** — 三段式固定基期法，抓被掩蓋的異常買超
2. **這檔現在能進場嗎？** — 綜合籌碼快篩：外資 + 投信 + 股價位置
3. **外資是不是在倒貨？** — 反向檢測：抓異常大賣的逃命訊號

### ⚔️ 同業對決（2 組）
4. **封測三雄誰被外資買最多？** — 2449 vs 3711 vs 6239 同業批次分析
5. **同產業誰有異常買點？** — 同業相對 z-score，找出「單獨被買」的訊號

### 📅 事件獵殺（3 組）
6. **營收公佈後能不能買？** — 事件研究法：前窗 vs 後窗 CAR 比較
7. **有沒有人提前知道營收？** — 資訊洩漏檢測：公佈前異常買超
8. **高股息 ETF 現在買哪一檔？** — 0056、00878、00919、00929 四檔比較

---

## 使用方式

1. 打開網站：https://whocare-lab.github.io/stock/
2. 選擇分頁（買點雷達 / 同業對決 / 事件獵殺）
3. 點擊「複製」按鈕
4. 貼到 ChatGPT
5. 把 `【2449】` 換成你要的股票代號
6. 直接看結論「事件前買 / 事件後買 / no signal」

> 提醒：上述提示詞屬於 DBA 課程學習版，適合做模型驗證與研究討論，不是投資指引。

---

## ⚠️ 投資風險聲明

- 本頁面所有提示詞產生的分析結果 **僅供參考，不構成投資建議**
- ChatGPT 資料可能過期、錯誤或缺少即時股價
- 「異常檢測」是統計方法，**不是預言**
- 歷史異常不代表未來會漲，**虧損自負**
- 下單前請務必確認即時行情，並諮詢專業投資顧問

---

## 技術對照表

| 網頁提示詞 | Python 檔案 | 函數/方法 | 資料來源 |
|-----------|------------|----------|---------|
| 外資有沒有偷偷買？ | `institutional_investors.py` | `three_segment_zscore()` | T86 API |
| 這檔現在能進場嗎？ | `institutional_investors.py` + `event_study_core.py` | 外資 10 日均 + 投信 10 日均 + 股價均線 | T86 + Yahoo |
| 外資是不是在倒貨？ | `institutional_investors.py` | `three_segment_zscore()` 反向 | T86 API |
| 封測三雄誰被買最多？ | `institutional_investors.py` + `group_analysis.py` | 同業批次分析 + `cross_sectional_zscore()` | T86 API |
| 同業誰有異常買點？ | `institutional_investors.py` | `cross_sectional_zscore()` | T86 API |
| 營收公佈後能不能買？ | `main_event_study.py` + `scenarios.py` | `scenario_1_post_announcement_strategy()` | MOPS + Yahoo |
| 有沒有人提前知道營收？ | `main_event_study.py` + `scenarios.py` | `scenario_2_information_leakage()` | MOPS + Yahoo |
| 高股息 ETF 買哪一檔？ | `institutional_investors.py` (ETF) | 外資買超 + 殖利率 + 52 週高點 | T86 + Yahoo |

---

## 關於作者 ✍️

**石頭哥**｜27年科技業主管．教育部部定大專院校講師．職涯專欄作家．元智大學 DBA 博士生

- **研究學習：** 生態系競爭策略｜社會資本｜組織變革
- **建構：** AI × 文獻探討 × 原子句耦合框架

> 相信每個人心中都有一道光；點亮它，人自然會前進。這也是撰寫中的《擴容》這本書的核心——帶你把職場傷痕煉就成領導力。

📍 **方格子寫作平台：** https://vocus.cc/user/@iiStone  
📙 **半本真人故事書：** https://whocare-lab.github.io/half_book_true_story/half_book_true_story.html  
💊 **姑爺爺的快樂膠囊：** https://www.threads.com/@iistone_1  
📮 **我想說說話：** s1149404@mail.yzu.edu.tw

---

© 2026 石頭哥個案研究模擬 v1.2 | 元智大學 DBA 博士生
