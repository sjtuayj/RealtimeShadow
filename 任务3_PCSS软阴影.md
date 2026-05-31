# 任务3：PCSS（Percentage Closer Soft Shadow）软阴影

## 一、原理

### 1.1 PCF 的局限

任务2的 PCF 使用固定半径 `filterSize` 对 Shadow Map 做多次采样：

```
visibility = (1/N) * Σᵢ shadowTest(uv + offsetᵢ × filterSize)
```

它可以把硬阴影边缘变成柔和过渡，但所有位置使用同一个滤波半径，因此阴影软硬程度基本一致。真实软阴影并不是这样：遮挡物和接收面越接近，阴影越硬；接收面离遮挡物越远，半影越宽，阴影越软。

| | PCF | PCSS |
|---|---|---|
| 滤波半径 | 固定 | 根据 blocker 和 receiver 深度动态变化 |
| 接触阴影 | 可能偏软 | 接触处更硬 |
| 远离遮挡物 | 软硬不变 | 半影逐渐变宽 |
| 核心额外步骤 | 无 | blocker search + penumbra 估算 |

### 1.2 PCSS 核心流程

PCSS 可以理解为在 PCF 前先估计“当前片元应该有多软”：

```
STEP 1: Blocker Search
        在 receiver 附近搜索比 receiver 更靠近光源的深度样本
        得到平均遮挡物深度 avgBlockerDepth

STEP 2: Penumbra Estimation
        根据 receiver 深度和 blocker 深度的距离估算半影大小
        receiver 离 blocker 越远，filterSize 越大

STEP 3: Variable-size PCF
        用动态 filterSize 做 PCF
```

当前实现中的半影估算为：

```
penumbraRatio = (zReceiver - avgBlockerDepth) / avgBlockerDepth
filterSize = clamp(penumbraRatio * LIGHT_SIZE_UV,
                   PCSS_MIN_FILTER_SIZE,
                   PCSS_MAX_FILTER_SIZE)
```

其中：

- `zReceiver`：当前片元在 light space 中的深度
- `avgBlockerDepth`：搜索得到的平均遮挡物深度
- `LIGHT_SIZE_UV`：模拟面积光大小
- `PCSS_MIN_FILTER_SIZE` / `PCSS_MAX_FILTER_SIZE`：限制滤波半径，避免过硬或过糊

### 1.3 findBlocker

`findBlocker()` 在当前片元的 Shadow Map UV 附近做 Poisson 圆盘采样。每个采样点读取 Shadow Map 深度：

```
closestDepth = unpack(texture2D(shadowMap, sampleUV))
```

如果：

```
zReceiver - bias > closestDepth
```

说明该采样点上有物体挡在 receiver 前面，是 blocker。函数累加所有 blocker 深度并取平均。

如果没有找到 blocker，说明当前片元没有被遮挡，直接返回可见：

```
return 1.0
```

### 1.4 动态 PCF

为了让 PCSS 复用任务2的 PCF 逻辑，将原来的 PCF 拆成两层：

```glsl
float PCFWithFilterSize(sampler2D shadowMap, vec4 coords, float filterSize)
float PCF(sampler2D shadowMap, vec4 coords)
```

- `PCFWithFilterSize()`：真正执行多采样阴影测试，滤波半径由参数传入
- `PCF()`：固定半径版本，保持任务2行为
- `PCSS()`：计算动态半径后调用 `PCFWithFilterSize()`

### 1.5 阴影只影响直接光照

之前直接使用：

```glsl
gl_FragColor = vec4(phongColor * visibility, 1.0);
```

会把环境光也一起压暗，阴影看起来像一块黑色贴图。当前实现改为在 Blinn-Phong 内部只让 `visibility` 影响直接光照：

```glsl
vec3 radiance = ambient + visibility * (diffuse + specular);
```

这样阴影区域仍保留基础环境亮度，视觉上更接近真实阴影。

### 1.6 数据流

```
片元 shadowCoord
  │
  ├→ PCSS()
  │    │
  │    ├→ 边界检查（超出 [0,1] → 可见）
  │    │
  │    ├→ findBlocker()
  │    │    ├→ poissonDiskSamples(uv)
  │    │    ├→ 在 BLOCKER_SEARCH_SIZE 半径内搜索 blocker
  │    │    └→ 返回 avgBlockerDepth，没有 blocker 返回 -1.0
  │    │
  │    ├→ 根据 avgBlockerDepth 估算 penumbraRatio
  │    ├→ 得到动态 filterSize
  │    │
  │    └→ PCFWithFilterSize(shadowMap, coords, filterSize)
  │         └→ 多次 shadow test 后取平均 visibility
  │
  └→ blinnPhong(visibility)
       └→ ambient + visibility × (diffuse + specular)
```

---

## 二、代码修改

主要修改 **1 个文件**：

- `src/shaders/phongShader/phongFragment.glsl`

同时为了提升整体 shadow map 精度，调优了光源正交投影参数：

- `src/lights/DirectionalLight.js`

### 修改1：[phongFragment.glsl](src/shaders/phongShader/phongFragment.glsl) — PCSS 参数

新增和调整阴影参数：

```glsl
#define NUM_SAMPLES 40
#define BLOCKER_SEARCH_NUM_SAMPLES NUM_SAMPLES
#define PCF_NUM_SAMPLES NUM_SAMPLES
#define NUM_RINGS 11

#define SHADOW_BIAS 0.004
#define BLOCKER_SEARCH_SIZE 0.0045
#define LIGHT_SIZE_UV 0.007
#define PCF_FILTER_SIZE 0.0035
#define PCSS_MIN_FILTER_SIZE 0.0008
#define PCSS_MAX_FILTER_SIZE 0.009
```

参数含义：

| 参数 | 值 | 说明 |
|------|-----|------|
| `NUM_SAMPLES` | 40 | blocker search 和 PCF 的采样数 |
| `SHADOW_BIAS` | 0.004 | 缓解 shadow acne，同时避免阴影过度漂移 |
| `BLOCKER_SEARCH_SIZE` | 0.0045 | blocker 搜索半径 |
| `LIGHT_SIZE_UV` | 0.007 | 模拟面积光大小 |
| `PCF_FILTER_SIZE` | 0.0035 | 任务2 PCF 的固定滤波半径 |
| `PCSS_MIN_FILTER_SIZE` | 0.0008 | PCSS 最小滤波半径 |
| `PCSS_MAX_FILTER_SIZE` | 0.009 | PCSS 最大滤波半径 |

### 修改2：[phongFragment.glsl](src/shaders/phongShader/phongFragment.glsl) — 实现 `findBlocker()`

原函数为空实现：

```glsl
float findBlocker( sampler2D shadowMap,  vec2 uv, float zReceiver ) {
  return 1.0;
}
```

当前实现：

```glsl
float findBlocker( sampler2D shadowMap,  vec2 uv, float zReceiver ) {
  poissonDiskSamples(uv);

  float blockerDepthSum = 0.0;
  int blockerCount = 0;
  float bias = SHADOW_BIAS;

  for (int i = 0; i < BLOCKER_SEARCH_NUM_SAMPLES; i++) {
    vec2 sampleUV = uv + poissonDisk[i] * BLOCKER_SEARCH_SIZE;
    if (sampleUV.x < 0.0 || sampleUV.x > 1.0 || sampleUV.y < 0.0 || sampleUV.y > 1.0) {
      continue;
    }

    float closestDepth = unpack(texture2D(shadowMap, sampleUV));
    if (zReceiver - bias > closestDepth) {
      blockerDepthSum += closestDepth;
      blockerCount++;
    }
  }

  if (blockerCount == 0) {
    return -1.0;
  }

  return blockerDepthSum / float(blockerCount);
}
```

与原理对应：

| 代码 | 说明 |
|------|------|
| `poissonDiskSamples(uv)` | 生成 blocker search 的圆盘采样点 |
| `sampleUV = uv + poissonDisk[i] * BLOCKER_SEARCH_SIZE` | 在当前片元附近搜索遮挡物 |
| `zReceiver - bias > closestDepth` | 判断该采样点是否存在 blocker |
| `blockerDepthSum / float(blockerCount)` | 返回平均 blocker depth |
| `return -1.0` | 没有 blocker，表示当前片元可见 |

### 修改3：[phongFragment.glsl](src/shaders/phongShader/phongFragment.glsl) — 抽出动态半径 PCF

为了支持 PCSS 的动态滤波半径，将 PCF 核心逻辑写成：

```glsl
float PCFWithFilterSize(sampler2D shadowMap, vec4 coords, float filterSize) {
  ...
}
```

任务2的固定半径 PCF 仍然保留：

```glsl
float PCF(sampler2D shadowMap, vec4 coords) {
  return PCFWithFilterSize(shadowMap, coords, PCF_FILTER_SIZE);
}
```

这样 PCF 和 PCSS 共用同一套采样和边界检查逻辑，区别只在于 `filterSize` 是固定还是动态计算。

### 修改4：[phongFragment.glsl](src/shaders/phongShader/phongFragment.glsl) — 实现 `PCSS()`

原函数为空实现：

```glsl
float PCSS(sampler2D shadowMap, vec4 coords){
  return 1.0;
}
```

当前实现：

```glsl
float PCSS(sampler2D shadowMap, vec4 coords){
  vec3 projCoords = coords.xyz;

  if (projCoords.x < 0.0 || projCoords.x > 1.0 ||
      projCoords.y < 0.0 || projCoords.y > 1.0 ||
      projCoords.z < 0.0 || projCoords.z > 1.0) {
    return 1.0;
  }

  // STEP 1: avgblocker depth
  float avgBlockerDepth = findBlocker(shadowMap, projCoords.xy, projCoords.z);
  if (avgBlockerDepth < 0.0) {
    return 1.0;
  }

  // STEP 2: penumbra size
  float penumbraRatio = (projCoords.z - avgBlockerDepth) / max(avgBlockerDepth, EPS);
  float filterSize = clamp(
    penumbraRatio * LIGHT_SIZE_UV,
    PCSS_MIN_FILTER_SIZE,
    PCSS_MAX_FILTER_SIZE
  );

  // STEP 3: filtering
  return PCFWithFilterSize(shadowMap, coords, filterSize);
}
```

与原理对应：

| 代码 | PCSS 步骤 | 说明 |
|------|----------|------|
| `findBlocker(...)` | STEP 1 | 搜索 blocker 平均深度 |
| `avgBlockerDepth < 0.0` | STEP 1 | 没有 blocker，直接可见 |
| `(zReceiver - avgBlockerDepth) / avgBlockerDepth` | STEP 2 | 估算半影比例 |
| `clamp(...)` | STEP 2 | 限制半影半径范围 |
| `PCFWithFilterSize(...)` | STEP 3 | 使用动态半径执行 PCF |

### 修改5：[phongFragment.glsl](src/shaders/phongShader/phongFragment.glsl) — 阴影只衰减直接光照

`blinnPhong()` 改为接收 `visibility`：

```glsl
vec3 blinnPhong(float visibility) {
  ...
  vec3 radiance = ambient + visibility * (diffuse + specular);
  vec3 phongColor = pow(radiance, vec3(1.0 / 2.2));
  return phongColor;
}
```

主函数中：

```glsl
vec3 phongColor = blinnPhong(visibility);
gl_FragColor = vec4(phongColor, 1.0);
```

这样环境光不会被阴影完全压暗，阴影区域仍保留基础亮度。

### 修改6：[DirectionalLight.js](src/lights/DirectionalLight.js) — 光源正交投影调优

为了提升 Shadow Map 有效精度，将光源投影范围从较宽的范围收紧到当前场景覆盖区域：

```js
mat4.ortho(projectionMatrix, -120, 120, -70, 110, 40, 240);
```

原因：

- 当前场景主要包含两个 Mary 模型和地板
- 原来的 far 范围过大，深度精度浪费较多
- 收紧 near/far 和上下范围后，Shadow Map 的有效深度精度更高

### 修改7：阴影模式切换

`main()` 中保留三种模式，截图时通过注释切换：

```glsl
// visibility = useShadowMap(uShadowMap, vec4(shadowCoord, 1.0));  // 任务1：硬阴影
visibility = PCF(uShadowMap, vec4(shadowCoord, 1.0));              // 任务2：PCF
// visibility = PCSS(uShadowMap, vec4(shadowCoord, 1.0));          // 任务3：PCSS
```

展示 PCSS 时切换为：

```glsl
// visibility = useShadowMap(uShadowMap, vec4(shadowCoord, 1.0));
// visibility = PCF(uShadowMap, vec4(shadowCoord, 1.0));
visibility = PCSS(uShadowMap, vec4(shadowCoord, 1.0));
```

切换后需要在浏览器中使用 `Ctrl + Shift + R` 强制刷新，避免浏览器缓存旧的 GLSL 文件。

---

## 三、任务3完成标准

- [x] 实现 `findBlocker()`，能够搜索 blocker 并计算平均 blocker depth
- [x] 实现 `PCSS()` 三个步骤：blocker search、penumbra estimation、variable-size PCF
- [x] 保留任务2的固定半径 `PCF()`，便于对比截图
- [x] 接触处阴影较硬，远离遮挡物处半影更宽
- [x] 阴影只衰减直接光照，环境光不被整体压黑
- [x] 保留硬阴影、PCF、PCSS 三种模式切换方式
- [x] Shadow Map 右下角小窗可视化
- [x] Blocker 搜索区域红绿色标可视化

## 四、调试方向

| 现象 | 可能原因 | 修复 |
|------|---------|------|
| PCSS 看起来和 PCF 差不多 | `LIGHT_SIZE_UV` 太小，动态半影不明显 | 适当增大 `LIGHT_SIZE_UV` 或 `PCSS_MAX_FILTER_SIZE` |
| 阴影边缘过糊 | `PCSS_MAX_FILTER_SIZE` 太大 | 减小 `PCSS_MAX_FILTER_SIZE` |
| 接触阴影太软 | `PCSS_MIN_FILTER_SIZE` 太大 | 减小 `PCSS_MIN_FILTER_SIZE` |
| 阴影噪点明显 | 采样数不足或 Poisson 随机变化明显 | 增大 `NUM_SAMPLES`，但注意性能 |
| 页面卡顿或刷新不稳定 | 8192 Shadow Map + PCSS 多采样开销较大 | 减小 `NUM_SAMPLES` 或 Shadow Map 分辨率 |
| 物体不显示 | GLSL 切换时三行 visibility 都被注释，或 shader 编译失败 | 确保三种模式只启用一行，并检查浏览器控制台 |
| 修改 GLSL 后效果没变 | 浏览器缓存旧 shader 文件 | 使用 `Ctrl + Shift + R` 强制刷新 |
| shadow acne 条纹 | bias 太小 | 增大 `SHADOW_BIAS` |
| 阴影漂浮 Peter Panning | bias 太大 | 减小 `SHADOW_BIAS` |

---

## 五、额外加分：调试可视化

### 5.1 Shadow Map 可视化（右下角小窗）

**功能**：在画面右下角 25%×25% 区域叠加 Shadow Map 灰度图，实时观察深度缓冲。

**实现**（`phongFragment.glsl` main() 开头）：

```glsl
if (uDebugShowShadowMap == 1) {
  if (gl_FragCoord.x > uScreenWidth * 0.75 && gl_FragCoord.y < uScreenHeight * 0.25) {
    vec2 debugUV = ...
    if (边缘) { 黄色边框; return; }
    float depth = unpack(texture2D(uShadowMap, debugUV));
    gl_FragColor = vec4(vec3(depth), 1.0);
    return;
  }
}
```

**涉及文件**：

| 文件 | 改动 |
|------|------|
| `phongFragment.glsl` | 叠加逻辑 + 黄色边框 |
| `PhongMaterial.js` | 新增 `uDebugShowShadowMap`, `uScreenWidth`, `uScreenHeight` uniforms |
| `WebGLRenderer.js` | 每帧从 `window.debugShowShadowMap` 更新 debug uniforms |
| `engine.js` | dat.gui Debug 面板 → "Show Shadow Map" 复选框 |

### 5.2 Blocker 搜索可视化（红绿色标）

**功能**：实时显示每个片元周围的 blocker 密度。绿色 = 无遮挡物，红色 = 大量遮挡物，中间呈黄/橙渐变。

**原理**：在 blinnPhong 着色后，运行一次 blocker 搜索（与 PCSS 的 Step 1 相同），统计 blocke
r 比例，用 `mix(绿, 红, ratio)` 插值颜色乘到 `phongColor` 上。

```glsl
if (uDebugShowBlocker == 1) {
  poissonDiskSamples(shadowCoord.xy);
  int blockerCount = 0;
  for (...) { 统计 blocker }
  float ratio = blockerCount / float(BLOCKER_SEARCH_NUM_SAMPLES);
  vec3 debugColor = mix(vec3(0,1,0), vec3(1,0,0), ratio);
  phongColor *= debugColor;
}
```

**GUI 控制**：dat.gui Debug 面板 → "Show Blocker Search" 复选框。

### 5.3 使用方式

1. 浏览器打开页面
2. 右上角 dat.gui → **Debug** 文件夹
3. 勾选 "Show Shadow Map" → 右下角显示 Shadow Map 灰度图
4. 勾选 "Show Blocker Search" → 场景中绿色=直接光照区域，红色=被遮挡区域

两个开关可以同时开启，互不影响。

