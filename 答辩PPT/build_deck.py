from pathlib import Path

root = Path(__file__).resolve().parent
index = root / "index.html"
html = index.read_text(encoding="utf-8")

slides = r'''
<!-- ============================================================
     RealtimeShadow 答辩 PPT · generated from realtimeshadow.pdf
     Style B: Swiss / IKB
     页码 → data-layout → 用途
     01 S01 封面
     02 S03 问题定义
     03 S11 渲染流程
     04 S17 系统结构
     05 S04 三类阴影方法
     06 S21 关键参数
     07 S22 硬阴影结果
     08 S22 PCF 结果
     09 S22 PCSS 结果
     10 S16 Blocker 可视化
     11 S08 方法对比
     12 S10 总结
     ============================================================ -->

<section class="slide accent" data-layout="S01" data-animate="hero">
  <div class="canvas-card">
    <canvas class="ascii-bg" aria-hidden="true"></canvas>
    <div class="chrome-min">
      <div class="l">Realtime Shadow · WebGL</div>
      <div class="r">Defense · 2026.05.31 · 01 / 12</div>
    </div>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto 1fr auto;gap:2.6vh">
      <div data-anim="kicker" class="t-meta" style="color:rgba(255,255,255,.78);letter-spacing:.22em">TWO-PASS SHADOW MAP · PCF · PCSS</div>
      <h1 data-anim="title" style="align-self:start;font-family:var(--sans),var(--sans-zh);font-weight:200;font-size:min(9.6vw,16.5vh);line-height:.96;letter-spacing:-.025em;color:#fff">实时阴影<br/>渲染实现</h1>
      <div data-anim="bottom" style="display:grid;grid-template-rows:auto auto;gap:1.6vh;border-top:1px solid rgba(255,255,255,.22);padding-top:2vh">
        <div class="lead" style="max-width:58ch;color:rgba(255,255,255,.86)">基于 WebGL 实现 Shadow Map 硬阴影、固定半径 PCF、深度相关 PCSS，并扩展 blocker 调试可视化、多光源叠加和移动光源。</div>
        <div style="display:flex;justify-content:space-between;align-items:end">
          <div class="t-meta" style="color:rgba(255,255,255,.6)">安燕杰 · 李志阳</div>
          <div class="t-meta" style="color:rgba(255,255,255,.6)">答辩汇报</div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="slide split" data-layout="S03" data-animate="split-statement">
  <div class="canvas-card">
    <div class="split-half">
      <div class="half b-ink" style="justify-content:space-between">
        <div class="chrome-min"><div class="l">02 / 12</div><div class="r">PROBLEM</div></div>
        <div data-anim="statement">
          <div class="t-meta on-dark" style="margin-bottom:2vh">WHY SHADOW</div>
          <h2 style="font-family:var(--sans),var(--sans-zh);font-weight:200;font-size:min(7.2vw,12.8vh);line-height:.98;letter-spacing:-.025em;color:var(--paper)">阴影表达<br/>空间关系</h2>
        </div>
        <div class="t-meta on-dark">Local lighting is not enough.</div>
      </div>
      <div class="half b-grey" style="justify-content:center;gap:4vh">
        <div data-anim="copy" class="lead" style="max-width:34ch;color:var(--text-primary)">局部光照只能计算表面明暗，不能处理物体之间的遮挡；离线路径追踪质量高但不适合 WebGL 实时场景。</div>
        <div data-anim="rules" style="display:grid;grid-template-columns:1fr;gap:1.6vh">
          <div class="card-fill" style="padding:2.2vh 1.6vw"><div class="t-cat">目标 01</div><div class="body-sm">从光源视角记录最近深度。</div></div>
          <div class="card-fill" style="padding:2.2vh 1.6vw"><div class="t-cat">目标 02</div><div class="body-sm">从相机视角比较片元深度与 shadow map。</div></div>
          <div class="card-fill" style="padding:2.2vh 1.6vw"><div class="t-cat accent">目标 03</div><div class="body-sm">在实时约束下逐步得到更自然的软阴影。</div></div>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="slide light" data-layout="S11" data-animate="timeline-h">
  <div class="canvas-card">
    <div class="chrome-min"><div class="l">RealtimeShadow · Pipeline</div><div class="r">03 / 12</div></div>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto 1fr auto;gap:4vh">
      <div data-anim="head" style="display:flex;flex-direction:column;gap:1.4vh">
        <div class="t-meta">RENDER PIPELINE</div>
        <h2 class="h-xl-zh" style="font-size:min(5.2vw,9.2vh)">Two-Pass Shadow Map</h2>
      </div>
      <div class="timeline-h" data-anim="timeline" style="min-height:42vh">
        <div class="tl-row">
          <div class="th-node up accent" style="left:4%"><span class="dot"></span><div class="label"><div class="yr">01</div><div class="name">Shadow Pass</div><div class="desc">从光源视角写入 FBO 深度。</div></div></div>
          <div class="th-node down" style="left:26%"><span class="dot"></span><div class="label"><div class="yr">02</div><div class="name">Pack / Unpack</div><div class="desc">RGBA 纹理存储深度，兼容 WebGL1。</div></div></div>
          <div class="th-node up" style="left:50%"><span class="dot"></span><div class="label"><div class="yr">03</div><div class="name">Camera Pass</div><div class="desc">片元采样 shadow map 并做深度比较。</div></div></div>
          <div class="th-node down accent" style="left:74%"><span class="dot"></span><div class="label"><div class="yr">04</div><div class="name">Multi Light</div><div class="desc">每个光源独立 shadow map，直接光照加法叠加。</div></div></div>
        </div>
      </div>
      <div class="body-sm" style="border-top:1px solid var(--border-subtle);padding-top:2vh;color:var(--text-secondary)">核心数据结构：普通网格在 <span class="mono">renderer.meshes</span>，阴影网格按光源索引保存到 <span class="mono">renderer.shadowMeshes[lightIndex]</span>。</div>
    </div>
  </div>
</section>

<section class="slide dark" data-layout="S17" data-animate="system-diagram">
  <div class="canvas-card">
    <div class="chrome-min"><div class="l">System Design</div><div class="r">04 / 12</div></div>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto 1fr auto;gap:3.4vh">
      <div data-anim="head" style="display:grid;grid-template-columns:5fr 6fr;gap:4vw;align-items:end">
        <div><div class="t-meta on-dark" style="margin-bottom:1.4vh">ARCHITECTURE</div><h2 class="h-xl-zh" style="font-size:min(4.8vw,8.6vh);color:var(--paper)">每个光源一张 Shadow Map</h2></div>
        <p class="body" style="color:rgba(255,255,255,.75)">移动光源改变位置后，渲染器在每帧重新计算 <span class="mono">uLightMVP</span>，并同步 shadow map、光强和 ambient 开关。</p>
      </div>
      <div data-anim="diagram" style="display:grid;grid-template-columns:1.05fr .55fr 1.05fr;gap:2vw;align-items:center">
        <div class="card-fill" style="padding:3vh 2vw;min-height:28vh">
          <div class="t-cat">Light 0 · warm</div>
          <div class="num-mega thin" style="font-size:min(4.8vw,8vh);margin:1.8vh 0;color:var(--ink)">3000</div>
          <div class="body-sm">固定主光，位置 (0, 80, 80)，负责主要照明与阴影。</div>
        </div>
        <div style="display:grid;place-items:center;color:var(--accent)">
          <div style="width:100%;height:1px;background:var(--accent)"></div>
          <div class="t-meta" style="margin-top:2vh;color:var(--accent)">ADD</div>
        </div>
        <div class="card-fill" style="padding:3vh 2vw;min-height:28vh">
          <div class="t-cat">Light 1 · cool</div>
          <div class="num-mega thin" style="font-size:min(4.8vw,8vh);margin:1.8vh 0;color:var(--accent)">2500</div>
          <div class="body-sm">轨道冷光，按 x/z 三角函数更新位置，形成随时间变化的阴影方向。</div>
        </div>
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1.4vw;border-top:1px solid rgba(255,255,255,.18);padding-top:2vh">
        <div class="body-sm" style="color:rgba(255,255,255,.74)">独立 FBO：8192 x 8192</div>
        <div class="body-sm" style="color:rgba(255,255,255,.74)">后续光源：<span class="mono">gl.ONE, gl.ONE</span></div>
        <div class="body-sm" style="color:rgba(255,255,255,.74)">Ambient：仅第一个 pass 加入</div>
      </div>
    </div>
  </div>
</section>

<section class="slide grey" data-layout="S04" data-animate="grid-reveal">
  <div class="canvas-card">
    <div class="chrome-min"><div class="l">Method Stack</div><div class="r">05 / 12</div></div>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto 1fr;gap:4vh">
      <div data-anim="head" style="display:flex;flex-direction:column;gap:1.4vh">
        <div class="t-meta">THREE MODES</div>
        <h2 class="h-xl-zh" style="font-size:min(5.2vw,9.2vh)">从硬阴影到动态半影</h2>
      </div>
      <div data-anim="grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:1.6vw;align-content:start">
        <div class="card-fill" style="padding:3vh 2vw;min-height:40vh"><div class="t-cat">Shadow Map</div><h3 class="h-md" style="margin:2vh 0">一次深度比较</h3><p class="body-sm">实现简单，遮挡关系明确；边界二值跳变，轮廓硬且容易锯齿。</p></div>
        <div class="card-fill" style="padding:3vh 2vw;min-height:40vh"><div class="t-cat">PCF</div><h3 class="h-md" style="margin:2vh 0">固定半径多采样</h3><p class="body-sm">Poisson 圆盘 40 次采样，取平均后边缘连续；但软硬程度不随深度变化。</p></div>
        <div class="card-accent" style="padding:3vh 2vw;min-height:40vh"><div class="t-cat">PCSS</div><h3 class="h-md" style="margin:2vh 0;color:var(--accent-on)">Blocker + Penumbra</h3><p class="body-sm" style="color:rgba(255,255,255,.86)">先搜索遮挡物平均深度，再估计半影半径，用动态 filter size 做 PCF。</p></div>
      </div>
    </div>
  </div>
</section>

<section class="slide light" data-layout="S21" data-animate="tech-spec">
  <div class="canvas-card">
    <div class="chrome-min"><div class="l">Implementation Parameters</div><div class="r">06 / 12</div></div>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto 1fr;gap:3.2vh">
      <div data-anim="head" style="display:flex;flex-direction:column;gap:1.4vh">
        <div class="t-meta">TECH SPEC</div>
        <h2 class="h-xl-zh" style="font-size:min(5vw,8.8vh)">质量与性能的折中</h2>
      </div>
      <div data-anim="spec" style="display:grid;grid-template-columns:1.1fr 1fr;gap:3vw;align-items:start">
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:1.2vw">
          <div class="card-fill" style="padding:2.4vh 1.5vw"><div class="t-cat">Shadow Map</div><div class="num-mega thin" style="font-size:min(4.8vw,8vh)">8192</div><div class="body-sm">x 8192 分辨率</div></div>
          <div class="card-fill" style="padding:2.4vh 1.5vw"><div class="t-cat">Samples</div><div class="num-mega thin" style="font-size:min(4.8vw,8vh);color:var(--accent)">40</div><div class="body-sm">PCF / PCSS 采样数</div></div>
          <div class="card-fill" style="padding:2.4vh 1.5vw"><div class="t-cat">Bias</div><div class="num-mega thin" style="font-size:min(3.8vw,6.8vh)">0.012</div><div class="body-sm">缓解 shadow acne</div></div>
          <div class="card-fill" style="padding:2.4vh 1.5vw"><div class="t-cat">Filter</div><div class="num-mega thin" style="font-size:min(3.8vw,6.8vh)">0.0008-0.009</div><div class="body-sm">PCSS 动态滤波范围</div></div>
        </div>
        <div class="bar-chart" style="padding-top:1vh">
          <div class="bar-row"><div class="bar-label">PCF radius</div><div class="bar-track"><div class="bar-fill" style="width:39%"></div></div><div class="bar-value">0.0035</div></div>
          <div class="bar-row"><div class="bar-label">Blocker</div><div class="bar-track"><div class="bar-fill" style="width:50%"></div></div><div class="bar-value">0.0045</div></div>
          <div class="bar-row"><div class="bar-label">Light size</div><div class="bar-track"><div class="bar-fill" style="width:78%"></div></div><div class="bar-value">0.007</div></div>
          <div class="bar-row"><div class="bar-label">Max filter</div><div class="bar-track"><div class="bar-fill" style="width:100%"></div></div><div class="bar-value">0.009</div></div>
          <p class="body-sm" style="margin-top:3vh;color:var(--text-secondary)">参数过小会导致噪声或锯齿，过大会产生 Peter Panning 或过度模糊；当前取值优先保证答辩截图稳定。</p>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="slide light" data-layout="S22" data-image-slot="s22-hero-21x9" data-animate="image-hero">
  <div class="canvas-card">
    <div class="chrome-min"><div class="l">Experiment 01 · Hard Shadow</div><div class="r">07 / 12</div></div>
    <div class="image-hero-body">
      <figure class="frame-img r-21x9 fit-contain swiss-lined" data-anim="image"><img data-image-slot="s22-hero-21x9" src="images/SM_shadow.png" alt="Shadow Map hard shadow result"></figure>
      <div data-anim="title" style="display:grid;grid-template-columns:1fr 1.1fr;gap:3vw;align-items:start">
        <div><div class="t-meta">RESULT</div><h2 class="h-xl-zh" style="font-size:min(4.8vw,8.5vh)">硬阴影验证基础管线</h2></div>
        <p class="body">光源 MVP、Shadow Pass、深度打包/解包和深度比较均能正常工作；双方向阴影来自两个独立光源。</p>
      </div>
      <div class="image-hero-stats" data-anim="stats">
        <div><div class="t-cat">优点</div><div class="body-sm">遮挡关系清晰</div></div>
        <div><div class="t-cat">问题</div><div class="body-sm">边界硬、锯齿明显</div></div>
        <div><div class="t-cat">用途</div><div class="body-sm">验证基础 Shadow Map</div></div>
      </div>
    </div>
  </div>
</section>

<section class="slide grey" data-layout="S22" data-image-slot="s22-hero-21x9" data-animate="image-hero">
  <div class="canvas-card">
    <div class="chrome-min"><div class="l">Experiment 02 · PCF</div><div class="r">08 / 12</div></div>
    <div class="image-hero-body">
      <figure class="frame-img r-21x9 fit-contain swiss-lined" data-anim="image"><img data-image-slot="s22-hero-21x9" src="images/PCF_shadow.png" alt="PCF shadow result"></figure>
      <div data-anim="title" style="display:grid;grid-template-columns:1fr 1.1fr;gap:3vw;align-items:start">
        <div><div class="t-meta">RESULT</div><h2 class="h-xl-zh" style="font-size:min(4.8vw,8.5vh)">PCF 将二值边界变成连续过渡</h2></div>
        <p class="body">PCF 对邻域内多次 shadow test 取平均，明显削弱硬阴影锯齿；固定滤波半径让接触区域和远处边缘的宽度差异不明显。</p>
      </div>
      <div class="image-hero-stats" data-anim="stats">
        <div><div class="t-cat">采样核</div><div class="body-sm">Poisson disk</div></div>
        <div><div class="t-cat">采样数</div><div class="body-sm">40</div></div>
        <div><div class="t-cat">半径</div><div class="body-sm">固定 0.0035</div></div>
      </div>
    </div>
  </div>
</section>

<section class="slide dark" data-layout="S22" data-image-slot="s22-hero-21x9" data-animate="image-hero">
  <div class="canvas-card">
    <div class="chrome-min"><div class="l">Experiment 03 · PCSS</div><div class="r">09 / 12</div></div>
    <div class="image-hero-body">
      <figure class="frame-img r-21x9 fit-contain swiss-lined" data-anim="image"><img data-image-slot="s22-hero-21x9" src="images/PCSS_shadow.png" alt="PCSS shadow result"></figure>
      <div data-anim="title" style="display:grid;grid-template-columns:1fr 1.1fr;gap:3vw;align-items:start">
        <div><div class="t-meta on-dark">RESULT</div><h2 class="h-xl-zh" style="font-size:min(4.8vw,8.5vh);color:var(--paper)">PCSS 表现接触硬、远处软</h2></div>
        <p class="body" style="color:rgba(255,255,255,.76)">PCSS 先搜索 blocker 平均深度，再由 receiver 与 blocker 的深度差估计半影大小，最后用动态半径执行 PCF。</p>
      </div>
      <div class="image-hero-stats" data-anim="stats" style="color:var(--paper)">
        <div><div class="t-cat on-dark">Blocker</div><div class="body-sm" style="color:rgba(255,255,255,.78)">搜索平均遮挡物深度</div></div>
        <div><div class="t-cat on-dark">Penumbra</div><div class="body-sm" style="color:rgba(255,255,255,.78)">按深度差放大滤波半径</div></div>
        <div><div class="t-cat on-dark">Cost</div><div class="body-sm" style="color:rgba(255,255,255,.78)">参数敏感、采样开销更高</div></div>
      </div>
    </div>
  </div>
</section>

<section class="slide light" data-layout="S16" data-image-slot="s16-brief-21x9" data-animate="grid-reveal">
  <div class="canvas-card">
    <div class="chrome-min"><div class="l">Debug Visualization</div><div class="r">10 / 12</div></div>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto 1fr auto;gap:3vh">
      <div data-anim="head" style="display:flex;flex-direction:column;gap:1.4vh">
        <div class="t-meta">BLOCKER SEARCH</div>
        <h2 class="h-xl-zh" style="font-size:min(5vw,8.8vh)">红绿色标验证遮挡分布</h2>
      </div>
      <div data-anim="grid" style="display:grid;grid-template-columns:repeat(3,1fr);gap:1.4vw">
        <figure class="tile"><div class="frame-img r-16x10 fit-contain swiss-lined"><img data-image-slot="s16-brief-16x10" src="images/SM_blocker_debug.png" alt="Shadow Map blocker debug"></div><figcaption class="swiss-img-caption"><span>Shadow Map</span><span>硬阴影模式</span></figcaption></figure>
        <figure class="tile"><div class="frame-img r-16x10 fit-contain swiss-lined"><img data-image-slot="s16-brief-16x10" src="images/PCF_blocker_debug.png" alt="PCF blocker debug"></div><figcaption class="swiss-img-caption"><span>PCF</span><span>固定滤波模式</span></figcaption></figure>
        <figure class="tile"><div class="frame-img r-16x10 fit-contain swiss-lined"><img data-image-slot="s16-brief-16x10" src="images/PCSS_blocker_debug.png" alt="PCSS blocker debug"></div><figcaption class="swiss-img-caption"><span>PCSS</span><span>动态半影模式</span></figcaption></figure>
      </div>
      <div class="body-sm" style="border-top:1px solid var(--border-subtle);padding-top:2vh;color:var(--text-secondary)">绿色表示几乎没有 blocker，红色表示 blocker 比例较高；该图用于验证 blocker search 与几何遮挡关系一致，而不是直接等同最终阴影明暗。</div>
    </div>
  </div>
</section>

<section class="slide grey" data-layout="S08" data-animate="duo-compare">
  <div class="canvas-card">
    <div class="chrome-min"><div class="l">Comparison</div><div class="r">11 / 12</div></div>
    <div style="flex:1;padding:0;display:grid;grid-template-rows:auto 1fr;gap:4vh">
      <div data-anim="head" style="display:flex;flex-direction:column;gap:1.4vh">
        <div class="t-meta">METHOD TRADE-OFF</div>
        <h2 class="h-xl-zh" style="font-size:min(5vw,8.8vh)">三种方法的定位不同</h2>
      </div>
      <div class="duo-compare" data-anim="compare">
        <div class="col">
          <div class="col-tag"><span class="num">01</span><span>FAST BASELINE</span></div>
          <div class="col-ttl">Shadow Map / PCF</div>
          <div class="col-desc">用于建立稳定实时管线，并以较低额外开销改善硬阴影边界。</div>
          <ul class="col-list"><li>实现简单，便于调试</li><li>PCF 实时性较好</li><li>固定半径限制真实感</li></ul>
        </div>
        <div class="vrule"></div>
        <div class="col accent">
          <div class="col-tag"><span class="num">02</span><span>DEPTH AWARE</span></div>
          <div class="col-ttl">PCSS</div>
          <div class="col-desc">通过 blocker search 和半影估计，让阴影宽度随遮挡物与接收面距离变化。</div>
          <ul class="col-list"><li>接触阴影更清晰</li><li>远离遮挡物处更柔和</li><li>采样开销和参数敏感度更高</li></ul>
        </div>
      </div>
    </div>
  </div>
</section>

<section class="slide split" data-layout="S10" data-animate="split-statement">
  <div class="canvas-card">
    <div class="split-half">
      <div class="half b-accent" style="padding:5.6vh 3.6vw 4.4vh;justify-content:space-between;position:relative;overflow:hidden">
        <canvas class="ascii-bg" aria-hidden="true"></canvas>
        <div class="chrome-min" style="margin-bottom:0;position:relative;z-index:1"><div class="l">12 / 12</div><div class="r">CONCLUSION</div></div>
        <div data-anim="manifesto" style="position:relative;z-index:1">
          <div class="t-meta" style="color:rgba(255,255,255,.78);letter-spacing:.22em;margin-bottom:2vh">TAKEAWAY</div>
          <h2 style="font-family:var(--sans),var(--sans-zh);font-size:min(7.2vw,12.8vh);line-height:.96;letter-spacing:-.025em;font-weight:200;color:#fff">管线已跑通<br/>软阴影可控</h2>
        </div>
        <div class="t-meta" style="color:rgba(255,255,255,.62);position:relative;z-index:1">End · RealtimeShadow</div>
      </div>
      <div class="half" style="padding:5.6vh 3.6vw 4.4vh;justify-content:space-between">
        <div class="chrome-min"><div class="l">SUMMARY</div><div class="r">03 POINTS</div></div>
        <div data-anim="rules" style="display:flex;flex-direction:column;gap:0">
          <div style="display:grid;grid-template-columns:auto 1fr;gap:2vw;align-items:start;padding:2.4vh 0;border-top:1px solid var(--border-subtle)">
            <div style="font-family:var(--sans);font-weight:200;font-size:min(4.2vw,7.4vh);line-height:.9">01</div>
            <div><h3 style="font-size:max(18px,1.7vw);font-weight:400;margin-bottom:1vh">完成三类阴影模式</h3><p class="body-sm">硬阴影、PCF 与 PCSS 均可通过 shader 注释切换，并在同一双光源场景验证。</p></div>
          </div>
          <div style="display:grid;grid-template-columns:auto 1fr;gap:2vw;align-items:start;padding:2.4vh 0;border-top:1px solid var(--border-subtle)">
            <div style="font-family:var(--sans);font-weight:200;font-size:min(4.2vw,7.4vh);line-height:.9">02</div>
            <div><h3 style="font-size:max(18px,1.7vw);font-weight:400;margin-bottom:1vh">扩展调试与多光源</h3><p class="body-sm">实现 Shadow Map 小窗、blocker 搜索可视化、双光源加法叠加和移动光源动画。</p></div>
          </div>
          <div style="display:grid;grid-template-columns:auto 1fr;gap:2vw;align-items:start;padding:2.4vh 0;border-top:1px solid var(--border-subtle);border-bottom:2px solid var(--accent)">
            <div style="font-family:var(--sans);font-weight:200;font-size:min(4.2vw,7.4vh);line-height:.9;color:var(--accent)">03</div>
            <div><h3 style="font-size:max(18px,1.7vw);font-weight:400;margin-bottom:1vh;color:var(--accent)">后续优化方向</h3><p class="body-sm">更稳定的采样序列、降低 shadow map 显存开销、使用时间累积降低噪声。</p></div>
          </div>
        </div>
        <div class="t-meta" style="color:var(--text-helper);text-align:right">Q & A</div>
      </div>
    </div>
  </div>
</section>
'''

original_marker = "<!-- ============================================================\n     SLIDES 插入区"
generated_marker = "<!-- ============================================================\n     RealtimeShadow 答辩 PPT"
start = html.find(original_marker)
if start == -1:
    start = html.index(generated_marker)
end = html.index("\n</div>\n\n<div id=\"nav\"></div>", start)
html = html[:start] + slides + html[end:]
html = html.replace("[必填] 替换为 PPT 标题 · Deck Title", "实时阴影渲染实现 · 答辩PPT")
index.write_text(html, encoding="utf-8")
print(index)
