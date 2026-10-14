<script setup>
import GuidePanel from "./components/GuidePanel.vue";
import HypsometricMap from "./components/HypsometricMap.vue";
import ElevationHistogram from "./components/ElevationHistogram.vue";
</script>

<template>
  <div class="spectrum-bar" aria-hidden="true"></div>

  <header>
    <p class="eyebrow">資料分析與視覺化 · 作業二</p>
    <h1>台灣本島的地形與降雨</h1>
    <p class="subtitle">哪裡多雨、什麼時候下？切換月份，看山脈怎麼決定雨落在哪一邊</p>
    <p class="intro">
      資料來源：Copernicus GLO-30 DEM（地形）、CHIRPS v3.0（2025 年逐月降雨量）。
      呈現範圍為台灣本島，不含澎湖、金門、馬祖等離島。
    </p>
  </header>

  <main>
    <GuidePanel />

    <section id="view-map" class="panel">
      <p class="eyebrow">View 01 · 空間分布</p>
      <h2>地形與降雨地圖</h2>
      <p class="panel-desc">
        切換「地形／降雨」圖層，拖動月份或按播放看 12 個月的變化；游標移到地圖上可查該地點的海拔與雨量。
      </p>
      <HypsometricMap />
    </section>

    <section id="view-histogram" class="panel">
      <p class="eyebrow">View 02 · 統計分布</p>
      <h2>各高程帶統計</h2>
      <p class="panel-desc">
        地形圖層顯示各高程帶佔本島面積的比例，降雨圖層顯示各高程帶的當月平均降雨量。
        游標移到長條上，地圖會只亮出那個高度範圍。
      </p>
      <ElevationHistogram />
    </section>
  </main>

  <footer>
    <p>
      地形：Copernicus GLO-30 DEM（AWS Open Data Registry, s3://copernicus-dem-30m）。
      降雨：CHIRPS v3.0（Climate Hazards Center, UC Santa Barbara），2025 年 1–12 月逐月資料，0.05°（約 5 km）解析度。
    </p>
    <p>
      降雨量是 2025 年單一年份的實際月雨量（衛星估計與測站觀測融合），不是長期平均；2025 年 7 月為氣象署 1951 年以來同月最多雨的紀錄，數值明顯高於常年。原始解析度約 5 km，地圖上的細節是內插的結果。
      本島邊界由高程資料以連通元件分析推導，非官方測繪邊界，僅供教學視覺化使用。
    </p>
  </footer>
</template>
