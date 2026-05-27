# 任务1：Shadow Map 硬阴影

## 一、原理

### 1.1 Two-Pass Shadow Map

实时阴影的核心技术是 **Two-Pass Shadow Map**（两趟阴影贴图）：

**Pass 1 — Shadow Pass（光源视角）**：把相机"放到"光源位置，渲染整个场景，不计算颜色，只记录每个片元到光源的最近深度 → 写入一张纹理（Shadow Map）。

**Pass 2 — Camera Pass（相机视角）**：回到正常相机视角渲染场景。对于每个片元：
1. 用之前构建的 `lightMVP` 矩阵算出它在光源空间的坐标
2. 从 Shadow Map 采样出"光源看到的最近深度"
3. 比较：当前片元深度 > Shadow Map深度 → 有东西挡在前面 → 阴影中



光源 ----------→ 遮挡物 ----------→ 接收面（阴影中）
       │                              │
       └→ SM深度 = 遮挡物深度          └→ 当前深度 > SM深度 → shadow


### 1.2 三个矩阵：lightMVP

要把世界空间中的顶点映射到光源的裁剪空间，需要三个矩阵连乘：

```
lightMVP = Projection × View × Model
```

| 矩阵 | 作用 | 对应代码 |
|------|------|---------|
| **Model** | 模型空间 → 世界空间 | `translate(translate) × scale(scale)` |
| **View** | 世界空间 → 光源观察空间 | `lookAt(lightPos, focalPoint, lightUp)` |
| **Projection** | 光源空间 → 裁剪空间 | `ortho(-100,100, -100,100, 1,200)` |

为什么平行光用**正交投影**（`ortho`）而不是透视？因为平行光的光线是平行的，没有"近大远小"的透视效果。正交投影用一个立方体裁剪区域，投影矩阵将立方体映射到 NDC（归一化设备坐标）。

```
顶点(模型空间) → Model → 世界空间 → View → 光源视角 → Projection → 裁剪空间 [-1,1]³
                                                                  ↓
                                                    存入 Shadow Map (深度)
```

### 1.3 深度比较

**Shader 端**（`useShadowMap`）：

```
1. shadowCoord = vPositionFromLight.xyz / vPositionFromLight.w   // 透视除法
2. shadowCoord = shadowCoord * 0.5 + 0.5                          // NDC [-1,1] → UV [0,1]
3. closestDepth = unpack(texture2D(shadowMap, shadowCoord.xy))   // 采样 SM 最近深度
4. currentDepth = shadowCoord.z                                   // 当前片元深度
5. return currentDepth - bias > closestDepth ? 0.0(阴影) : 1.0(可见)
```

**深度打包/解包**：Shadow Map 用 RGBA 四个通道存储深度值（32位），提高精度。

- `pack()`：`float depth → vec4 RGBA`，把浮点深度拆成4个字节存储
- `unpack()`：`vec4 RGBA → float depth`，还原深度值

### 1.4 Shadow Acne 与 Bias

**Shadow Acne（阴影痤疮）**：由于 Shadow Map 分辨率有限，一个texel覆盖了场景中的多个片元。当片元深度恰好接近SM记录的深度时，浮点精度误差导致"自己遮挡自己"——表面上出现条纹状伪影。

**Bias 解决方案**：在深度比较时加一个偏移量，`currentDepth - bias > closestDepth`。相当于把当前片元往光源方向"推"一点点，避免自遮挡。当前 `bias = 0.005`。

### 1.5 数据流总览

```
engine.js 加载模型
  └→ loadOBJ.js:
       ├→ PhongMaterial(lightMVP) → renderer.meshes[]        ← Pass 2 用
       └→ ShadowMaterial(lightMVP) → renderer.shadowMeshes[]  ← Pass 1 用

每帧 WebGLRenderer.render():
  ├→ gl.clear(主帧缓冲)
  ├→ bind light.fbo → gl.clear(FBO) → 遍历 shadowMeshes
  │      └→ shadowVertex.glsl: gl_Position = uLightMVP × pos
  │      └→ shadowFragment.glsl: pack(gl_FragCoord.z) → RGBA
  │
  └→ 遍历 meshes
         └→ phongVertex.glsl: vPositionFromLight = uLightMVP × pos
         └→ phongFragment.glsl: useShadowMap() → visibility → × phongColor
```

---

## 二、代码修改

共修改 **3 个文件**。

### 修改1：[DirectionalLight.js](data/src/lights/DirectionalLight.js) — `CalcLightMVP()`

**位置**：第 18-33 行

**改动**：从空壳函数（只创建矩阵不做计算）填充为完整实现。

```js
// Model transform
mat4.identity(modelMatrix);
mat4.translate(modelMatrix, modelMatrix, translate);
mat4.scale(modelMatrix, modelMatrix, scale);

// View transform
mat4.lookAt(viewMatrix, this.lightPos, this.focalPoint, this.lightUp);

// Projection transform
mat4.ortho(projectionMatrix, -100, 100, -100, 100, 1, 200);

mat4.multiply(lightMVP, projectionMatrix, viewMatrix);
mat4.multiply(lightMVP, lightMVP, modelMatrix);
```

**与原理对应**：

| 代码 | 原理章节 | 说明 |
|------|---------|------|
| `translate + scale` | 1.2 Model矩阵 | 将模型从局部空间平移到世界空间位置 |
| `lookAt(lightPos, focalPoint, lightUp)` | 1.2 View矩阵 | 从光源位置"看"场景中心，定义光源观察坐标系 |
| `ortho(-100,100, -100,100, 1,200)` | 1.2 Projection矩阵 | 平行光用正交投影，200×200×199 立方体裁剪区域 |
| `P × V × M` | 1.2 连乘顺序 | 右乘规则：顶点先乘M→再乘V→再乘P，代码中 `P×(V×M)` = `P×V×M` |

**正交投影范围说明**：场景中 Mary 模型缩放 20×20×20，光源在 `(0, 80, 80)`，地板在 `z=-30`。`left/right/bottom/top = ±100` 确保所有物体都在光源视野内，`near=1, far=200` 覆盖光源到最远物体的距离。

### 修改2：[phongFragment.glsl](data/src/shaders/phongShader/phongFragment.glsl) — `useShadowMap()`

**位置**：第 107-121 行

**改动**：从 `return 1.0`（无阴影）替换为完整的深度比较逻辑。

```glsl
float useShadowMap(sampler2D shadowMap, vec4 shadowCoord){
  vec3 projCoords = shadowCoord.xyz;

  // ① 边界检查
  if (projCoords.x < 0.0 || projCoords.x > 1.0 ||
      projCoords.y < 0.0 || projCoords.y > 1.0 ||
      projCoords.z < 0.0 || projCoords.z > 1.0) {
    return 1.0;
  }

  // ② 采样 Shadow Map + 深度比较
  float closestDepth = unpack(texture2D(shadowMap, projCoords.xy));
  float currentDepth = projCoords.z;
  float bias = 0.005;

  // ③ 判断遮挡
  return currentDepth - bias > closestDepth ? 0.0 : 1.0;
}
```

**与原理对应**：

| 代码 | 原理章节 | 说明 |
|------|---------|------|
| 边界检查 `[0,1]` | 1.3 | 超出 Shadow Map 范围的片元默认可见，不做比较 |
| `unpack(texture2D(...))` | 1.3 深度解包 | 从 RGBA 四通道还原32位深度值 |
| `currentDepth - bias > closestDepth` | 1.4 Shadow Acne | bias 偏移避免自遮挡条纹 |
| 返回 `0.0` / `1.0` | 1.3 深度比较 | 0.0=被遮挡(阴影)，1.0=可见(光亮) |

### 修改3：[WebGLRenderer.js](data/src/renderers/WebGLRenderer.js) — FBO 清理

**位置**：第 23、37-39 行

**改动**：
1. 主渲染循环开头增加 `gl.clear(COLOR_BUFFER_BIT | DEPTH_BUFFER_BIT)`
2. Shadow Pass 前绑定 FBO 并清空

```js
// 新增：清理主帧缓冲
gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

// 新增：Shadow Pass 前清理 FBO
gl.bindFramebuffer(gl.FRAMEBUFFER, this.lights[l].entity.fbo);
gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
```

**与原理对应**：FBO 不会被浏览器自动清理（只有 canvas 默认帧缓冲才会）。如果不清理 FBO，上一帧的深度数据残留，Shadow Map 内容错误 → 阴影位置偏移或全黑。对应原理 1.1 Shadow Pass，每次从光源渲染前必须清空上一帧的深度缓冲。

---

## 三、任务1完成标准

- [x] Mary 模型能在地板上投下硬阴影
- [x] 两个 Mary 之间的遮挡关系正确
- [x] 阴影方向与光源方向一致（光源在 `(0,80,80)` → 阴影投向前下方）
- [x] 阴影边缘可以有锯齿（硬阴影正常现象，留给 PCF 解决）
- [x] 不要求软阴影效果

## 四、调试方向

| 现象 | 可能原因 | 排查方法 |
|------|---------|---------|
| 全黑 | lightMVP 矩阵顺序错误或正交范围不覆盖场景 | 检查 `P×V×M` 连乘顺序，增大 ortho 范围 |
| 完全无阴影 | `useShadowMap()` 始终返回 1.0 | 检查 shadowCoord 是否在 [0,1] 内，正交范围是否过大 |
| 阴影位置偏移 | modelMatrix 与正常 Pass 不一致 | 确认 `loadOBJ.js` 中传入的 translate/scale 相同 |
| shadow acne（条纹） | bias 太小 | 增大 bias 到 0.01，或改用基于法线的动态 bias |
| 阴影缺失/破碎 | FBO 未清理 | 确认 Shadow Pass 前有 `gl.clear()` |
| 深度比较方向反了 | 0/1 颠倒 | 检查是 `> closestDepth` 还是 `< closestDepth` |
