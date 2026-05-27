# 任务2：PCF（Percentage Closer Filtering）软阴影

## 一、原理

### 1.1 硬阴影的局限

任务1的 `useShadowMap()` 对每个片元只做 **一次** 深度比较：

```
shadowTest(uv) = currentDepth - bias > shadowMapDepth ? 0.0 : 1.0
```

结果是二值的（0 或 1），阴影边缘呈现锯齿状阶梯过渡。这是因为 shadow map 分辨率有限，一个像素不可能"半遮挡"——要么被挡住，要么完全可见。

### 1.2 PCF 核心思路

**做多次比较，取平均。** 不是只在片元中心位置采样一次，而是在周围分布 N 个采样点，每个点独立做 shadow test，最后取平均：

```
visibility = (1/N) * Σᵢ shadowTest(uv + offsetᵢ × filterSize)
```

| | 硬阴影 | PCF |
|---|---|---|
| 采样点 | 1 个 | N 个（Poisson 圆盘分布） |
| shadow test 次数 | 1 次 | N 次 |
| 结果 | 0 或 1 | 0.0 ~ 1.0 连续值 |
| 阴影边缘 | 锯齿二值 | 柔化渐变 |

### 1.3 为什么用 Poisson 圆盘采样

三种常见采样策略对比：

- **纯随机**：样本会扎堆（clumping），产生噪点
- **规则网格**：产生明显的条带状伪影（banding artifacts）
- **Poisson 圆盘**：任意两个样本之间保持最小距离，分布均匀但不规则 → **柔化效果最自然**

代码中已有的 `poissonDiskSamples()` 生成 N=20 个分布在单位圆盘内的 Poisson 样本点，每个点与 `filterSize` 相乘后作为 UV 偏移量。

### 1.4 filterSize 参数

`filterSize` 控制圆盘采样半径（UV 空间）：

- `filterSize` 小 → 采样集中在片元附近 → 过渡窄 → 阴影边缘较硬
- `filterSize` 大 → 采样分布更广 → 过渡宽 → 阴影边缘更软

当前 shadow map 分辨率 8192×8192，正交投影范围 200×200：
- 1 个 texel = `1/8192 ≈ 0.00012` UV 单位
- `filterSize = 0.005` ≈ 41 个 texel 半径，产生肉眼可见的柔化

### 1.5 数据流

```
片元 shadowCoord
  │
  ├→ 边界检查（超出 [0,1] → 可见）
  │
  ├→ poissonDiskSamples(shadowCoord.xy)  // 用片元坐标作为随机种子
  │      └→ 填满 poissonDisk[0..19]
  │
  ├→ for i in 0..PCF_NUM_SAMPLES:
  │      offset = poissonDisk[i] × filterSize
  │      sampleUV = uv + offset
  │      ├→ sampleUV 越界？ → visibility += 1.0（跳过）
  │      └→ 正常：depth = unpack(texture2D(shadowMap, sampleUV))
  │              result = (currentDepth - bias > depth) ? 0.0 : 1.0
  │              visibility_sum += result
  │
  └→ return visibility_sum / PCF_NUM_SAMPLES
```

---

## 二、代码修改

共修改 **3 个文件**。

### 修改1：[phongFragment.glsl](src/shaders/phongShader/phongFragment.glsl) — 实现 `PCF()` 函数体

**位置**：第 90-92 行，原 `return 1.0` 替换为完整多采样逻辑

**改动与原理对应**：

```glsl
// ① 边界检查（与硬阴影相同）
if (projCoords 超出 [0,1]) return 1.0;
```
→ 对应原理 1.5：片元落在 shadow map 范围外，视为可见，不参与计算。

```glsl
// ② 生成 Poisson 圆盘采样点
poissonDiskSamples(projCoords.xy);
```
→ 对应原理 1.3：用片元 UV 作为随机种子，生成 20 个均匀分布但不规则的采样偏移。

```glsl
// ③ 遍历 N 个采样点，逐个做 shadow test
for (int i = 0; i < PCF_NUM_SAMPLES; i++) {
    vec2 offset = poissonDisk[i] * filterSize;
    float closestDepth = unpack(texture2D(shadowMap, projCoords.xy + offset));
    visibility += currentDepth - bias > closestDepth ? 0.0 : 1.0;
}
```
→ 对应原理 1.2 和 1.4：
- `poissonDisk[i] * filterSize`：将单位圆盘样本缩放到指定 UV 半径
- `projCoords.xy + offset`：在片元周围偏移采样，而不是只采中心
- 每个采样点独立做深度比较，累加二值结果

```glsl
// ④ 取平均
return visibility / float(PCF_NUM_SAMPLES);
```
→ 对应原理 1.2 核心公式：N 次 shadow test 取平均 → 0.0~1.0 连续值

**当前参数**：
| 参数 | 值 | 说明 |
|------|-----|------|
| `PCF_NUM_SAMPLES` | 20 | 每片元采样次数 |
| `filterSize` | 0.005 | UV 空间采样半径（≈41 texels @8192） |
| `bias` | 0.005 | 深度偏移防止 shadow acne |

### 修改2：[phongFragment.glsl](src/shaders/phongShader/phongFragment.glsl) — `main()` 切换调用

**位置**：第 154-156 行

```glsl
// visibility = useShadowMap(uShadowMap, vec4(shadowCoord, 1.0));  // 任务1
visibility = PCF(uShadowMap, vec4(shadowCoord, 1.0));              // 任务2 ← 当前
```

将活跃调用从硬阴影切换到 PCF。任务1 的调用保留注释，方便后续对比切换。

### 修改3：[FBO.js](src/textures/FBO.js) — Shadow Map 纹理加 `CLAMP_TO_EDGE`

**位置**：第 30-31 行之后

**问题**：WebGL 纹理默认 wrap 模式为 `REPEAT`。当 PCF 的采样偏移使 UV 超出 `[0,1]` 范围时，纹理采样会"环绕"到对侧，取到完全错误的深度值 → 地面出现多余阴影层。

**改动**：

```js
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
```

→ `CLAMP_TO_EDGE` 使越界采样被钳制到边缘像素值，不会环绕。

### 修改4：[phongFragment.glsl](src/shaders/phongShader/phongFragment.glsl) — PCF 逐采样点边界检查

**位置**：PCF 函数内采样循环（第 107-110 行）

**问题**：修改3（CLAMP_TO_EDGE）只能防止环绕，但边缘像素的深度值可能不适用于当前片元。在 Shadow Map 边缘区域，钳制的深度值仍可能导致误判。

**改动**：对每个偏移后的 `sampleUV` 单独做边界检查：

```glsl
for (int i = 0; i < PCF_NUM_SAMPLES; i++) {
    vec2 offset = poissonDisk[i] * filterSize;
    vec2 sampleUV = projCoords.xy + offset;
    if (sampleUV.x < 0.0 || sampleUV.x > 1.0 || sampleUV.y < 0.0 || sampleUV.y > 1.0) {
      visibility += 1.0;  // 越界采样点直接视为可见
    } else {
      float closestDepth = unpack(texture2D(shadowMap, sampleUV));
      visibility += currentDepth - bias > closestDepth ? 0.0 : 1.0;
    }
}
```

→ 两层防护：纹理层 `CLAMP_TO_EDGE` + Shader 层逐点越界跳过，彻底消除误采样。

---

## 三、任务2完成标准

- [x] 阴影边缘不再是二值锯齿，呈现柔化过渡
- [x] 阴影方向与光源方向一致
- [x] 接触点附近阴影较硬，远离接触点的边缘较软（filterSize 均匀时整体均匀柔化）
- [x] 不要求 blocker 搜索和自适应半影（留给任务3 PCSS）

## 四、调试方向

| 现象 | 可能原因 | 修复 |
|------|---------|------|
| 阴影边缘太硬、看不出柔化 | `filterSize` 太小 | 增大到 0.003~0.005 |
| 阴影边缘过于模糊 | `filterSize` 太大 | 减小到 0.0005~0.001 |
| 阴影区域有噪点 | `PCF_NUM_SAMPLES` 不够 | 增大到 30~40 |
| shadow acne 加重 | 多采样降低了有效精度 | 增大 `bias` 到 0.01 |
| 性能下降明显 | 采样数 × 片元数过大 | 降低 `PCF_NUM_SAMPLES` 或 shadow map 分辨率 |
| 地面上多出一层异常阴影 | 纹理 `REPEAT` 环绕 + 采样越界 | FBO 加 `CLAMP_TO_EDGE` + PCF 逐点边界检查 |
