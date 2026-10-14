<script setup>
// View 1：地形／降雨地圖
// 兩個圖層都用 d3.contours() 依門檻由低到高產生填色多邊形，後畫的（較高的值）疊在先畫的上面；
// 海洋／離島格為 nodata（< 0），天然被排除在所有 contour(>=0) 之外。
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { contours, geoPath, geoTransform, pointer, select } from "d3";
import { useJson } from "../composables/useJson";
import { useMapState } from "../composables/useMapState";
import {
  ELEVATION_THRESHOLDS,
  HYPSOMETRIC_COLORS,
  BAND_LABELS,
  RAIN_THRESHOLDS,
  RAIN_COLORS,
  RAIN_LABELS,
  MONTH_LABELS,
  RAIN_YEAR,
} from "../constants";

const dem = useJson("data/taiwan-dem-grid.json");
const rain = useJson("data/rain-grid.json");
const { layer, month, playing, activeBand, hoverBand } = useMapState();

const grid = dem.data;
const loading = computed(() => dem.loading.value || rain.loading.value);
const error = computed(() => dem.error.value || rain.error.value);

const cellPx = 2.2;
const legendWidth = 200;
const margin = { top: 28, right: 20, bottom: 10, left: 10 };
const NODATA = -9999;

// 緯度方向實際公里數較經度方向長，用 cos(平均緯度) 修正經度方向，避免地圖被拉寬。
const layout = computed(() => {
  if (!grid.value) return null;
  const { width, height, bbox } = grid.value;
  const cosLat = Math.cos((((bbox[1] + bbox[3]) / 2) * Math.PI) / 180);
  const displayWidth = width * cellPx * cosLat;
  const displayHeight = height * cellPx;
  return {
    cosLat,
    displayWidth,
    svgWidth: margin.left + displayWidth + legendWidth + margin.right,
    svgHeight: margin.top + displayHeight + margin.bottom,
  };
});

const path = geoPath(
  geoTransform({
    point(x, y) {
      this.stream.point(x * cellPx, y * cellPx);
    },
  })
);

function bandPathsFor(values, thresholds) {
  const { width, height } = grid.value;
  return contours().size([width, height]).thresholds(thresholds)(values).map((b) => path(b));
}

// 地形等值線只依資料計算一次
const elevationPaths = computed(() =>
  grid.value ? bandPathsFor(grid.value.values, ELEVATION_THRESHOLDS) : []
);

// 降雨等值線每個月算一次後快取。降雨檔的 nodata 是 -1，換成與 DEM 相同的 -9999，
// 兩個圖層的海岸邊緣才會落在同一個位置。
const rainCache = new Map();
function rainPaths(m) {
  if (!rainCache.has(m)) {
    const values = rain.data.value.months[m].map((v) => (v < 0 ? NODATA : v));
    rainCache.set(m, bandPathsFor(values, RAIN_THRESHOLDS));
  }
  return rainCache.get(m);
}

const isRain = computed(() => layer.value === "rain");
const colors = computed(() => (isRain.value ? RAIN_COLORS : HYPSOMETRIC_COLORS));
const labels = computed(() => (isRain.value ? RAIN_LABELS : BAND_LABELS));
const legendTitle = computed(() =>
  isRain.value ? `${RAIN_YEAR} 年 ${MONTH_LABELS[month.value]}降雨量` : "海拔高度"
);

const bandPaths = computed(() => {
  if (!grid.value || !rain.data.value) return [];
  return isRain.value ? rainPaths(month.value) : elevationPaths.value;
});

const outlinePath = computed(() => elevationPaths.value[0] ?? "");

// 長條圖滑到某個高程帶時，用半透明白色蓋住其他地方。
// 三個由大到小的區域（全島 ⊇ 高於下限 ⊇ 高於上限）疊在一起，配合 fill-rule: evenodd，
// 被蓋到偶數次的部分（剛好就是該高程帶）不會填色。
const dimPath = computed(() => {
  const i = activeBand.value;
  const p = elevationPaths.value;
  if (i === null || !p.length) return "";
  const above = p[i + 1] ?? "";
  // 最低一帶的下限就是全島，只需要蓋住比它高的部分
  return i === 0 ? above : p[0] + p[i] + above;
});

// --- 滑過查詢：用 d3.pointer 把游標位置換算成網格的列與欄 ---
const mapGroup = ref(null);
const wrapper = ref(null);
const tip = ref(null);

function onMove(event) {
  const { width, height, values, bbox } = grid.value;
  const [x, y] = pointer(event, mapGroup.value);
  const col = Math.floor(x / cellPx);
  const row = Math.floor(y / cellPx);
  const inside = col >= 0 && col < width && row >= 0 && row < height;
  const elevation = inside ? values[row * width + col] : NODATA;
  if (elevation === NODATA) return onLeave();

  const [left, top] = pointer(event, wrapper.value);
  tip.value = {
    left,
    top,
    elevation: Math.round(elevation),
    rain: rain.data.value.months[month.value][row * width + col],
    lon: bbox[0] + ((col + 0.5) / width) * (bbox[2] - bbox[0]),
    lat: bbox[3] - ((row + 0.5) / height) * (bbox[3] - bbox[1]),
    row,
    col,
  };
  // 最後一個「不高於該海拔」的門檻，就是它所在的高程帶
  hoverBand.value = Math.max(0, ELEVATION_THRESHOLDS.findLastIndex((t) => t <= elevation));
}

function onLeave() {
  tip.value = null;
  hoverBand.value = null;
}

// 播放中游標停在地圖上不動時，提示框的雨量也要跟著月份更新
watch(month, (m) => {
  if (!tip.value) return;
  const { row, col } = tip.value;
  tip.value = { ...tip.value, rain: rain.data.value.months[m][row * grid.value.width + col] };
});

// 地圖的 <g> 要等資料載入後才會出現，出現時再用 D3 綁定事件
watch(mapGroup, (g) => {
  if (g) select(g).on("pointermove", onMove).on("pointerleave", onLeave);
});

onBeforeUnmount(() => {
  playing.value = false;
  onLeave();
});
</script>

<template>
  <div id="hypsometric-map">
    <div class="map-controls">
      <div class="layer-switch" role="group" aria-label="圖層">
        <button :class="{ active: !isRain }" @click="layer = 'elevation'">地形</button>
        <button :class="{ active: isRain }" @click="layer = 'rain'">降雨</button>
      </div>
      <div class="month-control" :class="{ disabled: !isRain }">
        <button
          class="play"
          :disabled="!isRain"
          :aria-label="playing ? '暫停' : '播放'"
          @click="playing = !playing"
        >
          {{ playing ? "❚❚" : "▶" }}
        </button>
        <input
          v-model.number="month"
          type="range"
          min="0"
          max="11"
          step="1"
          :disabled="!isRain"
          aria-label="月份"
        />
        <span class="month-label">{{ MONTH_LABELS[month] }}</span>
      </div>
    </div>

    <p v-if="loading" class="status">資料載入中…</p>
    <p v-else-if="error" class="status error">載入失敗：{{ error.message }}</p>
    <div v-else ref="wrapper" class="map-wrapper">
      <svg
        :viewBox="`0 0 ${layout.svgWidth} ${layout.svgHeight}`"
        width="100%"
        :style="{ maxWidth: layout.svgWidth + 'px' }"
      >
        <g
          ref="mapGroup"
          class="map-area"
          :transform="`translate(${margin.left},${margin.top}) scale(${layout.cosLat},1)`"
        >
          <g class="hypsometric-bands">
            <path v-for="(d, i) in bandPaths" :key="i" :d="d" :fill="colors[i]" />
          </g>
          <path v-if="dimPath" class="map-dim" :d="dimPath" />
          <path class="map-outline" :d="outlinePath" />
        </g>

        <g
          class="legend"
          :transform="`translate(${margin.left + layout.displayWidth + 24}, ${margin.top + 10})`"
        >
          <text class="legend-title" x="0" y="-14">{{ legendTitle }}</text>
          <g
            v-for="(color, i) in colors"
            :key="i"
            class="legend-row"
            :transform="`translate(0, ${i * 28})`"
          >
            <rect width="20" height="20" :fill="color" stroke="#00000022" />
            <text x="30" y="10" dy="0.35em">{{ labels[i] }}</text>
          </g>
        </g>
      </svg>

      <div v-if="tip" class="map-tooltip" :style="{ left: tip.left + 'px', top: tip.top + 'px' }">
        <div class="tip-coord">{{ tip.lat.toFixed(2) }}°N, {{ tip.lon.toFixed(2) }}°E</div>
        <div>海拔 <strong>{{ tip.elevation.toLocaleString() }}</strong> m</div>
        <div>{{ RAIN_YEAR }} 年 {{ MONTH_LABELS[month] }}降雨 <strong>{{ tip.rain }}</strong> mm</div>
      </div>
    </div>
  </div>
</template>
