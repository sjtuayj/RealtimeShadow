# RealtimeShadow — WebGL 实时阴影

基于 GAMES202 框架实现的 WebGL 实时阴影项目，使用 Two-Pass Shadow Map 技术，逐步实现硬阴影、PCF 软阴影和 PCSS。

## 项目结构

```
.
├── index.html              # 入口页面
├── src/
│   ├── engine.js           # 主程序：初始化 GL/Camera/Renderer/Light，加载模型
│   ├── renderers/
│   │   ├── WebGLRenderer.js    # 渲染循环：Shadow Pass → Camera Pass
│   │   └── MeshRender.js       # 单 Mesh 绘制，管理 FBO 切换
│   ├── lights/
│   │   └── DirectionalLight.js # 平行光 + CalcLightMVP()
│   ├── shaders/
│   │   ├── phongShader/        # Phong 着色器（含阴影采样函数）
│   │   ├── shadowShader/       # Shadow Pass 着色器
│   │   ├── Shader.js           # Shader 编译/链接
│   │   └── InternalShader.js   # 光源 Cube 着色器
│   ├── materials/
│   │   ├── PhongMaterial.js    # 相机 Pass 材质
│   │   └── ShadowMaterial.js   # Shadow Pass 材质
│   ├── textures/
│   │   └── FBO.js              # Shadow Map Framebuffer（8192×8192）
│   ├── loads/
│   │   └── loadOBJ.js          # OBJ/MTL 加载器
│   └── objects/
│       └── Mesh.js             # 网格数据
├── assets/                 # 模型资源（Mary + 地板）
├── lib/                    # 第三方库（three.js, gl-matrix 等）
├── 实时阴影任务大纲.md      # 原始实现计划
├── 任务1_ShadowMap硬阴影.md # 任务1 原理 + 实现归档
├── 任务2_PCF软阴影.md       # 任务2 原理 + 实现归档
├── 任务3_PCSS软阴影.md      # 任务3 原理 + 实现归档
└── 说明.pdf                # 作业说明文档
```

## 任务进度

### 已实现

| 任务 | 状态 | 关键文件 | 归档文档 |
|------|------|---------|---------|
| 基础场景跑通 | ✅ | `engine.js` | — |
| **任务1：Shadow Map 硬阴影** | ✅ | `DirectionalLight.js`, `phongFragment.glsl`, `WebGLRenderer.js`, `FBO.js` | [任务1_ShadowMap硬阴影.md](任务1_ShadowMap硬阴影.md) |
| **任务2：PCF 软阴影** | ✅ | `phongFragment.glsl`, `FBO.js` | [任务2_PCF软阴影.md](任务2_PCF软阴影.md) |
| **任务3：PCSS** | ✅ | `phongFragment.glsl` (`findBlocker`, `PCSS`, `PCFWithFilterSize`) | [任务3_PCSS软阴影.md](任务3_PCSS软阴影.md) |
| 截图和提交整理 | ✅ | `images/` | [images](./images) |

### 待实现

1. **截图和提交整理**
   - 新建 `images/` 文件夹
   - 分别截取硬阴影、PCF、PCSS 效果图
   - 提交时删除 `/lib` 和 `/assets`

## 快速开始

### VS Code
安装 `Live Server` 插件，右键 `index.html` → Open with Live Server。

### 命令行
```bash
# 安装
npm install http-server -g

# 在项目根目录运行
http-server . -p 8000 -c-1
```

然后浏览器打开 `http://127.0.0.1:8000`。

### 注意事项
- 使用 `-c-1` 禁用缓存，否则 GLSL 修改后可能不生效
- 如遇模型不显示，强制刷新（Ctrl+Shift+R）并检查浏览器控制台报错

## 操作说明

| 操作 | 功能 |
|------|------|
| 鼠标右键拖拽 | 旋转相机 |
| 滚轮 | 缩放 |
| 鼠标左键拖拽 | 平移相机 |

## 当前参数

| 参数 | 值 | 位置 |
|------|-----|------|
| Shadow Map 分辨率 | 8192×8192 | `engine.js` |
| 光源位置 | (0, 80, 80) | `engine.js` |
| 正交投影范围 | left/right=±120, bottom=-70, top=110, near=40, far=240 | `DirectionalLight.js` |
| PCF/PCSS 采样数 | 40 | `phongFragment.glsl` |
| Shadow bias | 0.004 | `phongFragment.glsl` |
| PCF filterSize | 0.0035 | `phongFragment.glsl` |
| PCSS blocker search size | 0.0045 | `phongFragment.glsl` |
| PCSS light size | 0.007 | `phongFragment.glsl` |
| PCSS filterSize 范围 | 0.0008 ~ 0.009 | `phongFragment.glsl` |
| 纹理 wrap 模式 | CLAMP_TO_EDGE | `FBO.js` |

## 切换阴影模式

在 `src/shaders/phongShader/phongFragment.glsl` 的 `main()` 中切换注释：

```glsl
// visibility = useShadowMap(uShadowMap, vec4(shadowCoord, 1.0));  // 任务1：硬阴影
visibility = PCF(uShadowMap, vec4(shadowCoord, 1.0));              // 任务2：PCF
// visibility = PCSS(uShadowMap, vec4(shadowCoord, 1.0));          // 任务3：PCSS
```

每次切换阴影模式后，请在浏览器中使用 `Ctrl + Shift + R` 强制刷新，避免浏览器缓存旧的 GLSL 文件。
