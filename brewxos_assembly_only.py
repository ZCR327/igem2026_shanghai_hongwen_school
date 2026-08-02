"""
BrewXOS Fermenter Mini - 整机装配渲染
======================================
只生成组装版，相机特写。在 Blender Scripting 工作台运行。
运行前手动设置输出路径: bpy.context.scene.render.filepath = 'D:/render.png'
"""

import bpy
import math


# ============================================================
# 工具函数
# ============================================================

def clear_scene():
    # 先递归删除所有子集合中的物体
    for coll in list(bpy.data.collections):
        for obj in list(coll.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    # 再删除所有子集合
    for coll in list(bpy.data.collections):
        if coll.name != bpy.context.scene.collection.name:
            bpy.data.collections.remove(coll)
    # 最后清理材质
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)


def mat(name, color, metallic=0.0, roughness=0.5, alpha=1.0):
    m = bpy.data.materials.new(name=name)
    m.use_nodes = True
    bsdf = None
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            bsdf = n
            break
    if bsdf is None:
        bsdf = m.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        out = m.node_tree.nodes.get('Material Output')
        if out:
            m.node_tree.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Alpha'].default_value = alpha
    if alpha < 1.0:
        m.blend_method = 'BLEND'
    return m


def box(name, w, d, h, loc, mt):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(loc[0], loc[1], loc[2] + h / 2))
    o = bpy.context.active_object
    o.name = name
    o.scale = (w / 2, d / 2, h / 2)
    o.data.materials.append(mt)
    return o


def cyl(name, r, h, loc, mt, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(
        radius=r, depth=h, vertices=verts,
        location=(loc[0], loc[1], loc[2] + h / 2))
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mt)
    return o


def torus(name, R, r, loc, mt):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(mt)
    return o


# ============================================================
# 材质
# ============================================================

M = {}

def init_mat():
    global M
    M['s4']  = mat("Steel_4mm",     (0.14, 0.14, 0.15), 0.90, 0.30)
    M['s2']  = mat("Steel_2mm",     (0.17, 0.17, 0.18), 0.85, 0.35)
    M['al']  = mat("Aluminum",      (0.64, 0.64, 0.66), 0.95, 0.25)
    M['gl']  = mat("Glass_GG17",    (0.55, 0.82, 0.76), 0.00, 0.05, 0.40)
    M['ss']  = mat("SS304",         (0.58, 0.58, 0.60), 0.90, 0.28)
    M['pg']  = mat("PCB_Green",     (0.04, 0.17, 0.11), 0.00, 0.55)
    M['pr']  = mat("PCB_Red",       (0.14, 0.05, 0.05), 0.00, 0.55)
    M['pp']  = mat("PP_Plastic",    (0.24, 0.24, 0.26), 0.00, 0.50)
    M['si']  = mat("Silicone",      (0.74, 0.44, 0.24), 0.00, 0.70)
    M['wo']  = mat("Insul_Wool",    (0.84, 0.80, 0.73), 0.00, 0.88)
    M['rb']  = mat("Rubber",        (0.08, 0.08, 0.08), 0.00, 0.92)
    M['sc']  = mat("Screen_Off",    (0.02, 0.02, 0.05), 0.10, 0.20)
    M['so']  = mat("Screen_On",     (0.10, 0.40, 0.33), 0.00, 0.30)
    M['rd']  = mat("EStop_Red",     (0.70, 0.12, 0.12), 0.08, 0.40)
    M['bw']  = mat("Btn_White",     (0.87, 0.87, 0.88), 0.08, 0.40)
    M['ba']  = mat("Btn_Amber",     (0.78, 0.46, 0.23), 0.15, 0.38)
    M['lg']  = mat("LED_Green",     (0.08, 0.85, 0.25), 0.00, 0.08)
    M['la']  = mat("LED_Amber",     (1.00, 0.65, 0.08), 0.00, 0.08)
    M['mo']  = mat("Motor",         (0.43, 0.43, 0.45), 0.88, 0.32)
    M['pu']  = mat("Pump",          (0.20, 0.20, 0.22), 0.08, 0.52)
    M['cu']  = mat("Copper",        (0.82, 0.62, 0.32), 0.60, 0.30)
    M['uv']  = mat("UVC",           (0.45, 0.25, 0.75), 0.00, 0.08)
    M['liq'] = mat("Liquid",        (0.65, 0.50, 0.20), 0.00, 0.20, 0.35)
    M['tu']  = mat("Silicone_Tube", (0.82, 0.78, 0.73), 0.00, 0.48, 0.80)


# ============================================================
# 整机装配
# ============================================================

def build():
    c = bpy.data.collections.new("BrewXOS_Assembly")
    bpy.context.scene.collection.children.link(c)

    # ── 底板 ──
    box("P01_底板", 350, 350, 4, (0, 0, 0), M['s4'])
    c.objects.link(bpy.context.active_object)

    # ── 支脚 ×4 ──
    for fx, fy in [(-160, -160), (160, -160), (-160, 160), (160, 160)]:
        cyl("P23_支脚", 10, 5, (fx, fy, -5), M['rb'])
        c.objects.link(bpy.context.active_object)

    # ── 漏液托盘 ──
    box("P06_托盘", 280, 280, 3, (0, 0, 4), M['pp'])
    c.objects.link(bpy.context.active_object)
    for ex in [-25, 25]:
        cyl("P06_电极", 2, 15, (ex, 0, 7), M['ss'])
        c.objects.link(bpy.context.active_object)

    # ── 罐体支座 (2020 型材) ──
    for ax, ay in [(-120, -120), (120, -120), (-120, 120), (120, 120)]:
        box("P08_立柱", 20, 20, 25, (ax, ay, 7), M['al'])
        c.objects.link(bpy.context.active_object)
    for bx in [-120, 120]:
        box("P08_横梁X", 240, 20, 20, (0, bx, 7), M['al'])
        c.objects.link(bpy.context.active_object)
    for by in [-120, 120]:
        box("P08_横梁Y", 20, 240, 20, (by, 0, 7), M['al'])
        c.objects.link(bpy.context.active_object)

    # ── 加热膜 + 保温棉 ──
    cyl("P09_加热膜", 43, 80, (0, 0, 32), M['si'], 32)
    c.objects.link(bpy.context.active_object)
    cyl("P10_保温棉", 45, 82, (0, 0, 31), M['wo'], 24)
    c.objects.link(bpy.context.active_object)

    # ── 发酵罐 ⌀80×100 ──
    cyl("P07_发酵罐", 40, 100, (0, 0, 32), M['gl'])
    c.objects.link(bpy.context.active_object)
    cyl("液体内容物", 37, 70, (0, 0, 47), M['liq'])
    c.objects.link(bpy.context.active_object)

    # ── 罐盖 + KF16×6 ──
    cyl("P07_罐盖", 42, 6, (0, 0, 132), M['ss'])
    c.objects.link(bpy.context.active_object)
    for i in range(6):
        a = i * math.pi / 3
        px = 42 * math.cos(a)
        py = 42 * math.sin(a)
        cyl(f"KF16_{i+1}", 5, 8, (px, py, 135), M['ss'])
        c.objects.link(bpy.context.active_object)

    # ── UV-C 灯环 ──
    torus("P18_UVC灯环", 30, 2, (0, 0, 130), M['uv'])
    c.objects.link(bpy.context.active_object)

    # ── 搅拌电机 + 轴 + 密封 ──
    cyl("P11_电机", 12, 40, (0, 0, 145), M['mo'])
    c.objects.link(bpy.context.active_object)
    cyl("P11_法兰", 16, 5, (0, 0, 138), M['al'])
    c.objects.link(bpy.context.active_object)
    cyl("P12_搅拌轴", 3, 80, (0, 0, 58), M['ss'])
    c.objects.link(bpy.context.active_object)
    cyl("P12_密封法兰", 15, 10, (0, 0, 128), M['ss'])
    c.objects.link(bpy.context.active_object)

    # ── 四叶桨叶 ──
    for pi in range(4):
        a = pi * math.pi / 2
        bx = 25 * math.cos(a)
        by = 25 * math.sin(a)
        box(f"P13_桨叶{pi+1}", 36, 4, 24, (bx, by, 55), M['ss'])
        c.objects.link(bpy.context.active_object)

    # ── 空气过滤器 ×2 ──
    cyl("P17_过滤器1", 12, 40, (-30, 0, 148), M['pp'])
    c.objects.link(bpy.context.active_object)
    cyl("P17_过滤器2", 12, 40, (30, 0, 148), M['pp'])
    c.objects.link(bpy.context.active_object)

    # ── 主板 ──
    box("B1_主板", 100, 80, 2, (0, -148, 140), M['pg'])
    c.objects.link(bpy.context.active_object)
    for nm, cx, cz, cw, cd in [
        ("ESP32", -30, -15, 22, 16),
        ("ADS1256", 0, -10, 14, 14),
        ("MAX31865", 20, 10, 12, 10),
        ("PT100", -20, 16, 10, 8),
    ]:
        box(f"IC_{nm}", cw, cd, 2, (cx, -148 + cz, 142), M['cu'])
        c.objects.link(bpy.context.active_object)

    # ── 驱动板 ──
    box("B2_驱动板", 100, 80, 2, (0, 110, 10), M['pr'])
    c.objects.link(bpy.context.active_object)
    for nm, dx, dz, dw, dd in [
        ("SSR", -30, -15, 22, 22),
        ("Relay", 10, -10, 14, 12),
        ("DCDC", 20, 10, 12, 10),
        ("LDO", -10, 16, 10, 8),
    ]:
        box(f"D_{nm}", dw, dd, 3, (dx, 110 + dz, 12), M['cu'])
        c.objects.link(bpy.context.active_object)
    box("SSR散热片", 30, 30, 10, (-30, 96, 14), M['al'])
    c.objects.link(bpy.context.active_object)

    # ── 机箱外壳 (四壁 + 顶盖) ──
    # 侧板: 2mm × 348mm纵深 × 450mm高
    box("P05_左侧板", 2, 348, 450, (-174, 0, 4), M['s2'])
    c.objects.link(bpy.context.active_object)
    box("P05_右侧板", 2, 348, 450, (174, 0, 4), M['s2'])
    c.objects.link(bpy.context.active_object)

    # 前面板: 348mm宽 × 2mm深 × 450mm高 (全高封闭, 底面 Z=4)
    box("P03_前面板", 348, 2, 450, (0, -174, 4), M['s2'])
    c.objects.link(bpy.context.active_object)

    # 后盖板: 348mm宽 × 2mm深 × 450mm高 (全高封闭, 底面 Z=4)
    box("P04_后盖板", 348, 2, 450, (0, 174, 4), M['s2'])
    c.objects.link(bpy.context.active_object)

    # 顶盖
    box("P02_顶盖", 350, 350, 2, (0, 0, 452), M['s2'])
    c.objects.link(bpy.context.active_object)

    # ── TFT 屏幕 ──
    box("TFT_框", 74, 58, 5, (0, -173, 350), M['sc'])
    c.objects.link(bpy.context.active_object)
    box("TFT_显示", 66, 50, 0.5, (0, -173, 353), M['so'])
    c.objects.link(bpy.context.active_object)

    # ── 急停按钮 ──
    cyl("急停_底座", 15, 10, (120, -174, 365), M['rd'])
    c.objects.link(bpy.context.active_object)
    cyl("急停_蘑菇头", 18, 6, (120, -176, 372), M['rd'])
    c.objects.link(bpy.context.active_object)

    # ── 操作按钮 ×3 + LED ×3 ──
    for bi, bx in enumerate([-50, 0, 50]):
        mtb = [M['bw'], M['ba'], M['bw']][bi]
        cyl(f"按钮{bi+1}", 10, 6, (bx, -175, 390), mtb)
        c.objects.link(bpy.context.active_object)
    for li, lx in enumerate([-110, -80, -50]):
        mtl = [M['lg'], M['la'], M['lg']][li]
        cyl(f"LED{li+1}", 2.5, 2, (lx, -174, 398), mtl)
        c.objects.link(bpy.context.active_object)

    # ── 蠕动泵 ×3 ──
    for pi, pn in enumerate(["酸液泵", "碱液泵", "补料泵"]):
        py = -60 + pi * 60
        box(f"P14_支架{pi+1}", 10, 40, 50, (-145, py, 4), M['al'])
        c.objects.link(bpy.context.active_object)
        box(f"P15_{pn}", 50, 40, 30, (-115, py, 29), M['pu'])
        c.objects.link(bpy.context.active_object)
        cyl(f"P15_{pn}_泵头", 12, 12, (-90, py, 39), M['pp'])
        c.objects.link(bpy.context.active_object)

    # ── 气泵 ──
    box("P16_气泵", 40, 30, 25, (-125, 90, 4), M['pu'])
    c.objects.link(bpy.context.active_object)

    # ── 流量计 ──
    cyl("P19_流量计", 10, 60, (185, 0, 10), M['gl'])
    c.objects.link(bpy.context.active_object)

    # ── 管路 ──
    cyl("管路_酸液", 3, 80, (-90, -30, 49), M['tu'])
    c.objects.link(bpy.context.active_object)
    cyl("管路_碱液", 3, 80, (-90, 30, 49), M['tu'])
    c.objects.link(bpy.context.active_object)
    cyl("管路_补料", 3, 80, (-90, 90, 49), M['tu'])
    c.objects.link(bpy.context.active_object)


# ============================================================
# 场景设置
# ============================================================

def setup_scene():
    # 相机：正前方偏右
    bpy.ops.object.camera_add(location=(420, -650, 320))
    cam = bpy.context.active_object
    cam.name = "Camera_Main"
    cam.rotation_euler = (math.radians(64), 0, math.radians(58))
    bpy.context.scene.camera = cam

    # 俯视辅助相机
    bpy.ops.object.camera_add(location=(0, 0, 600))
    cam2 = bpy.context.active_object
    cam2.name = "Camera_Top"
    cam2.rotation_euler = (0, 0, 0)

    # 正面特写相机
    bpy.ops.object.camera_add(location=(0, -550, 230))
    cam3 = bpy.context.active_object
    cam3.name = "Camera_Front"
    cam3.rotation_euler = (math.radians(75), 0, 0)

    # 灯光
    bpy.ops.object.light_add(type='AREA', location=(300, -600, 500))
    bpy.context.active_object.data.energy = 800
    bpy.context.active_object.data.size = 600
    bpy.context.active_object.name = "KeyLight"

    bpy.ops.object.light_add(type='AREA', location=(-200, 300, 350))
    bpy.context.active_object.data.energy = 400
    bpy.context.active_object.data.size = 400
    bpy.context.active_object.name = "FillLight"

    bpy.ops.object.light_add(type='AREA', location=(0, 0, 600))
    bpy.context.active_object.data.energy = 150
    bpy.context.active_object.data.size = 300
    bpy.context.active_object.name = "RimLight"

    # 渲染设置
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.cycles.use_denoising = True
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    bpy.context.scene.render.film_transparent = False

    # 世界背景
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.89, 0.87, 0.83, 1.0)
    bg.inputs['Strength'].default_value = 0.25

    # 输出
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.image_settings.color_mode = 'RGBA'


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    clear_scene()
    init_mat()
    build()
    setup_scene()

    print("=" * 50)
    print("BrewXOS Fermenter Mini — 整机装配完成")
    print("=" * 50)
    print("相机:")
    print("  Camera_Main  — 正前方斜45°全景")
    print("  Camera_Front — 正面特写")
    print("  Camera_Top   — 俯视")
    print()
    print("渲染: F12 或用以下代码:")
    print("  bpy.context.scene.render.filepath = 'D:/brewxos_render.png'")
    print("  bpy.ops.render.render(write_still=True)")
    print("=" * 50)
