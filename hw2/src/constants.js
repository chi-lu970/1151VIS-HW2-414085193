// 共用設定：兩個視圖都會用到的分層門檻與色階，確保視覺一致。
import { scaleThreshold, schemeYlGnBu } from "d3";

export const ELEVATION_THRESHOLDS = [0, 100, 500, 1000, 1500, 2000, 2500, 3000, 3500];

// 傳統分層設色地形圖配色：低地綠 → 丘陵黃棕 → 高山白
export const HYPSOMETRIC_COLORS = [
  "#a9d0a0", // 0-100m
  "#c6dd8f", // 100-500m
  "#e3d989", // 500-1000m
  "#e9c178", // 1000-1500m
  "#dba667", // 1500-2000m
  "#c68657", // 2000-2500m
  "#a8694a", // 2500-3000m
  "#8a5240", // 3000-3500m
  "#ff7a00", // 3500m+
];

export const BAND_LABELS = [
  "0–100 m",
  "100–500 m",
  "500–1000 m",
  "1000–1500 m",
  "1500–2000 m",
  "2000–2500 m",
  "2500–3000 m",
  "3000–3500 m",
  "3500 m+",
];

export const hypsometricColor = scaleThreshold()
  .domain(ELEVATION_THRESHOLDS.slice(1))
  .range(HYPSOMETRIC_COLORS);

// --- 降雨圖層 ---
// 資料為 CHIRPS v3.0 的 2025 年逐月降雨量
export const RAIN_YEAR = 2025;

// 12 個月共用同一組門檻與顏色，換月份時顏色才能互相比較。
// 2025 年 7 月破紀錄多雨（山區超過 2000 mm），上端門檻拉到 1200 mm 才不會整島同色。
export const RAIN_THRESHOLDS = [0, 25, 50, 100, 200, 300, 500, 800, 1200];

export const RAIN_COLORS = schemeYlGnBu[9];

export const RAIN_LABELS = [
  "0–25 mm",
  "25–50 mm",
  "50–100 mm",
  "100–200 mm",
  "200–300 mm",
  "300–500 mm",
  "500–800 mm",
  "800–1200 mm",
  "1200 mm+",
];

export const rainColor = scaleThreshold()
  .domain(RAIN_THRESHOLDS.slice(1))
  .range(RAIN_COLORS);

export const MONTH_LABELS = [
  "1 月", "2 月", "3 月", "4 月", "5 月", "6 月",
  "7 月", "8 月", "9 月", "10 月", "11 月", "12 月",
];
