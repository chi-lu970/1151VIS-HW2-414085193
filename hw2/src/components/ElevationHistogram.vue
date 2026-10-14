<script setup>
// View 2：各高程帶統計（水平長條圖）
// 地形圖層：各高程帶佔本島面積的百分比；降雨圖層：各高程帶的當月平均降雨量。
// 這張圖整個由 D3 繪製（select / join / transition），換圖層或月份時長條會平滑伸縮。
import { computed, ref, watch } from "vue";
import { axisBottom, interpolateNumber, max, scaleBand, scaleLinear, select } from "d3";
import { useJson } from "../composables/useJson";
import { useMapState } from "../composables/useMapState";
import { HYPSOMETRIC_COLORS, MONTH_LABELS, RAIN_YEAR, rainColor } from "../constants";

const area = useJson("data/elevation-bands.json");
const rain = useJson("data/rain-by-band.json");
const { layer, month, activeBand, hoverBand } = useMapState();

const loading = computed(() => area.loading.value || rain.loading.value);
const error = computed(() => area.error.value || rain.error.value);

const margin = { top: 34, right: 84, bottom: 78, left: 112 };
const barHeight = 38;
const width = 640;
const innerWidth = width - margin.left - margin.right;
const bandCount = 9;
const height = margin.top + margin.bottom + bandCount * barHeight;
const axisY = height - margin.bottom;

const svg = ref(null);
const isRain = computed(() => layer.value === "rain");

const rows = computed(() => {
  if (!area.data.value || !rain.data.value) return [];
  return area.data.value.bands.map((b, i) => {
    const value = isRain.value ? rain.data.value.bands[i].rain_mm[month.value] : b.pct_of_island;
    return {
      index: i,
      label: b.max_m === null ? `${b.min_m}m 以上` : `${b.min_m}–${b.max_m}m`,
      value,
      fill: isRain.value ? rainColor(value) : HYPSOMETRIC_COLORS[i],
    };
  });
});

// 降雨的 x 軸上限取 12 個月的最大值並固定，換月份時長條長短才能直接比較
const xMax = computed(() => {
  if (!rows.value.length) return 1;
  return isRain.value
    ? max(rain.data.value.bands, (b) => max(b.rain_mm))
    : max(rows.value, (d) => d.value);
});

const xTitle = computed(() => (isRain.value ? `${RAIN_YEAR} 年 ${MONTH_LABELS[month.value]}平均降雨量（mm）` : "佔本島面積比例（%）"));

const footnote = computed(() => {
  if (!rows.value.length) return "";
  return isRain.value
    ? `${RAIN_YEAR} 年 ${MONTH_LABELS[month.value]}本島平均降雨量約 ${Math.round(rain.data.value.island_mean_mm[month.value])} mm`
    : `本島總面積約 ${Math.round(area.data.value.total_island_area_km2).toLocaleString()} km²（估算值）`;
});

const y = scaleBand()
  .domain([...Array(bandCount).keys()])
  .range([margin.top, height - margin.bottom])
  .padding(0.25);

const format = (v) => (isRain.value ? `${Math.round(v)} mm` : `${v.toFixed(1)}%`);

function draw() {
  if (!svg.value || !rows.value.length) return;
  const x = scaleLinear().domain([0, xMax.value * 1.1]).range([0, innerWidth]);
  const root = select(svg.value).select(".plot");
  const t = root.transition().duration(500);

  root
    .select(".axis")
    .transition(t)
    .call(axisBottom(x).ticks(5).tickSizeOuter(0).tickPadding(6).tickFormat((v) => (isRain.value ? v : `${v}%`)));

  // 垂直格線：讓長條長度可以直接對照到刻度
  root
    .select(".grid")
    .transition(t)
    .call(axisBottom(x).ticks(5).tickSize(-(axisY - margin.top)).tickFormat(""))
    .call((g) => g.select(".domain").remove());

  const row = root
    .select(".rows")
    .selectAll("g.bar-row")
    .data(rows.value, (d) => d.index)
    .join((enter) => {
      const g = enter.append("g").attr("class", "bar-row");
      g.append("rect")
        .attr("class", "hit")
        .attr("x", -margin.left)
        .attr("y", (d) => y(d.index) - (y.step() - y.bandwidth()) / 2)
        .attr("width", width)
        .attr("height", y.step());
      g.append("text")
        .attr("class", "y-label")
        .attr("x", -12)
        .attr("y", (d) => y(d.index) + y.bandwidth() / 2)
        .attr("dy", "0.32em")
        .attr("text-anchor", "end")
        .text((d) => d.label);
      g.append("rect")
        .attr("class", "bar")
        .attr("y", (d) => y(d.index))
        .attr("height", y.bandwidth())
        .attr("width", 0)
        .attr("fill", (d) => d.fill);
      g.append("text")
        .attr("class", "value")
        .attr("x", 8)
        .attr("y", (d) => y(d.index) + y.bandwidth() / 2)
        .attr("dy", "0.35em")
        .property("_value", 0);
      // 滑到某一列 → 地圖只亮出那個高程帶
      g.on("pointerenter", (_, d) => (activeBand.value = d.index)).on(
        "pointerleave",
        () => (activeBand.value = null)
      );
      return g;
    });

  row
    .select(".bar")
    .transition(t)
    .attr("width", (d) => x(d.value))
    .attr("fill", (d) => d.fill);

  row
    .select(".value")
    .transition(t)
    .attr("x", (d) => x(d.value) + 8)
    .textTween(function (d) {
      const i = interpolateNumber(this._value, d.value);
      this._value = d.value;
      return (k) => format(i(k));
    });
}

function highlight() {
  if (!svg.value) return;
  const current = activeBand.value ?? hoverBand.value;
  select(svg.value)
    .selectAll("g.bar-row")
    .classed("is-active", (d) => d.index === current);
}

// <svg> 要等資料載入後才會出現，所以 svg 本身也是觸發條件
watch([svg, rows], draw, { flush: "post" });
watch([svg, activeBand, hoverBand], highlight, { flush: "post" });
</script>

<template>
  <div id="elevation-histogram">
    <p v-if="loading" class="status">資料載入中…</p>
    <p v-else-if="error" class="status error">載入失敗：{{ error.message }}</p>
    <svg
      v-else
      ref="svg"
      :viewBox="`0 0 ${width} ${height}`"
      width="100%"
      :style="{ maxWidth: width + 'px' }"
    >
      <!-- 這個群組的內容全部由 D3 管理，Vue 不碰 -->
      <g class="plot" :transform="`translate(${margin.left},0)`">
        <g class="grid" :transform="`translate(0,${axisY})`"></g>
        <g class="axis" :transform="`translate(0,${axisY})`"></g>
        <g class="rows"></g>
        <text class="axis-title" :x="innerWidth / 2" :y="axisY + 50" text-anchor="middle">
          {{ xTitle }}
        </text>
        <text class="axis-title" :x="-12" :y="margin.top - 14" text-anchor="end">海拔高度</text>
      </g>
      <text class="footnote" :x="margin.left" :y="height - 6">{{ footnote }}</text>
    </svg>
  </div>
</template>
