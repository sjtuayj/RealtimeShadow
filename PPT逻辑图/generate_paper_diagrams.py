from PIL import Image, ImageDraw, ImageFont
import math
from pathlib import Path

OUT = Path(__file__).parent
W, H = 1920, 1080

BG = "#fbfcff"
INK = "#172033"
MUTED = "#5d6b7c"
LINE = "#cfd8e6"
BLUE = "#2563eb"
CYAN = "#06b6d4"
AMBER = "#f59e0b"
GREEN = "#16a34a"
RED = "#dc2626"
NAVY = "#0f172a"
PANEL = "#ffffff"

FONT = r"C:\Windows\Fonts\simhei.ttf"
ARIAL = r"C:\Windows\Fonts\arial.ttf"
ARIAL_BOLD = r"C:\Windows\Fonts\arialbd.ttf"


def font(size, bold=False):
    path = FONT if bold else FONT
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.truetype(ARIAL_BOLD if bold else ARIAL, size)


def canvas(title, subtitle=None):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for x in range(80, W, 80):
        d.line((x, 150, x, H - 70), fill="#eef2f7", width=1)
    for y in range(180, H, 80):
        d.line((70, y, W - 70, y), fill="#eef2f7", width=1)
    d.text((90, 60), title, font=font(50, True), fill=INK)
    if subtitle:
        d.text((92, 125), subtitle, font=font(27), fill=MUTED)
    return im, d


def shadow_box(d, xy, fill=PANEL, outline=LINE, radius=22, width=3):
    x1, y1, x2, y2 = xy
    d.rounded_rectangle((x1 + 8, y1 + 10, x2 + 8, y2 + 10), radius=radius, fill="#e8edf5")
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def text_center(d, xy, text, size=30, color=INK, bold=False):
    box = d.textbbox((0, 0), text, font=font(size, bold))
    tw, th = box[2] - box[0], box[3] - box[1]
    x1, y1, x2, y2 = xy
    d.text(((x1 + x2 - tw) / 2, (y1 + y2 - th) / 2 - 2), text, font=font(size, bold), fill=color)


def arrow(d, p1, p2, color=BLUE, width=5):
    d.line((*p1, *p2), fill=color, width=width)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    r = 18
    pts = [
        p2,
        (p2[0] - r * math.cos(ang - 0.45), p2[1] - r * math.sin(ang - 0.45)),
        (p2[0] - r * math.cos(ang + 0.45), p2[1] - r * math.sin(ang + 0.45)),
    ]
    d.polygon(pts, fill=color)


def label(d, xy, text, size=25, color=MUTED):
    d.text(xy, text, font=font(size), fill=color)


def pill(d, xy, text, fill, outline, size=28):
    d.rounded_rectangle(xy, radius=18, fill=fill, outline=outline, width=3)
    text_center(d, xy, text, size=size, color=INK, bold=True)


def save(im, name):
    im.save(OUT / name, quality=95)


def diagram_two_pass():
    im, d = canvas("Two-Pass Shadow Map 架构", "Shadow Pass 生成深度纹理，Camera Pass 采样并完成可见性判断")
    shadow_box(d, (95, 210, 560, 760))
    shadow_box(d, (760, 210, 1225, 760))
    shadow_box(d, (1425, 210, 1885, 760))
    text_center(d, (140, 235, 515, 295), "1  Shadow Pass", 34, bold=True)
    text_center(d, (805, 235, 1180, 295), "Shadow Map", 34, bold=True)
    text_center(d, (1470, 235, 1840, 295), "2  Camera Pass", 34, bold=True)
    pill(d, (170, 365, 485, 450), "Light View", "#fff7e6", AMBER)
    pill(d, (170, 510, 485, 595), "Depth Only", "#eaf2ff", BLUE)
    for i in range(10):
        shade = int(235 - i * 14)
        d.rectangle((855 + i * 34, 390, 889 + i * 34, 600), fill=(shade, shade, shade), outline="#d1d5db")
    d.rounded_rectangle((845, 380, 1195, 610), radius=14, outline=CYAN, width=5)
    pill(d, (1500, 340, 1810, 425), "Project to Light", "#eaf2ff", BLUE)
    pill(d, (1500, 500, 1810, 585), "Depth Compare", "#ecfdf5", GREEN)
    arrow(d, (560, 480), (760, 480))
    arrow(d, (1225, 480), (1425, 480))
    shadow_box(d, (355, 835, 1565, 975), fill="#f8fafc")
    text_center(d, (385, 850, 1535, 910), "visibility = d_receiver - bias > d_map(x,y) ? 0 : 1", 34, color=NAVY, bold=True)
    label(d, (510, 925), "对应代码：shadowFragment.glsl pack(depth)  →  phongFragment.glsl unpack() / useShadowMap()", 25)
    save(im, "paper_01_two_pass_shadowmap.png")


def diagram_mvp_pack():
    im, d = canvas("Light MVP 与深度打包", "同一套光源空间变换连接 Shadow Pass 与 Camera Pass")
    xs = [135, 500, 865, 1230]
    names = ["Model", "View", "Projection", "Light MVP"]
    subs = ["T × S", "lookAt(light)", "ortho volume", "P × V × M"]
    fills = ["#eaf2ff", "#fff7e6", "#ecfdf5", "#eff6ff"]
    outlines = [BLUE, AMBER, GREEN, BLUE]
    for x, n, s, f, o in zip(xs, names, subs, fills, outlines):
        pill(d, (x, 220, x + 280, 335), n, f, o, 32)
        text_center(d, (x, 325, x + 280, 385), s, 25, MUTED)
    for a, b in zip(xs[:-1], xs[1:]):
        arrow(d, (a + 290, 278), (b - 20, 278))
    shadow_box(d, (170, 515, 830, 835))
    text_center(d, (220, 545, 780, 610), "Light Frustum", 35, bold=True)
    d.polygon([(320, 740), (530, 615), (705, 690), (505, 815)], outline=BLUE, fill="#dbeafe")
    d.line((530, 615, 530, 500), fill=AMBER, width=7)
    d.ellipse((505, 465, 555, 515), fill=AMBER)
    label(d, (260, 790), "顶点从模型空间映射到光源裁剪空间", 24)
    shadow_box(d, (1030, 515, 1700, 835))
    text_center(d, (1080, 545, 1650, 610), "RGBA Depth Texture", 35, bold=True)
    colors = ["#ef4444", "#22c55e", "#3b82f6", "#64748b"]
    for i, c in enumerate(colors):
        d.rounded_rectangle((1110 + i * 135, 670, 1215 + i * 135, 770), radius=14, fill=c)
        text_center(d, (1110 + i * 135, 670, 1215 + i * 135, 770), "RGBA"[i], 36, "#ffffff", True)
    arrow(d, (850, 675), (1020, 675), CYAN)
    label(d, (1120, 790), "WebGL1 中用颜色纹理保存深度值", 24)
    save(im, "paper_02_light_mvp_depth_pack.png")


def diagram_hard_bias():
    im, d = canvas("硬阴影与 Bias", "一次深度比较给出二值可见性；Bias 用于缓解自遮挡")
    shadow_box(d, (105, 205, 920, 790))
    d.rectangle((200, 665, 820, 700), fill="#cbd5e1")
    d.polygon([(420, 665), (560, 665), (500, 470)], fill="#64748b", outline=NAVY)
    d.ellipse((260, 285, 325, 350), fill=AMBER)
    for p in [(500, 470), (650, 665), (360, 665)]:
        d.line((292, 318, *p), fill="#fbbf24", width=4)
    d.polygon([(500, 470), (650, 665), (720, 665), (555, 470)], fill="#1f2937")
    label(d, (235, 360), "Light", 25)
    label(d, (438, 430), "Occluder", 25)
    label(d, (620, 720), "Receiver", 25)
    shadow_box(d, (1040, 205, 1785, 790))
    text_center(d, (1090, 250, 1735, 310), "Depth Compare", 38, bold=True)
    pill(d, (1130, 390, 1435, 470), "d_receiver - bias", "#eaf2ff", BLUE, 28)
    pill(d, (1130, 555, 1435, 635), "d_map(x,y)", "#fff7e6", AMBER, 28)
    arrow(d, (1455, 430), (1600, 430))
    arrow(d, (1455, 595), (1600, 595))
    d.rounded_rectangle((1615, 420, 1725, 610), radius=18, fill="#ecfdf5", outline=GREEN, width=3)
    text_center(d, (1615, 420, 1725, 610), "0 / 1", 38, bold=True)
    label(d, (1120, 700), "Bias 太小：shadow acne；Bias 太大：Peter Panning", 26, RED)
    save(im, "paper_03_hard_shadow_bias.png")


def diagram_pcf():
    im, d = canvas("PCF 固定半径滤波", "Poisson 圆盘多次 shadow test，平均后得到连续可见性")
    shadow_box(d, (100, 200, 850, 820))
    for i in range(9):
        d.line((205 + i * 65, 290, 205 + i * 65, 745), fill="#e2e8f0", width=2)
        d.line((205, 290 + i * 55, 725, 290 + i * 55), fill="#e2e8f0", width=2)
    d.ellipse((295, 330, 695, 730), outline=BLUE, width=5)
    d.ellipse((485, 520, 515, 550), fill=NAVY)
    for i in range(40):
        a = i * 2.399
        r = 185 * math.sqrt((i + 0.5) / 40)
        x = 500 + r * math.cos(a)
        y = 535 + r * math.sin(a)
        d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=BLUE)
    label(d, (335, 765), "UV 邻域采样：40 个 Poisson points", 26)
    arrow(d, (855, 515), (1025, 515))
    shadow_box(d, (1035, 200, 1825, 820))
    text_center(d, (1085, 245, 1775, 305), "固定半径 soft edge", 36, bold=True)
    for x in range(1160, 1660):
        t = (x - 1160) / 500
        val = int(25 + 225 * t)
        d.line((x, 455, x, 610), fill=(val, val, val), width=1)
    d.rectangle((1160, 455, 1660, 610), outline=NAVY, width=3)
    label(d, (1145, 660), "visibility = 平均 N 次二值比较结果", 28)
    label(d, (1145, 705), "效果：边缘平滑，但软硬不随距离变化", 25, MUTED)
    save(im, "paper_04_pcf_poisson.png")


def diagram_pcss():
    im, d = canvas("PCSS 动态半影流程", "Blocker Search → Penumbra Estimation → Variable-size PCF")
    boxes = [(105, 220, 545, 555), (705, 220, 1145, 555), (1305, 220, 1865, 555)]
    titles = ["1  Blocker Search", "2  Penumbra Size", "3  Variable PCF"]
    fills = ["#fff7e6", "#eaf2ff", "#ecfdf5"]
    outs = [AMBER, BLUE, GREEN]
    for b, t, f, o in zip(boxes, titles, fills, outs):
        shadow_box(d, b, fill=f, outline=o)
        text_center(d, (b[0] + 20, b[1] + 25, b[2] - 20, b[1] + 85), t, 31, bold=True)
    arrow(d, (555, 385), (695, 385))
    arrow(d, (1155, 385), (1295, 385))
    d.ellipse((220, 345, 430, 555), outline=AMBER, width=5)
    for i in range(18):
        x = 325 + 95 * math.cos(i * 2.4) * math.sqrt((i + 1) / 18)
        y = 450 + 95 * math.sin(i * 2.4) * math.sqrt((i + 1) / 18)
        d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=RED if i % 3 else GREEN)
    label(d, (180, 610), "统计邻域中更靠近光源的样本，求 avgBlockerDepth", 25)
    d.line((800, 500, 1050, 300), fill=BLUE, width=6)
    d.line((800, 500, 1035, 500), fill=LINE, width=4)
    d.line((1035, 500, 1050, 300), fill=LINE, width=4)
    d.ellipse((780, 480, 820, 520), fill=RED)
    d.ellipse((1030, 280, 1070, 320), fill=BLUE)
    label(d, (770, 610), "receiver 与 blocker 深度差越大，半影半径越大", 25)
    d.rectangle((1380, 420, 1760, 510), fill="#111827")
    for x in range(1430, 1760):
        t = (x - 1430) / 330
        val = int(25 + 230 * t)
        d.line((x, 420, x, 510), fill=(val, val, val), width=1)
    d.rectangle((1380, 420, 1760, 510), outline=NAVY, width=3)
    d.arc((1335, 285, 1515, 465), 200, 360, fill=GREEN, width=6)
    d.arc((1540, 250, 1815, 525), 200, 360, fill=CYAN, width=6)
    label(d, (1370, 610), "接触处硬，远离遮挡物处更软", 27)
    shadow_box(d, (355, 805, 1565, 955), fill="#f8fafc")
    text_center(d, (385, 835, 1535, 895), "filterSize = clamp(((zR - zB) / zB) × LIGHT_SIZE_UV)", 33, bold=True)
    save(im, "paper_05_pcss_pipeline.png")


def diagram_debug():
    im, d = canvas("调试可视化", "Shadow Map 小窗用于检查深度分布；Blocker 热力图用于检查遮挡搜索")
    shadow_box(d, (105, 205, 980, 820))
    d.rounded_rectangle((180, 300, 895, 710), radius=18, fill="#111827")
    d.rectangle((230, 610, 780, 645), fill="#64748b")
    d.polygon([(430, 610), (535, 610), (490, 445)], fill="#94a3b8")
    d.ellipse((250, 345, 310, 405), fill=AMBER)
    d.rectangle((720, 595, 895, 710), fill="#d1d5db", outline="#facc15", width=6)
    for x in range(720, 895):
        val = int(45 + (x - 720) / 175 * 180)
        d.line((x, 595, x, 710), fill=(val, val, val), width=1)
    label(d, (250, 750), "右下角 Shadow Map 灰度小窗：全黑/全白/裁剪都能快速定位问题", 25)
    shadow_box(d, (1110, 205, 1815, 820))
    for i in range(24):
        for j in range(12):
            t = (i / 23) * 0.75 + (j / 11) * 0.25
            if t < 0.5:
                r = int(34 + t * 2 * 216); g = 197; b = 94
            else:
                r = 239; g = int(197 - (t - 0.5) * 2 * 129); b = 68
            d.rectangle((1190 + i * 24, 350 + j * 24, 1214 + i * 24, 374 + j * 24), fill=(r, g, b))
    d.rectangle((1190, 350, 1766, 638), outline=NAVY, width=3)
    label(d, (1190, 690), "绿色 → 无 blocker；红色 → blocker 占比高", 28)
    label(d, (1190, 735), "注意：显示的是搜索阶段统计，不等于最终亮度", 24, MUTED)
    save(im, "paper_06_debug_visualization.png")


def diagram_multilight():
    im, d = canvas("多光源渲染架构", "每个光源独立生成 Shadow Map，Camera Pass 用加法混合叠加直接光")
    shadow_box(d, (110, 205, 720, 455), fill="#fff7e6", outline=AMBER)
    text_center(d, (145, 235, 685, 295), "Light 0 固定暖色主光", 32, bold=True)
    label(d, (170, 330), "Shadow Pass → light0.fbo", 27)
    label(d, (170, 375), "Camera Pass：ambient + direct0", 27)
    shadow_box(d, (110, 575, 720, 825), fill="#eaf2ff", outline=BLUE)
    text_center(d, (145, 605, 685, 665), "Light 1 轨道冷色光", 32, bold=True)
    label(d, (170, 700), "Shadow Pass → light1.fbo", 27)
    label(d, (170, 745), "Camera Pass：direct1 only", 27)
    arrow(d, (730, 330), (980, 330), AMBER)
    arrow(d, (730, 700), (980, 700), BLUE)
    shadow_box(d, (990, 260, 1400, 780))
    text_center(d, (1025, 305, 1365, 365), "Additive Blending", 35, bold=True)
    d.rounded_rectangle((1070, 430, 1320, 510), radius=18, fill="#fff7e6", outline=AMBER, width=3)
    d.rounded_rectangle((1120, 535, 1370, 615), radius=18, fill="#eaf2ff", outline=BLUE, width=3)
    arrow(d, (1245, 510), (1245, 535), GREEN)
    label(d, (1050, 675), "gl.blendFunc(ONE, ONE)", 30, BLUE)
    shadow_box(d, (1475, 345, 1840, 675), fill="#ecfdf5", outline=GREEN)
    text_center(d, (1505, 395, 1810, 455), "Final Radiance", 34, bold=True)
    label(d, (1525, 510), "ambient 只加一次", 27)
    label(d, (1525, 560), "direct light 逐光源叠加", 27)
    save(im, "paper_07_multilight_additive.png")


def diagram_dynamic():
    im, d = canvas("动态光源与动态模型", "运动会改变 lightMVP，因此每帧都要重新生成 Shadow Map")
    shadow_box(d, (105, 200, 1030, 840))
    d.ellipse((285, 330, 865, 720), outline=BLUE, width=6)
    d.ellipse((480, 465, 670, 610), outline=GREEN, width=6)
    d.ellipse((820, 510, 880, 570), fill=BLUE)
    d.rectangle((555, 535, 615, 595), fill="#86efac", outline=GREEN, width=3)
    d.ellipse((560, 475, 610, 525), fill="#94a3b8")
    d.rectangle((420, 650, 740, 680), fill="#cbd5e1")
    arrow(d, (790, 485), (850, 520), BLUE)
    arrow(d, (620, 510), (650, 560), GREEN)
    label(d, (760, 590), "Light orbit", 27, BLUE)
    label(d, (570, 630), "Model orbit + rotation", 27, GREEN)
    shadow_box(d, (1150, 200, 1810, 840))
    text_center(d, (1190, 250, 1770, 315), "Per-frame Update", 35, bold=True)
    steps = ["1. 更新 light1 位置", "2. 更新小 Mary transform", "3. 重算 uLightMVP", "4. Shadow Pass 写入 FBO", "5. Camera Pass 采样阴影"]
    for i, s in enumerate(steps):
        y = 380 + i * 85
        d.rounded_rectangle((1230, y, 1730, y + 56), radius=16, fill="#f8fafc", outline=LINE, width=2)
        label(d, (1255, y + 13), s, 27, INK)
        if i < len(steps) - 1:
            arrow(d, (1480, y + 58), (1480, y + 80), CYAN, 4)
    save(im, "paper_08_dynamic_scene.png")


def diagram_comparison():
    im, d = canvas("Shadow Map / PCF / PCSS 方法对比", "从基础遮挡验证到固定软化，再到深度相关半影")
    cols = [(110, 210, 595, 800), (760, 210, 1245, 800), (1410, 210, 1875, 800)]
    heads = ["Hard Shadow", "PCF", "PCSS"]
    outs = [RED, BLUE, GREEN]
    desc = [
        ["一次深度比较", "边界二值、锯齿明显", "适合验证遮挡关系"],
        ["固定半径多采样", "边缘连续变软", "接触与远处软硬相近"],
        ["blocker + 动态半影", "接触硬、远处软", "更接近面积光效果"],
    ]
    for c, h, o, lines in zip(cols, heads, outs, desc):
        shadow_box(d, c, outline=o)
        text_center(d, (c[0] + 25, 245, c[2] - 25, 310), h, 36, bold=True)
        x1, y1 = c[0] + 95, 390
        if h == "Hard Shadow":
            d.rectangle((x1, y1, x1 + 150, y1 + 90), fill="#111827")
            d.rectangle((x1 + 150, y1, x1 + 330, y1 + 90), fill="#e5e7eb")
        elif h == "PCF":
            for x in range(x1, x1 + 330):
                t = (x - x1) / 330
                val = int(20 + t * 230)
                d.line((x, y1, x, y1 + 90), fill=(val, val, val), width=1)
        else:
            d.rectangle((x1, y1, x1 + 130, y1 + 90), fill="#111827")
            for x in range(x1 + 130, x1 + 330):
                t = (x - x1 - 130) / 200
                val = int(20 + t * 230)
                d.line((x, y1, x, y1 + 90), fill=(val, val, val), width=1)
        d.rectangle((x1, y1, x1 + 330, y1 + 90), outline=NAVY, width=3)
        for i, line in enumerate(lines):
            label(d, (c[0] + 75, 585 + i * 58), line, 27, INK if i == 0 else MUTED)
    save(im, "paper_09_method_comparison.png")


if __name__ == "__main__":
    diagram_two_pass()
    diagram_mvp_pack()
    diagram_hard_bias()
    diagram_pcf()
    diagram_pcss()
    diagram_debug()
    diagram_multilight()
    diagram_dynamic()
    diagram_comparison()
