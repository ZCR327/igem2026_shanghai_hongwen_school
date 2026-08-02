"""
BrewXOS Fermenter Mini - 零部件拆解建模
==========================================
基于 BrewXOS 硬件文档，23 个零部件逐一独立建模。
爆炸图布局，自下而上按装配顺序排列。
在 Blender Scripting 工作台中运行。
"""

import bpy
import math


# ============================================================
# 工具函数
# ============================================================

def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)
    for coll in list(bpy.data.collections):
        if coll.name != "Collection":
            bpy.data.collections.remove(coll)


def make_material(name, color, metallic=0.0, roughness=0.5, alpha=1.0):
    """创建 PBR 材质（兼容 Blender 3.x / 4.x）"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = None
    for node in mat.node_tree.nodes:
        if node.type == 'BSDF_PRINCIPLED':
            bsdf = node
            break
    if bsdf is None:
        bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        output = mat.node_tree.nodes.get('Material Output')
        if output:
            mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Alpha'].default_value = alpha
    if alpha < 1.0:
        mat.blend_method = 'BLEND'
    return mat


def box(name, w, d, h, loc, mat):
    """立方体 (宽x深x高), loc 为底面中心"""
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(loc[0], loc[1], loc[2] + h / 2)
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (w / 2, d / 2, h / 2)
    obj.data.materials.append(mat)
    return obj


def cyl(name, r, h, loc, mat, verts=48):
    """圆柱体 (半径, 高度), loc 为底面中心"""
    bpy.ops.mesh.primitive_cylinder_add(
        radius=r, depth=h, vertices=verts,
        location=(loc[0], loc[1], loc[2] + h / 2)
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def torus(name, R, r, loc, mat):
    """圆环"""
    bpy.ops.mesh.primitive_torus_add(
        major_radius=R, minor_radius=r, location=loc
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def sphere(name, r, loc, mat):
    """球体"""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def label(obj, text, offset_z=0):
    """在物体上方添加文字标注（用 Empty + 自定义属性，方便查看）"""
    obj["_label"] = text


# ============================================================
# 材质库
# ============================================================

MAT = {}

def init_materials():
    global MAT
    MAT['steel_4mm']   = make_material("Steel_4mm",   (0.14, 0.14, 0.15), metallic=0.90, roughness=0.30)
    MAT['steel_2mm']   = make_material("Steel_2mm",   (0.17, 0.17, 0.18), metallic=0.85, roughness=0.35)
    MAT['aluminum']    = make_material("Aluminum",    (0.64, 0.64, 0.66), metallic=0.95, roughness=0.25)
    MAT['glass']       = make_material("Glass_GG17",  (0.55, 0.82, 0.76), metallic=0.00, roughness=0.05, alpha=0.40)
    MAT['stainless']   = make_material("SS304",       (0.58, 0.58, 0.60), metallic=0.90, roughness=0.28)
    MAT['pcb_green']   = make_material("PCB_Green",   (0.04, 0.17, 0.11), metallic=0.00, roughness=0.55)
    MAT['pcb_red']     = make_material("PCB_Red",     (0.14, 0.05, 0.05), metallic=0.00, roughness=0.55)
    MAT['plastic_pp']  = make_material("PP_Plastic",  (0.24, 0.24, 0.26), metallic=0.00, roughness=0.50)
    MAT['silicone']    = make_material("Silicone",    (0.74, 0.44, 0.24), metallic=0.00, roughness=0.70)
    MAT['wool']        = make_material("Insul_Wool",  (0.84, 0.80, 0.73), metallic=0.00, roughness=0.88)
    MAT['rubber']      = make_material("Rubber",      (0.08, 0.08, 0.08), metallic=0.00, roughness=0.92)
    MAT['screen']      = make_material("Screen",      (0.02, 0.02, 0.05), metallic=0.10, roughness=0.20)
    MAT['screen_on']   = make_material("Screen_On",   (0.10, 0.40, 0.33), metallic=0.00, roughness=0.30)
    MAT['red_btn']     = make_material("EStop_Red",   (0.70, 0.12, 0.12), metallic=0.08, roughness=0.40)
    MAT['btn_white']   = make_material("Btn_White",   (0.87, 0.87, 0.88), metallic=0.08, roughness=0.40)
    MAT['btn_amber']   = make_material("Btn_Amber",   (0.78, 0.46, 0.23), metallic=0.15, roughness=0.38)
    MAT['led_green']   = make_material("LED_Green",   (0.08, 0.85, 0.25), metallic=0.00, roughness=0.08)
    MAT['led_amber']   = make_material("LED_Amber",   (1.00, 0.65, 0.08), metallic=0.00, roughness=0.08)
    MAT['motor']       = make_material("Motor_Body",  (0.43, 0.43, 0.45), metallic=0.88, roughness=0.32)
    MAT['pump']        = make_material("Pump_Body",   (0.20, 0.20, 0.22), metallic=0.08, roughness=0.52)
    MAT['copper']      = make_material("Copper",      (0.82, 0.62, 0.32), metallic=0.60, roughness=0.30)
    MAT['uvc']         = make_material("UVC_Purple",  (0.45, 0.25, 0.75), metallic=0.00, roughness=0.08)
    MAT['liquid']      = make_material("Liquid",      (0.65, 0.50, 0.20), metallic=0.00, roughness=0.20, alpha=0.35)
    MAT['tube']        = make_material("Tube",         (0.82, 0.78, 0.73), metallic=0.00, roughness=0.48, alpha=0.80)


# ============================================================
# 23 个零部件逐一建模
# ============================================================

def build_all():
    print("=" * 60)
    print("BrewXOS Fermenter Mini - 零部件拆解建模")
    print("23 个零件 · 爆炸图布局")
    print("=" * 60)

    init_materials()
    root = bpy.context.scene.collection

    # 爆炸图 Y 轴间距
    GAP = 150  # 零件组之间间距（足够分开看清每个零件）
    Y_BASE = -900  # 起始 Y

    # ========================================================
    # 零件组 1: 底板 + 支脚  (P-01, P-23)
    # ========================================================
    y0 = Y_BASE
    coll = bpy.data.collections.new("01_底板")
    root.children.link(coll)

    # P-01 底板 350×350×4mm
    box("P01_底板_350x350x4mm", 350, 350, 4, (0, y0, 0), MAT['steel_4mm'])
    coll.objects.link(bpy.context.active_object)

    # P-23 支脚 ×4  ⌀20×5mm
    for i, (fx, fy) in enumerate([(-160, -160), (160, -160), (-160, 160), (160, 160)]):
        cyl(f"P23_支脚{i+1}_D20x5mm", 10, 5, (fx, fy + y0, -5), MAT['rubber'])
        coll.objects.link(bpy.context.active_object)

    y0 += GAP

    # ========================================================
    # 零件组 2: 漏液托盘  (P-06)
    # ========================================================
    coll = bpy.data.collections.new("02_漏液托盘")
    root.children.link(coll)
    box("P06_漏液托盘_280x280x3mm", 280, 280, 3, (0, y0, 0), MAT['plastic_pp'])
    coll.objects.link(bpy.context.active_object)

    # 电极 ×2
    for ei, ex in enumerate([-25, 25]):
        cyl(f"P06_电极{ei+1}", 2, 15, (ex, y0, 3), MAT['stainless'])
        coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 3: 罐体支座  (P-08)
    # ========================================================
    coll = bpy.data.collections.new("03_罐体支座")
    root.children.link(coll)

    # 4 根 2020 铝型材立柱 240mm
    for ax, ay in [(-120, -120), (120, -120), (-120, 120), (120, 120)]:
        box(f"P08_立柱_20x20x240mm", 20, 20, 240, (ax, ay + y0, 0), MAT['aluminum'])
        coll.objects.link(bpy.context.active_object)

    # 4 根横梁
    for bx in [-120, 120]:
        box(f"P08_横梁_240x20x20mm", 240, 20, 20, (0, bx + y0, 120), MAT['aluminum'])
        coll.objects.link(bpy.context.active_object)
    for by in [-120, 120]:
        box(f"P08_横梁_20x240x20mm", 20, 240, 20, (by, y0, 120), MAT['aluminum'])
        coll.objects.link(bpy.context.active_object)

    # 8× 角件
    for cx, cy in [(-120, -120), (120, -120), (-120, 120), (120, 120),
                   (-120, -120), (120, -120), (-120, 120), (120, 120)]:
        i = len([o for o in coll.objects if "角件" in o.name]) + 1
        box(f"P08_角件{i}", 20, 20, 5, (cx, cy + y0, 235), MAT['aluminum'])
        coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 4: 加热膜  (P-09)
    # ========================================================
    coll = bpy.data.collections.new("04_加热膜")
    root.children.link(coll)

    cyl("P09_加热膜_50W220V", 43, 80, (0, y0, 0), MAT['silicone'], verts=32)
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 5: 保温棉  (P-10)
    # ========================================================
    coll = bpy.data.collections.new("05_保温棉")
    root.children.link(coll)

    cyl("P10_保温棉_1cm厚", 45, 82, (0, y0, 0), MAT['wool'], verts=24)
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 6: 发酵罐  (P-07)
    # ========================================================
    coll = bpy.data.collections.new("06_发酵罐")
    root.children.link(coll)

    cyl("P07_发酵罐_D80x100_GG17", 40, 100, (0, y0, 0), MAT['glass'])
    coll.objects.link(bpy.context.active_object)
    # 罐内液体示意
    cyl("P07_液体内容物", 37, 70, (0, y0, 20), MAT['liquid'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 7: 罐盖 + 法兰  (P-07 附件)
    # ========================================================
    coll = bpy.data.collections.new("07_罐盖法兰")
    root.children.link(coll)

    cyl("P07_罐盖_D84x6mm", 42, 6, (0, y0, 0), MAT['stainless'])
    coll.objects.link(bpy.context.active_object)

    # 6× KF16 法兰接口
    for i in range(6):
        angle = i * math.pi / 3
        px = 42 * math.cos(angle)
        pz = 42 * math.sin(angle)
        cyl(f"P07_KF16接口{i+1}_D10x8mm", 5, 8, (px, y0, pz + 3), MAT['stainless'])
        coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 8: UV-C 灯环  (P-18)
    # ========================================================
    coll = bpy.data.collections.new("08_UVC灯环")
    root.children.link(coll)

    torus("P18_UVC灯环_254nm_D60", 30, 2, (0, y0, 0), MAT['uvc'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 9: 搅拌电机  (P-11)
    # ========================================================
    coll = bpy.data.collections.new("09_搅拌电机")
    root.children.link(coll)

    cyl("P11_JGB37电机_D24x40mm", 12, 40, (0, y0, 0), MAT['motor'])
    coll.objects.link(bpy.context.active_object)
    # 电机法兰
    cyl("P11_电机法兰_D32x5mm", 16, 5, (0, y0, -5), MAT['aluminum'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 10: 磁力密封 + 搅拌轴  (P-12)
    # ========================================================
    coll = bpy.data.collections.new("10_搅拌轴")
    root.children.link(coll)

    cyl("P12_磁力密封轴_D6x80mm", 3, 80, (0, y0, 0), MAT['stainless'])
    coll.objects.link(bpy.context.active_object)
    # 密封法兰
    cyl("P12_密封法兰_D30x10mm", 15, 10, (0, y0, -10), MAT['stainless'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 11: 四叶桨叶  (P-13)
    # ========================================================
    coll = bpy.data.collections.new("11_桨叶")
    root.children.link(coll)

    for pi in range(4):
        angle = pi * math.pi / 2
        bx = 25 * math.cos(angle)
        by = 25 * math.sin(angle)
        box(f"P13_桨叶{pi+1}_D50", 36, 4, 24, (bx, y0 + by, 0), MAT['stainless'])
        coll.objects.link(bpy.context.active_object)
    # 中心轴套
    cyl("P13_轴套_D10x20mm", 5, 20, (0, y0, 0), MAT['stainless'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 12: 空气过滤器  (P-17)
    # ========================================================
    coll = bpy.data.collections.new("12_过滤器")
    root.children.link(coll)

    for fi, fx in enumerate([-30, 30]):
        cyl(f"P17_过滤器{fi+1}_D25x40_0.22um", 12, 40, (fx, y0, 0), MAT['plastic_pp'])
        coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 13: 主板  (P-?? Board 1)
    # ========================================================
    coll = bpy.data.collections.new("13_主板")
    root.children.link(coll)

    box("Board1_主板_100x80x1.6mm", 100, 80, 1.6, (0, y0, 0), MAT['pcb_green'])
    coll.objects.link(bpy.context.active_object)

    # 芯片
    chips = [
        ("ESP32-S3",    -35, -20, 22, 16),
        ("ADS1256_ADC",   0, -15, 14, 14),
        ("MAX31865_PT",  20,   5, 12, 10),
        ("端子排_PT100", -20,  15, 10,  8),
        ("端子排_I2C",   -40,   5,  8,  6),
        ("USB-C",         35, -20,  8, 12),
    ]
    for cname, cx, cz, cw, cd in chips:
        box(f"IC_{cname}", cw, cd, 2, (cx, y0 + cz, 1.6), MAT['copper'])
        coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 14: 驱动板  (P-?? Board 2)
    # ========================================================
    coll = bpy.data.collections.new("14_驱动板")
    root.children.link(coll)

    box("Board2_驱动板_100x80x1.6mm", 100, 80, 1.6, (0, y0, 0), MAT['pcb_red'])
    coll.objects.link(bpy.context.active_object)

    drv_chips = [
        ("SSR-25DA",     -30, -15, 22, 22),
        ("继电器模块",    10, -10, 14, 12),
        ("LM2596_DCDC",   20,  10, 12, 10),
        ("LDO_AMS1117",  -10,  20, 10,  8),
        ("MOSFET×6",      30, -20, 30, 15),
    ]
    for dname, dx, dz, dw, dd in drv_chips:
        box(f"D_{dname}", dw, dd, 3, (dx, y0 + dz, 1.6), MAT['copper'])
        coll.objects.link(bpy.context.active_object)

    # SSR 散热片
    box("SSR散热片_30x30x10mm", 30, 30, 10, (-30, y0 - 15, 3), MAT['aluminum'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 15: 板间排线  (P-??)
    # ========================================================
    coll = bpy.data.collections.new("15_排线")
    root.children.link(coll)

    box("排线_20P_20cm", 18, 2, 200, (0, y0, 0), MAT['btn_amber'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 16: 前面板  (P-03)
    # ========================================================
    coll = bpy.data.collections.new("16_前面板")
    root.children.link(coll)

    box("P03_前面板_350x130x2mm", 350, 2, 130, (0, y0, 0), MAT['steel_2mm'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 17: 后盖板  (P-04)
    # ========================================================
    coll = bpy.data.collections.new("17_后盖板")
    root.children.link(coll)

    box("P04_后盖板_350x130x2mm", 350, 2, 130, (0, y0, 0), MAT['steel_2mm'])
    coll.objects.link(bpy.context.active_object)

    # USB-C 孔标记 和 220V 进线孔
    cyl("P04_USBC孔", 5, 2, (0, y0, 90), MAT['screen'])
    coll.objects.link(bpy.context.active_object)
    cyl("P04_220V进线孔", 10, 2, (-60, y0, 30), MAT['plastic_pp'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 18: 侧板 ×2  (P-05)
    # ========================================================
    coll = bpy.data.collections.new("18_侧板")
    root.children.link(coll)

    box("P05_左侧板_450x130x2mm", 2, 130, 450, (-176, y0, 0), MAT['steel_2mm'])
    coll.objects.link(bpy.context.active_object)
    box("P05_右侧板_450x130x2mm", 2, 130, 450, (176, y0, 0), MAT['steel_2mm'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 19: 顶盖  (P-02)
    # ========================================================
    coll = bpy.data.collections.new("19_顶盖")
    root.children.link(coll)

    box("P02_顶盖_350x350x2mm", 350, 350, 2, (0, y0, 0), MAT['steel_2mm'])
    coll.objects.link(bpy.context.active_object)

    # 散热孔 ×5
    for hi in range(5):
        hx = -40 + hi * 20
        cyl(f"P02_散热孔{hi+1}_D5mm", 3, 2, (hx, y0, 1), MAT['screen'])
        coll.objects.link(bpy.context.active_object)
    # TFT 开孔
    box("P02_TFT开孔_74x58mm", 74, 58, 2, (0, y0 - 140, 1), MAT['screen'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 20: TFT 屏幕  (P-??)
    # ========================================================
    coll = bpy.data.collections.new("20_TFT屏幕")
    root.children.link(coll)

    box("TFT_屏幕框_74x58x5mm", 74, 58, 5, (0, y0, 0), MAT['screen'])
    coll.objects.link(bpy.context.active_object)
    box("TFT_显示区_66x50mm", 66, 50, 0.5, (0, y0, 2.5), MAT['screen_on'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 21: 急停按钮  (P-??)
    # ========================================================
    coll = bpy.data.collections.new("21_急停按钮")
    root.children.link(coll)

    cyl("急停_底座_D30x10mm", 15, 10, (0, y0, 0), MAT['red_btn'])
    coll.objects.link(bpy.context.active_object)
    cyl("急停_蘑菇头_D36x6mm", 18, 6, (0, y0, 10), MAT['red_btn'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 22: 操作按钮 + LED  (P-??)
    # ========================================================
    coll = bpy.data.collections.new("22_按钮LED")
    root.children.link(coll)

    for bi, bx in enumerate([-40, 0, 40]):
        mat_btn = [MAT['btn_white'], MAT['btn_amber'], MAT['btn_white']][bi]
        cyl(f"按钮{bi+1}_D20x6mm", 10, 6, (bx, y0, 0), mat_btn)
        coll.objects.link(bpy.context.active_object)

    for li, lx in enumerate([-90, -60, -30]):
        mat_led = [MAT['led_green'], MAT['led_amber'], MAT['led_green']][li]
        cyl(f"LED_{['RUN','ALM','PWR'][li]}_D4mm", 2, 2, (lx, y0, 8), mat_led)
        coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 23: 蠕动泵 ×3 + 气泵 + 流量计  (P-14/15/16/19)
    # ========================================================
    coll = bpy.data.collections.new("23_泵组")
    root.children.link(coll)

    # 3× 蠕动泵
    pump_names = ["P101_酸液泵", "P102_碱液泵", "P103_补料泵"]
    for pi, pname in enumerate(pump_names):
        px = -100 + pi * 100
        # 支架
        box(f"P14_支架{pi+1}", 10, 40, 50, (px - 30, y0, 0), MAT['aluminum'])
        coll.objects.link(bpy.context.active_object)
        # 泵体
        box(f"P15_{pname}_50x40x30", 50, 40, 30, (px, y0, 25), MAT['pump'])
        coll.objects.link(bpy.context.active_object)
        # 泵头
        cyl(f"P15_{pname}_泵头_D24x12", 12, 12, (px + 25, y0, 35), MAT['plastic_pp'])
        coll.objects.link(bpy.context.active_object)

    # 气泵 P-16
    box("P16_气泵_KPM24A_40x30x25", 40, 30, 25, (-150, y0, 0), MAT['pump'])
    coll.objects.link(bpy.context.active_object)

    # 流量计 P-19
    cyl("P19_流量计_LZB3_D20x60", 10, 60, (150, y0, 15), MAT['glass'])
    coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 24: 硅胶管路  (P-20)
    # ========================================================
    coll = bpy.data.collections.new("24_管路")
    root.children.link(coll)

    for ti in range(5):
        cyl(f"P20_硅胶管{ti+1}_ID3mm_1m", 3, 100, (-50 + ti * 25, y0, 0), MAT['tube'])
        coll.objects.link(bpy.context.active_object)
    y0 += GAP

    # ========================================================
    # 零件组 25: 螺丝紧固件  (P-21, P-22)
    # ========================================================
    coll = bpy.data.collections.new("25_紧固件")
    root.children.link(coll)

    # M3 尼龙柱 ×8
    for ni in range(8):
        nx = -35 + ni * 10
        cyl(f"P21_尼龙柱{ni+1}_M3x10mm", 2, 10, (nx, y0, 0), MAT['plastic_pp'])
        coll.objects.link(bpy.context.active_object)

    # M4 螺丝 ×20
    for si in range(20):
        sx = -95 + si * 10
        cyl(f"P22_M4螺丝{si+1}_M4x10", 2, 10, (sx, y0, 15), MAT['stainless'])
        coll.objects.link(bpy.context.active_object)

    # ========================================================
    # ========================================================
    # 组装版：所有零件按实际位置装配成整机
    # ========================================================
    # ========================================================
    ASM_X = 650  # 组装版在拆解版右侧 650mm

    print("构建组装版整机...")
    asm = bpy.data.collections.new("ASM_整机装配")
    root.children.link(asm)

    # --- 底板 P-01 + 支脚 P-23 ---
    box("ASM_P01_底板", 350, 350, 4, (ASM_X, 0, 0), MAT['steel_4mm'])
    asm.objects.link(bpy.context.active_object)
    for fx, fy in [(-160, -160), (160, -160), (-160, 160), (160, 160)]:
        cyl("ASM_P23_支脚", 10, 5, (ASM_X + fx, fy, -5), MAT['rubber'])
        asm.objects.link(bpy.context.active_object)

    # --- 漏液托盘 P-06 ---
    box("ASM_P06_漏液托盘", 280, 280, 3, (ASM_X, 0, 4), MAT['plastic_pp'])
    asm.objects.link(bpy.context.active_object)

    # --- 罐体支座 P-08 (2020铝型材框架) ---
    # 4 根立柱
    for ax, ay in [(-120, -120), (120, -120), (-120, 120), (120, 120)]:
        box("ASM_P08_立柱", 20, 20, 25, (ASM_X + ax, ay, 7), MAT['aluminum'])
        asm.objects.link(bpy.context.active_object)
    # 横梁
    for bx in [-120, 120]:
        box("ASM_P08_横梁", 240, 20, 20, (ASM_X, bx, 7), MAT['aluminum'])
        asm.objects.link(bpy.context.active_object)

    # --- 加热膜 P-09 + 保温棉 P-10 ---
    cyl("ASM_P09_加热膜", 43, 80, (ASM_X, 0, 32), MAT['silicone'], verts=32)
    asm.objects.link(bpy.context.active_object)
    cyl("ASM_P10_保温棉", 45, 82, (ASM_X, 0, 31), MAT['wool'], verts=24)
    asm.objects.link(bpy.context.active_object)

    # --- 发酵罐 P-07 ---
    cyl("ASM_P07_发酵罐", 40, 100, (ASM_X, 0, 32), MAT['glass'])
    asm.objects.link(bpy.context.active_object)
    cyl("ASM_P07_液体", 37, 70, (ASM_X, 0, 47), MAT['liquid'])
    asm.objects.link(bpy.context.active_object)

    # --- 罐盖 P-07 法兰 ---
    cyl("ASM_P07_罐盖", 42, 6, (ASM_X, 0, 132), MAT['stainless'])
    asm.objects.link(bpy.context.active_object)
    for i in range(6):
        angle = i * math.pi / 3
        px = 42 * math.cos(angle)
        py = 42 * math.sin(angle)
        cyl("ASM_P07_KF16", 5, 8, (ASM_X + px, py, 135), MAT['stainless'])
        asm.objects.link(bpy.context.active_object)

    # --- UV-C 灯环 P-18 ---
    torus("ASM_P18_UVC", 30, 2, (ASM_X, 0, 130), MAT['uvc'])
    asm.objects.link(bpy.context.active_object)

    # --- 搅拌电机 P-11 + 搅拌轴 P-12 + 桨叶 P-13 ---
    cyl("ASM_P11_电机", 12, 40, (ASM_X, 0, 145), MAT['motor'])
    asm.objects.link(bpy.context.active_object)
    cyl("ASM_P11_法兰", 16, 5, (ASM_X, 0, 138), MAT['aluminum'])
    asm.objects.link(bpy.context.active_object)
    cyl("ASM_P12_搅拌轴", 3, 80, (ASM_X, 0, 58), MAT['stainless'])
    asm.objects.link(bpy.context.active_object)
    for pi in range(4):
        angle = pi * math.pi / 2
        bx = 25 * math.cos(angle)
        by = 25 * math.sin(angle)
        box(f"ASM_P13_桨叶{pi+1}", 36, 4, 24, (ASM_X + bx, by, 55), MAT['stainless'])
        asm.objects.link(bpy.context.active_object)

    # --- 空气过滤器 P-17 ×2 (罐盖上方两侧) ---
    cyl("ASM_P17_过滤器1", 12, 40, (ASM_X - 30, 0, 148), MAT['plastic_pp'])
    asm.objects.link(bpy.context.active_object)
    cyl("ASM_P17_过滤器2", 12, 40, (ASM_X + 30, 0, 148), MAT['plastic_pp'])
    asm.objects.link(bpy.context.active_object)

    # --- 主板 Board 1 (前面板内侧) ---
    box("ASM_Board1_主板", 100, 80, 1.6, (ASM_X, -160, 140), MAT['pcb_green'])
    asm.objects.link(bpy.context.active_object)
    for cname, cx, cz, cw, cd in [
        ("ESP32", -30, -14, 22, 16), ("ADS1256", 0, -9, 14, 14),
        ("MAX31865", 20, 11, 12, 10), ("PT100", -20, 21, 10, 8),
    ]:
        box(f"ASM_IC_{cname}", cw, cd, 2, (ASM_X + cx, -160 + cz, 141.6), MAT['copper'])
        asm.objects.link(bpy.context.active_object)

    # --- 驱动板 Board 2 (底板后部) ---
    box("ASM_Board2_驱动板", 100, 80, 1.6, (ASM_X, 120, 10), MAT['pcb_red'])
    asm.objects.link(bpy.context.active_object)
    for dname, dx, dz, dw, dd in [
        ("SSR", -30, -14, 22, 22), ("Relay", 10, -9, 14, 12),
        ("DCDC", 20, 11, 12, 10), ("LDO", -10, 21, 10, 8),
    ]:
        box(f"ASM_D_{dname}", dw, dd, 3, (ASM_X + dx, 120 + dz, 11.6), MAT['copper'])
        asm.objects.link(bpy.context.active_object)
    box("ASM_SSR散热片", 30, 30, 10, (ASM_X - 30, 106, 13), MAT['aluminum'])
    asm.objects.link(bpy.context.active_object)

    # --- 侧板 P-05 (左右) ---
    box("ASM_P05_左侧板", 2, 130, 450, (ASM_X - 174, 0, 4), MAT['steel_2mm'])
    asm.objects.link(bpy.context.active_object)
    box("ASM_P05_右侧板", 2, 130, 450, (ASM_X + 174, 0, 4), MAT['steel_2mm'])
    asm.objects.link(bpy.context.active_object)

    # --- 前面板 P-03 ---
    box("ASM_P03_前面板", 350, 2, 130, (ASM_X, -174, 324), MAT['steel_2mm'])
    asm.objects.link(bpy.context.active_object)

    # --- 后盖板 P-04 ---
    box("ASM_P04_后盖板", 350, 2, 130, (ASM_X, 174, 324), MAT['steel_2mm'])
    asm.objects.link(bpy.context.active_object)

    # --- 顶盖 P-02 ---
    box("ASM_P02_顶盖", 350, 350, 2, (ASM_X, 0, 452), MAT['steel_2mm'])
    asm.objects.link(bpy.context.active_object)

    # --- TFT 屏幕 (前面板外侧) ---
    box("ASM_TFT_屏幕框", 74, 58, 5, (ASM_X, -173, 350), MAT['screen'])
    asm.objects.link(bpy.context.active_object)
    box("ASM_TFT_显示区", 66, 50, 0.5, (ASM_X, -173, 353), MAT['screen_on'])
    asm.objects.link(bpy.context.active_object)

    # --- 急停按钮 (前面板右上) ---
    cyl("ASM_急停_底座", 15, 10, (ASM_X + 120, -174, 365), MAT['red_btn'])
    asm.objects.link(bpy.context.active_object)
    cyl("ASM_急停_蘑菇头", 18, 6, (ASM_X + 120, -176, 372), MAT['red_btn'])
    asm.objects.link(bpy.context.active_object)

    # --- 操作按钮 ×3 + LED ×3 (前面板) ---
    for bi, bx in enumerate([-50, 0, 50]):
        mat_btn = [MAT['btn_white'], MAT['btn_amber'], MAT['btn_white']][bi]
        cyl(f"ASM_按钮{bi+1}", 10, 6, (ASM_X + bx, -175, 390), mat_btn)
        asm.objects.link(bpy.context.active_object)
    for li, lx in enumerate([-120, -90, -60]):
        mat_led = [MAT['led_green'], MAT['led_amber'], MAT['led_green']][li]
        cyl(f"ASM_LED_{li+1}", 2, 2, (ASM_X + lx, -174, 400), mat_led)
        asm.objects.link(bpy.context.active_object)

    # --- 蠕动泵 ×3 (底板左侧后部) ---
    pump_names = ["酸液泵", "碱液泵", "补料泵"]
    for pi, pname in enumerate(pump_names):
        py = -60 + pi * 60
        box(f"ASM_P14_支架{pi+1}", 10, 40, 50, (ASM_X - 145, py, 4), MAT['aluminum'])
        asm.objects.link(bpy.context.active_object)
        box(f"ASM_P15_{pname}", 50, 40, 30, (ASM_X - 115, py, 29), MAT['pump'])
        asm.objects.link(bpy.context.active_object)
        cyl(f"ASM_P15_{pname}_泵头", 12, 12, (ASM_X - 90, py, 39), MAT['plastic_pp'])
        asm.objects.link(bpy.context.active_object)

    # --- 气泵 P-16 ---
    box("ASM_P16_气泵", 40, 30, 25, (ASM_X - 130, 100, 4), MAT['pump'])
    asm.objects.link(bpy.context.active_object)

    # --- 流量计 P-19 (侧面) ---
    cyl("ASM_P19_流量计", 10, 60, (ASM_X + 170, 0, 20), MAT['glass'])
    asm.objects.link(bpy.context.active_object)

    # --- 管路 P-20 (泵→罐方向示意) ---
    cyl("ASM_P20_管路1", 3, 80, (ASM_X - 90, -40, 49), MAT['tube'])
    asm.objects.link(bpy.context.active_object)
    cyl("ASM_P20_管路2", 3, 80, (ASM_X - 90, 20, 49), MAT['tube'])
    asm.objects.link(bpy.context.active_object)

    # ========================================================
    # 相机 + 灯光（同时覆盖拆解版和组装版）
    # ========================================================
    print("设置相机和灯光...")

    # 主相机：居中俯视，同时看到左右两版
    bpy.ops.object.camera_add(location=(ASM_X / 2 + 100, Y_BASE + 1000, 600))
    cam = bpy.context.active_object
    cam.name = "Camera_Main"
    cam.rotation_euler = (math.radians(60), 0, math.radians(75))
    bpy.context.scene.camera = cam

    # 组装版特写相机
    bpy.ops.object.camera_add(location=(ASM_X, -350, 280))
    cam_asm = bpy.context.active_object
    cam_asm.name = "Camera_Assembly"
    cam_asm.rotation_euler = (math.radians(72), 0, math.radians(90))

    # 拆解版俯视
    bpy.ops.object.camera_add(location=(0, Y_BASE + 800, 800))
    cam_top = bpy.context.active_object
    cam_top.name = "Camera_Top"
    cam_top.rotation_euler = (0, 0, 0)

    # 灯光覆盖整个场景
    bpy.ops.object.light_add(type='AREA', location=(ASM_X / 2, Y_BASE + 1500, 600))
    bpy.context.active_object.data.energy = 700
    bpy.context.active_object.data.size = 600

    bpy.ops.object.light_add(type='AREA', location=(ASM_X / 2, Y_BASE + 1500, 300))
    bpy.context.active_object.data.energy = 400
    bpy.context.active_object.data.size = 500

    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

    # 浅灰背景
    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.92, 0.90, 0.86, 1.0)
    bg.inputs['Strength'].default_value = 0.3

    print("=" * 60)
    print("建模完成! 左侧=拆解爆炸图 · 右侧=整机装配")
    print("拆解版: 25 组零件沿 Y 轴排列，间距 150mm")
    print("组装版: 所有零件按实际位置装配 (ASM_整机装配)")
    print("")
    print("操作提示:")
    print("  Numpad 0     = 主相机 (全景)")
    print("  选中 Camera_Assembly → Numpad 0 = 组装版特写")
    print("  选中 Camera_Top → Numpad 0 = 俯视拆解版")
    print("  鼠标滚轮缩放 / 中键拖拽旋转")
    print("=" * 60)


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    clear_scene()
    build_all()
