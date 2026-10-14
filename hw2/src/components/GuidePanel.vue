<script setup>
const steps = [
  {
    title: "地形與降雨地圖",
    question: "哪裡高？哪裡多雨？",
    desc: "切到降雨圖層後按播放：冬天雨集中在東北部迎風面，西南部幾乎不下雨；<br />夏天雨帶換到南部與山區。",
  },
  {
    title: "各高程帶統計",
    question: "越高的地方雨越多嗎？",
    desc: "每條長條是一個高度區間。游標移上去，地圖會標出這個高度在哪裡；游標在地圖上移動時，對應的長條也會加框。",
  },
];
</script>

<template>
  <section class="panel guide">
    <h2>怎麼讀這份視覺化</h2>
    <div class="guide-steps">
      <div v-for="(s, i) in steps" :key="s.title" class="guide-step">
        <span class="step-num">{{ i + 1 }}</span>
        <p class="guide-step-text">
          <strong>{{ s.title }}</strong><br />
          {{ s.question }}<br />
          <span class="guide-step-desc" v-html="s.desc"></span>
        </p>
      </div>
    </div>
  </section>
</template>
