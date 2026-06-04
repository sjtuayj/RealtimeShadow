# 实时阴影答辩 PPT 内容与图片清单

建议做 12 页，逻辑从“为什么需要阴影”到“怎么实现、怎么验证、扩展了什么”。

## 1. 标题页：WebGL 实时阴影渲染

讲：项目实现 Two-Pass Shadow Map、PCF、PCSS，并扩展 Shadow Map/Blocker 可视化、双光源、移动光源和动态模型。

贴图：`PPT逻辑图/00_imagegen_shadow_concept.png` 作为背景或右侧主视觉。

## 2. 问题背景：局部光照为什么不够

讲：Blinn-Phong 只能算表面明暗，不能表达物体之间“谁挡住谁”；实时路径追踪代价高，所以使用 Shadow Map。

贴图：可以放一张最终场景截图 `images/PCSS_shadow.png`，旁边用一句话说明“阴影表达空间遮挡关系”。

## 3. Shadow Map 两趟算法

讲：Shadow Pass 从光源视角写入最近深度；Camera Pass 从相机视角把片元变换到光源空间并与 Shadow Map 比较。

贴图：优先用 `PPT逻辑图/imagegen_academic_02_two_pass_shadowmap.png`。若需要极简矢量备用，再用 `PPT逻辑图/01_shadowmap_two_pass.svg`。

## 4. Light MVP 与深度编码

讲：`uLightMVP = Projection × View × Model`；方向光使用正交投影；WebGL1 用 RGBA 打包 `gl_FragCoord.z`，Camera Pass 再 unpack。

贴图：可用 `PPT逻辑图/imagegen_academic_01_overall_pipeline.png` 中的整体管线部分，或备用 `PPT逻辑图/02_light_mvp_depth_pack.svg`。

## 5. 硬阴影与 Bias

讲：硬阴影就是一次深度比较；`SHADOW_BIAS = 0.012` 用来缓解 shadow acne，但过大会 Peter Panning。

贴图：`images/SM_shadow.png`，可额外截一张有硬边/锯齿的局部放大图。公式可直接贴：

```text
visibility = d_receiver - bias > d_map(x,y) ? 0.0 : 1.0
```

## 6. PCF：固定半径软化边缘

讲：PCF 在 UV 邻域里做 40 次 Poisson 圆盘采样，每次做 shadow test，最后平均成连续 visibility。

贴图：`PPT逻辑图/imagegen_academic_03_pcf_pipeline.png` 和 `images/PCF_shadow.png`。

## 7. PCSS：动态半影

讲：PCSS 比 PCF 多两步：先找 blocker 平均深度，再用 receiver 和 blocker 的深度差估算半影，最后调用动态半径 PCF。

贴图：`PPT逻辑图/imagegen_academic_04_pcss_pipeline.png` 和 `images/PCSS_shadow.png`。

## 8. 调试可视化：Shadow Map 小窗 + Blocker Search

讲：Shadow Map 小窗用于确认 FBO、深度打包、光源投影是否正常；Blocker Search 红绿色标显示邻域遮挡比例，帮助解释 PCSS 的 blocker 阶段。

贴图：`PPT逻辑图/imagegen_academic_06_dynamic_debug_pipeline.png` 的右侧调试可视化部分；再贴 `images/SM_blocker_debug.png`、`images/PCF_blocker_debug.png`、`images/PCSS_blocker_debug.png` 三图横向对比。

## 9. 多光源架构

讲：每个光源都有独立 FBO；逐光源执行 Shadow Pass 和 Camera Pass；第一个 pass 加 ambient，后续光源使用 `gl.blendFunc(ONE, ONE)` 叠加直接光照。

贴图：`PPT逻辑图/imagegen_academic_05_multilight_pipeline.png`。

## 10. 动态光源与动态模型

讲：Light 1 按圆轨道更新位置，小 Mary 做公转和自转；由于光源和模型都在变，每帧都要重新计算 Shadow Pass 和 Camera Pass 的 `uLightMVP`。

贴图：`PPT逻辑图/imagegen_academic_06_dynamic_debug_pipeline.png` 的左侧动态更新循环；如果可以录屏，建议放 5 到 8 秒 GIF 或视频。

## 11. 三种方法结果对比

讲：硬阴影用于验证基础管线；PCF 解决锯齿但半影固定；PCSS 更像面积光，接触处硬、远处软，但更耗性能。

贴图：三列贴 `images/SM_shadow.png`、`images/PCF_shadow.png`、`images/PCSS_shadow.png`；方法原理图可回看 `PPT逻辑图/imagegen_academic_02_two_pass_shadowmap.png`、`PPT逻辑图/imagegen_academic_03_pcf_pipeline.png`、`PPT逻辑图/imagegen_academic_04_pcss_pipeline.png`。

## 12. 总结与可改进方向

讲：已完成 Shadow Map、PCF、PCSS、调试可视化、多光源和动画；关键工程点是 lightMVP、深度 pack/unpack、bias、采样越界和性能质量平衡。

贴图：放参数表或最终 `images/PCSS_shadow.png`。可改进方向：更稳定采样序列、降低 Shadow Map 显存开销、时间累积降噪。

## 可直接贴出的核心参数

## 本次 imagegen 生成的中文论文风格 Pipeline 图

| 图 | 文件 | 建议使用页 |
|---|---|---|
| 整体渲染管线 | `PPT逻辑图/imagegen_academic_01_overall_pipeline.png` | 第 3/4 页 |
| Two-Pass Shadow Map | `PPT逻辑图/imagegen_academic_02_two_pass_shadowmap.png` | 第 3/5 页 |
| PCF 固定半径软阴影 | `PPT逻辑图/imagegen_academic_03_pcf_pipeline.png` | 第 6 页 |
| PCSS 动态半影 | `PPT逻辑图/imagegen_academic_04_pcss_pipeline.png` | 第 7 页 |
| 多光源叠加 | `PPT逻辑图/imagegen_academic_05_multilight_pipeline.png` | 第 9 页 |
| 动态更新与调试可视化 | `PPT逻辑图/imagegen_academic_06_dynamic_debug_pipeline.png` | 第 8/10 页 |

| 参数 | 值 | 说明 |
|---|---:|---|
| Shadow Map 分辨率 | 8192 × 8192 | 每个光源独立 FBO |
| `SHADOW_BIAS` | 0.012 | 缓解多光源下自遮挡 |
| `NUM_SAMPLES` | 40 | PCF/PCSS 采样数 |
| `PCF_FILTER_SIZE` | 0.0035 | PCF 固定滤波半径 |
| `BLOCKER_SEARCH_SIZE` | 0.0045 | PCSS blocker 搜索半径 |
| `LIGHT_SIZE_UV` | 0.007 | 模拟面积光大小 |
| `PCSS_MIN/MAX_FILTER_SIZE` | 0.0008 / 0.009 | 动态半影范围 |
| Light 0 | 3000, 暖色, (0,80,80) | 固定主光 |
| Light 1 | 2500, 冷色, 轨道半径 100 | 移动补光 |

## 答辩时建议强调的代码对应关系

| 内容 | 代码位置 |
|---|---|
| Light MVP | `src/lights/DirectionalLight.js` |
| Shadow Pass 深度写入 | `src/shaders/shadowShader/shadowVertex.glsl`, `shadowFragment.glsl` |
| 硬阴影深度比较 | `src/shaders/phongShader/phongFragment.glsl::useShadowMap()` |
| PCF | `PCFWithFilterSize()`, `PCF()` |
| PCSS | `findBlocker()`, `PCSS()` |
| 多光源叠加 | `src/renderers/WebGLRenderer.js::render()` |
| 动态光源/模型 | `src/engine.js::mainLoop()` |
| Shadow Map 小窗 | `src/shaders/DebugShader.js` |
