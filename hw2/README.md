# HW2：台灣本島的地形與降雨

資料分析與視覺化課程作業二，由作業一（地形高度分佈）延伸而來。在原本的地形圖上加入 **每月降雨量**，並用 **D3.js v7** 做成可互動的動態網頁，讓讀者自己操作後看出「山脈怎麼決定雨落在哪一邊」。

畫面框架是 Vue 3（Composition API + `<script setup>`），繪圖、動畫與互動由 D3 負責。

規劃見 [`PLAN.md`](PLAN.md)，兩張圖的做法見 [`CHARTS.md`](CHARTS.md)。

## 預覽

```
cd hw2
npm install
npm run dev      # 開發模式 http://localhost:5173/
npm run build    # 產出 dist/（相對路徑，可直接部署到靜態空間）
```

## 內容與互動

- **View 1 地形與降雨地圖**
  - 「地形／降雨」圖層切換
  - 月份滑桿與播放鍵，自動輪播 12 個月
  - 游標移到地圖上，顯示該地點的經緯度、海拔、當月降雨量
- **View 2 各高程帶統計**
  - 地形圖層：各高程帶佔本島面積的百分比
  - 降雨圖層：各高程帶的當月平均降雨量，換月份時長條平滑伸縮
  - 游標移到長條上，地圖只亮出那個高度範圍；游標在地圖上時，對應的長條加框

## 專案結構

```
src/
  main.js, App.vue             # 入口
  constants.js                 # 高程與降雨的門檻、色階、圖例文字
  composables/
    useJson.js                 # 資料載入（loading / error 狀態、請求快取）
    useMapState.js             # 兩張圖共用的狀態（圖層、月份、播放、選中的高程帶）
  components/
    GuidePanel.vue
    HypsometricMap.vue         # View 1
    ElevationHistogram.vue     # View 2
public/data/                   # 前處理產出的 JSON
scripts/                       # Python 前處理（輸出到 public/data/）
```

## 資料來源

- **地形**：Copernicus GLO-30 DEM（30 m 解析度），AWS Open Data Registry `s3://copernicus-dem-30m`（免金鑰）。本島邊界由高程資料自身推導（陸地遮罩 + 連通元件分析取最大陸塊），未使用外部邊界檔。
- **降雨**：CHIRPS v3.0 逐月降雨量（Climate Hazards Center, UC Santa Barbara），**2025 年** 1–12 月，0.05°（約 5 km）解析度，衛星估計與測站觀測融合，免註冊。

降雨量是 2025 年單一年份的實際月雨量，不是長期平均；2025 年 7 月破紀錄多雨，數值明顯高於常年。

## 重新產生資料

```
python scripts/fetch_dem.py      # 下載 DEM 圖磚到 data/raw/
python scripts/process_dem.py    # → taiwan-dem-grid.json、elevation-bands.json、summary.json
python scripts/process_rain.py   # → rain-grid.json、rain-by-band.json
```

`process_rain.py` 只會從 CHIRPS 的全球月雨量檔讀取台灣範圍（不必下載整個檔案），並重採樣到與 DEM 完全相同的 200×260 網格，所以每一格同時有海拔與 12 個月的雨量。
