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
├── images/                 # 报告截图（基础阴影结果 + Blocker 可视化）
├── lib/                    # 第三方库（three.js, gl-matrix 等）
├── 实时阴影任务大纲.md      # 原始实现计划
├── 任务1_ShadowMap硬阴影.md # 任务1 原理 + 实现归档
├── 任务2_PCF软阴影.md       # 任务2 原理 + 实现归档
├── 任务3_PCSS软阴影.md      # 任务3 原理 + 实现归档
├── 额外任务_多光源与移动光源.md # 额外任务原理 + 实现归档
└── 说明.pdf                # 作业说明文档
```

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
| 鼠标左键拖拽 | 旋转相机 |
| 滚轮 | 缩放 |
| 鼠标右键拖拽 | 平移相机 |
| Shadow Mode | 在 `PCF`、`PCSS`、`Hard` 三种阴影模式之间实时切换 |
| Show Shadow Map | 在右下角显示 Shadow Map 灰度小窗 |
| Show Blocker Search | 显示 Blocker 搜索红绿色标可视化 |
| Animate Light | 开启/关闭移动光源动画 |
| Animate Model | 开启/关闭动态模型自转和平动 |

## 当前参数

| 参数 | 值 | 位置 |
|------|-----|------|
| Shadow Map 分辨率 | 8192×8192 | `engine.js` |
| 光源位置 | (0, 80, 80) | `engine.js` |
| 正交投影范围 | left/right=±120, bottom=-70, top=110, near=40, far=240 | `DirectionalLight.js` |
| PCF/PCSS 采样数 | 40 | `phongFragment.glsl` |
| Shadow bias | 0.012 | `phongFragment.glsl` |
| PCF filterSize | 0.0035 | `phongFragment.glsl` |
| PCSS blocker search size | 0.0045 | `phongFragment.glsl` |
| PCSS light size | 0.007 | `phongFragment.glsl` |
| PCSS filterSize 范围 | 0.0008 ~ 0.009 | `phongFragment.glsl` |
| 纹理 wrap 模式 | CLAMP_TO_EDGE | `FBO.js` |

## 切换阴影模式

页面右上角提供 dat.gui 控制面板，可通过 `Shadow Mode` 下拉框在三种模式之间实时切换，无需修改 shader 或刷新页面：

| 模式 | 说明 |
|------|------|
| `PCF` | 固定滤波半径软阴影，边缘平滑，默认模式 |
| `PCSS` | 基于 blocker search 的动态半影软阴影，接触处较硬、远离遮挡物处较软 |
| `Hard` | 基础 Shadow Map 硬阴影，用于观察原始遮挡关系 |

调试时可同时打开 `Show Shadow Map` 查看右下角深度图小窗，或打开 `Show Blocker Search` 查看 blocker 搜索区域的红绿色标。`Animate Light` 和 `Animate Model` 可分别控制移动光源和动态模型动画，便于截图或对比不同阴影模式。
