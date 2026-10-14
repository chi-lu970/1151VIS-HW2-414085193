import { ref, watch } from "vue";
import { interval } from "d3";

// 兩個視圖共用的互動狀態（模組層級，所有元件拿到的是同一份）。
const layer = ref("rain"); // "elevation" | "rain"
const month = ref(0); // 0 = 一月
const playing = ref(false);
const activeBand = ref(null); // 長條圖上被滑過的高程帶 → 地圖只亮出該範圍
const hoverBand = ref(null); // 地圖游標所在的高程帶 → 長條圖加外框

// 自動播放：用 d3.interval 每 0.9 秒換下一個月
let timer = null;
watch(playing, (on) => {
  timer?.stop();
  timer = on ? interval(() => (month.value = (month.value + 1) % 12), 900) : null;
});

// 月份只對降雨圖層有意義，切回地形時停止播放
watch(layer, (l) => {
  if (l !== "rain") playing.value = false;
});

export function useMapState() {
  return { layer, month, playing, activeBand, hoverBand };
}
