"""
BrewXOS Fermenter Mini - Blender 双版建模
============================================
左侧：25 组零部件拆解爆炸图 (间距 150mm)
右侧：完整整机装配 (X=700)
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
    for c in list(bpy.data.collections):
        if c.name != "Collection":
            bpy.data.collections.remove(c)


def mat(name, color, metallic=0.0, roughness=0.5, alpha=1.0):
    m = bpy.data.materials.new(name=name)
    m.use_nodes = True
    bsdf = None
    for n in m.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            bsdf = n; break
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
    """loc = 底面中心"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(loc[0], loc[1], loc[2]+h/2))
    o = bpy.context.active_object
    o.name = name; o.scale = (w/2, d/2, h/2); o.data.materials.append(mt)
    return o


def cyl(name, r, h, loc, mt, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, vertices=verts,
        location=(loc[0], loc[1], loc[2]+h/2))
    o = bpy.context.active_object; o.name = name; o.data.materials.append(mt)
    return o


def torus(name, R, r, loc, mt):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc)
    o = bpy.context.active_object; o.name = name; o.data.materials.append(mt)
    return o


# ============================================================
# 材质
# ============================================================

M = {}
def init_mat():
    global M
    M['s4'] = mat("Steel_4mm",  (0.14,0.14,0.15), 0.90,0.30)
    M['s2'] = mat("Steel_2mm",  (0.17,0.17,0.18), 0.85,0.35)
    M['al'] = mat("Aluminum",   (0.64,0.64,0.66), 0.95,0.25)
    M['gl'] = mat("Glass_GG17", (0.55,0.82,0.76), 0.00,0.05,0.40)
    M['ss'] = mat("SS304",      (0.58,0.58,0.60), 0.90,0.28)
    M['pg'] = mat("PCB_Green",  (0.04,0.17,0.11), 0.00,0.55)
    M['pr'] = mat("PCB_Red",    (0.14,0.05,0.05), 0.00,0.55)
    M['pp'] = mat("PP_Plastic", (0.24,0.24,0.26), 0.00,0.50)
    M['si'] = mat("Silicone",   (0.74,0.44,0.24), 0.00,0.70)
    M['wo'] = mat("Insul_Wool", (0.84,0.80,0.73), 0.00,0.88)
    M['rb'] = mat("Rubber",     (0.08,0.08,0.08), 0.00,0.92)
    M['sc'] = mat("Screen",     (0.02,0.02,0.05), 0.10,0.20)
    M['so'] = mat("Screen_On",  (0.10,0.40,0.33), 0.00,0.30)
    M['rd'] = mat("EStop_Red",  (0.70,0.12,0.12), 0.08,0.40)
    M['bw'] = mat("Btn_White",  (0.87,0.87,0.88), 0.08,0.40)
    M['ba'] = mat("Btn_Amber",  (0.78,0.46,0.23), 0.15,0.38)
    M['lg'] = mat("LED_Green",  (0.08,0.85,0.25), 0.00,0.08)
    M['la'] = mat("LED_Amber",  (1.00,0.65,0.08), 0.00,0.08)
    M['mo'] = mat("Motor",      (0.43,0.43,0.45), 0.88,0.32)
    M['pu'] = mat("Pump",       (0.20,0.20,0.22), 0.08,0.52)
    M['cu'] = mat("Copper",     (0.82,0.62,0.32), 0.60,0.30)
    M['uv'] = mat("UVC",        (0.45,0.25,0.75), 0.00,0.08)
    M['liq']= mat("Liquid",     (0.65,0.50,0.20), 0.00,0.20,0.35)
    M['tu'] = mat("Tube",       (0.82,0.78,0.73), 0.00,0.48,0.80)


# ============================================================
# 左：拆解爆炸图
# ============================================================

def build_exploded(root):
    GAP = 150
    y = -900

    def coll(name):
        c = bpy.data.collections.new(name)
        root.children.link(c)
        return c

    # 01 底板 + 支脚
    c = coll("01_底板")
    box("P01_底板_350x350x4", 350,350,4, (0,y,0), M['s4']);        c.objects.link(bpy.context.active_object)
    for fx,fy in [(-160,-160),(160,-160),(-160,160),(160,160)]:
        cyl("P23_支脚_D20x5",10,5,(fx,fy+y,-5),M['rb']);          c.objects.link(bpy.context.active_object)
    y += GAP

    # 02 漏液托盘
    c = coll("02_漏液托盘")
    box("P06_托盘_280x280x3",280,280,3,(0,y,0),M['pp']);          c.objects.link(bpy.context.active_object)
    for ex in [-25,25]:
        cyl("P06_电极",2,15,(ex,y,3),M['ss']);                     c.objects.link(bpy.context.active_object)
    y += GAP

    # 03 罐体支座
    c = coll("03_罐体支座")
    for ax,ay in [(-120,-120),(120,-120),(-120,120),(120,120)]:
        box("P08_立柱_20x20x25",20,20,25,(ax,ay+y,0),M['al']);     c.objects.link(bpy.context.active_object)
    for bx in [-120,120]:
        box("P08_横梁_240x20x20",240,20,20,(0,bx+y,0),M['al']);    c.objects.link(bpy.context.active_object)
    for by in [-120,120]:
        box("P08_横梁_20x240x20",20,240,20,(by,y,0),M['al']);      c.objects.link(bpy.context.active_object)
    y += GAP

    # 04 加热膜
    c = coll("04_加热膜")
    cyl("P09_加热膜_50W",43,80,(0,y,0),M['si'],32);               c.objects.link(bpy.context.active_object)
    y += GAP

    # 05 保温棉
    c = coll("05_保温棉")
    cyl("P10_保温棉_1cm",45,82,(0,y,0),M['wo'],24);               c.objects.link(bpy.context.active_object)
    y += GAP

    # 06 发酵罐
    c = coll("06_发酵罐")
    cyl("P07_发酵罐_D80x100",40,100,(0,y,0),M['gl']);             c.objects.link(bpy.context.active_object)
    cyl("液体内容物",37,70,(0,y,15),M['liq']);                     c.objects.link(bpy.context.active_object)
    y += GAP

    # 07 罐盖 + KF16×6
    c = coll("07_罐盖法兰")
    cyl("P07_罐盖_D84x6",42,6,(0,y,0),M['ss']);                   c.objects.link(bpy.context.active_object)
    for i in range(6):
        a=i*math.pi/3; px=42*math.cos(a); pz=42*math.sin(a)
        cyl(f"KF16_{i+1}_D10x8",5,8,(px,y,pz+3),M['ss']);          c.objects.link(bpy.context.active_object)
    y += GAP

    # 08 UV-C 灯环
    c = coll("08_UVC灯环")
    torus("P18_UVC_D60",30,2,(0,y,0),M['uv']);                     c.objects.link(bpy.context.active_object)
    y += GAP

    # 09 搅拌电机
    c = coll("09_搅拌电机")
    cyl("P11_JGB37_D24x40",12,40,(0,y,0),M['mo']);                 c.objects.link(bpy.context.active_object)
    cyl("P11_法兰_D32x5",16,5,(0,y,-5),M['al']);                   c.objects.link(bpy.context.active_object)
    y += GAP

    # 10 搅拌轴 + 密封
    c = coll("10_搅拌轴")
    cyl("P12_磁力轴_D6x80",3,80,(0,y,0),M['ss']);                  c.objects.link(bpy.context.active_object)
    cyl("P12_密封法兰_D30x10",15,10,(0,y,-10),M['ss']);            c.objects.link(bpy.context.active_object)
    y += GAP

    # 11 四叶桨叶
    c = coll("11_桨叶")
    for pi in range(4):
        a=pi*math.pi/2; bx=25*math.cos(a); bz=25*math.sin(a)
        box(f"P13_桨叶{pi+1}",36,4,24,(bx,y+bz,0),M['ss']);        c.objects.link(bpy.context.active_object)
    cyl("P13_轴套_D10x20",5,20,(0,y,0),M['ss']);                   c.objects.link(bpy.context.active_object)
    y += GAP

    # 12 空气过滤器 ×2
    c = coll("12_过滤器")
    for fx in [-30,30]:
        cyl(f"P17_过滤器_D25x40",12,40,(fx,y,0),M['pp']);          c.objects.link(bpy.context.active_object)
    y += GAP

    # 13 主板
    c = coll("13_主板")
    box("Board1_主板_100x80",100,80,1.6,(0,y,0),M['pg']);          c.objects.link(bpy.context.active_object)
    for nm,cx,cz,cw,cd in [("ESP32",-35,-20,22,16),("ADS1256",0,-15,14,14),
        ("MAX31865",20,5,12,10),("PT100",-20,15,10,8)]:
        box(f"IC_{nm}",cw,cd,2,(cx,y+cz,1.6),M['cu']);             c.objects.link(bpy.context.active_object)
    y += GAP

    # 14 驱动板
    c = coll("14_驱动板")
    box("Board2_驱动板_100x80",100,80,1.6,(0,y,0),M['pr']);        c.objects.link(bpy.context.active_object)
    for nm,dx,dz,dw,dd in [("SSR",-30,-15,22,22),("Relay",10,-10,14,12),
        ("DCDC",20,10,12,10),("LDO",-10,20,10,8)]:
        box(f"D_{nm}",dw,dd,3,(dx,y+dz,1.6),M['cu']);              c.objects.link(bpy.context.active_object)
    box("SSR散热片",30,30,10,(-30,y-15,3),M['al']);                c.objects.link(bpy.context.active_object)
    y += GAP

    # 15 排线
    c = coll("15_排线")
    box("排线_20P_20cm",18,2,200,(0,y,0),M['ba']);                  c.objects.link(bpy.context.active_object)
    y += GAP

    # 16 前面板
    c = coll("16_前面板")
    box("P03_前面板_350x130x2",350,2,130,(0,y,0),M['s2']);          c.objects.link(bpy.context.active_object)
    y += GAP

    # 17 后盖板
    c = coll("17_后盖板")
    box("P04_后盖板_350x130x2",350,2,130,(0,y,0),M['s2']);          c.objects.link(bpy.context.active_object)
    y += GAP

    # 18 侧板 ×2
    c = coll("18_侧板")
    box("P05_左侧板_450x130x2",2,130,450,(-176,y,0),M['s2']);       c.objects.link(bpy.context.active_object)
    box("P05_右侧板_450x130x2",2,130,450,(176,y,0),M['s2']);        c.objects.link(bpy.context.active_object)
    y += GAP

    # 19 顶盖
    c = coll("19_顶盖")
    box("P02_顶盖_350x350x2",350,350,2,(0,y,0),M['s2']);            c.objects.link(bpy.context.active_object)
    y += GAP

    # 20 TFT 屏幕
    c = coll("20_TFT屏幕")
    box("TFT_屏幕框_74x58x5",74,58,5,(0,y,0),M['sc']);              c.objects.link(bpy.context.active_object)
    box("TFT_显示区_66x50",66,50,.5,(0,y,2.5),M['so']);             c.objects.link(bpy.context.active_object)
    y += GAP

    # 21 急停按钮
    c = coll("21_急停按钮")
    cyl("急停_底座_D30x10",15,10,(0,y,0),M['rd']);                  c.objects.link(bpy.context.active_object)
    cyl("急停_蘑菇头_D36x6",18,6,(0,y,10),M['rd']);                 c.objects.link(bpy.context.active_object)
    y += GAP

    # 22 按钮 + LED
    c = coll("22_按钮LED")
    for bi,bx in enumerate([-40,0,40]):
        mtb = [M['bw'],M['ba'],M['bw']][bi]
        cyl(f"按钮{bi+1}_D20x6",10,6,(bx,y,0),mtb);                 c.objects.link(bpy.context.active_object)
    for li,lx in enumerate([-90,-60,-30]):
        mtl = [M['lg'],M['la'],M['lg']][li]
        cyl(f"LED_{['RUN','ALM','PWR'][li]}_D4",2,2,(lx,y,8),mtl);  c.objects.link(bpy.context.active_object)
    y += GAP

    # 23 泵组
    c = coll("23_泵组")
    for pi,pn in enumerate(["酸液泵","碱液泵","补料泵"]):
        px=-100+pi*100
        box(f"P14_支架{pi+1}",10,40,50,(px-30,y,0),M['al']);        c.objects.link(bpy.context.active_object)
        box(f"P15_{pn}_50x40x30",50,40,30,(px,y,25),M['pu']);       c.objects.link(bpy.context.active_object)
        cyl(f"P15_{pn}_泵头_D24x12",12,12,(px+25,y,35),M['pp']);    c.objects.link(bpy.context.active_object)
    box("P16_气泵_40x30x25",40,30,25,(-150,y,0),M['pu']);           c.objects.link(bpy.context.active_object)
    cyl("P19_流量计_D20x60",10,60,(150,y,15),M['gl']);               c.objects.link(bpy.context.active_object)
    y += GAP

    # 24 管路
    c = coll("24_管路")
    for ti in range(5):
        cyl(f"P20_硅胶管{ti+1}",3,100,(-50+ti*25,y,0),M['tu']);     c.objects.link(bpy.context.active_object)
    y += GAP

    # 25 紧固件
    c = coll("25_紧固件")
    for ni in range(8):
        cyl(f"P21_尼龙柱{ni+1}_M3x10",2,10,(-35+ni*10,y,0),M['pp']); c.objects.link(bpy.context.active_object)
    for si in range(20):
        cyl(f"P22_M4螺丝{si+1}",2,10,(-95+si*10,y,15),M['ss']);     c.objects.link(bpy.context.active_object)


# ============================================================
# 右：整机装配 (X = 700)
# ============================================================

def build_assembled(root):
    AX = 700  # 组装版 X 偏移
    c = bpy.data.collections.new("ASM_整机装配")
    root.children.link(c)

    # --- 底板 P-01 (350×350×4mm) ---
    box("ASM_P01_底板", 350,350,4, (AX,0,0), M['s4'])
    c.objects.link(bpy.context.active_object)

    # --- 支脚 P-23 (4×) ---
    for fx,fy in [(-160,-160),(160,-160),(-160,160),(160,160)]:
        cyl("ASM_P23_支脚", 10,5, (AX+fx,fy,-5), M['rb'])
        c.objects.link(bpy.context.active_object)

    # --- 漏液托盘 P-06 ---
    box("ASM_P06_托盘", 280,280,3, (AX,0,4), M['pp'])
    c.objects.link(bpy.context.active_object)

    # --- 罐体支座 P-08 (2020铝型材，高25mm) ---
    for ax,ay in [(-120,-120),(120,-120),(-120,120),(120,120)]:
        box("ASM_P08_立柱", 20,20,25, (AX+ax,ay,7), M['al'])
        c.objects.link(bpy.context.active_object)
    for bx in [-120,120]:
        box("ASM_P08_横梁", 240,20,20, (AX,bx,7), M['al'])
        c.objects.link(bpy.context.active_object)
    for by in [-120,120]:
        box("ASM_P08_横梁2", 20,240,20, (AX+by,0,7), M['al'])
        c.objects.link(bpy.context.active_object)

    # --- 加热膜 P-09 (绕罐) + 保温棉 P-10 ---
    cyl("ASM_P09_加热膜", 43,80, (AX,0,32), M['si'],32)
    c.objects.link(bpy.context.active_object)
    cyl("ASM_P10_保温棉", 45,82, (AX,0,31), M['wo'],24)
    c.objects.link(bpy.context.active_object)

    # --- 发酵罐 P-07 (⌀80×100 玻璃) ---
    cyl("ASM_P07_发酵罐", 40,100, (AX,0,32), M['gl'])
    c.objects.link(bpy.context.active_object)
    cyl("ASM_液体", 37,70, (AX,0,47), M['liq'])
    c.objects.link(bpy.context.active_object)

    # --- 罐盖 + KF16×6 ---
    cyl("ASM_罐盖_D84x6", 42,6, (AX,0,132), M['ss'])
    c.objects.link(bpy.context.active_object)
    for i in range(6):
        a=i*math.pi/3; px=42*math.cos(a); py=42*math.sin(a)
        cyl(f"ASM_KF16_{i+1}", 5,8, (AX+px,py,135), M['ss'])
        c.objects.link(bpy.context.active_object)

    # --- UV-C 灯环 P-18 (罐盖内圈) ---
    torus("ASM_P18_UVC", 30,2, (AX,0,130), M['uv'])
    c.objects.link(bpy.context.active_object)

    # --- 搅拌电机 P-11 + 轴 P-12 + 桨叶 P-13 ---
    cyl("ASM_P11_电机", 12,40, (AX,0,145), M['mo'])
    c.objects.link(bpy.context.active_object)
    cyl("ASM_P11_法兰", 16,5, (AX,0,138), M['al'])
    c.objects.link(bpy.context.active_object)
    cyl("ASM_P12_搅拌轴", 3,80, (AX,0,58), M['ss'])
    c.objects.link(bpy.context.active_object)
    cyl("ASM_P12_密封法兰", 15,10, (AX,0,128), M['ss'])
    c.objects.link(bpy.context.active_object)
    for pi in range(4):
        a=pi*math.pi/2; bx=25*math.cos(a); by=25*math.sin(a)
        box(f"ASM_P13_桨叶{pi+1}", 36,4,24, (AX+bx,by,55), M['ss'])
        c.objects.link(bpy.context.active_object)

    # --- 空气过滤器 P-17 ×2 (罐盖上方两侧) ---
    cyl("ASM_P17_过滤器1", 12,40, (AX-30,0,148), M['pp'])
    c.objects.link(bpy.context.active_object)
    cyl("ASM_P17_过滤器2", 12,40, (AX+30,0,148), M['pp'])
    c.objects.link(bpy.context.active_object)

    # --- 主板 Board1 (前面板内侧, Y=-160, Z=140) ---
    box("ASM_Board1_主板", 100,80,1.6, (AX, -160, 140), M['pg'])
    c.objects.link(bpy.context.active_object)
    for nm,cx,cz,cw,cd in [("ESP32",-30,-15,22,16),("ADS1256",0,-10,14,14),
        ("MAX31865",20,10,12,10),("PT100",-20,16,10,8)]:
        box(f"ASM_IC_{nm}", cw,cd,2, (AX+cx, -160+cz, 141.6), M['cu'])
        c.objects.link(bpy.context.active_object)

    # --- 驱动板 Board2 (底板后部, Y=120, Z=10) ---
    box("ASM_Board2_驱动板", 100,80,1.6, (AX, 120, 10), M['pr'])
    c.objects.link(bpy.context.active_object)
    for nm,dx,dz,dw,dd in [("SSR",-30,-15,22,22),("Relay",10,-10,14,12),
        ("DCDC",20,10,12,10),("LDO",-10,16,10,8)]:
        box(f"ASM_D_{nm}", dw,dd,3, (AX+dx, 120+dz, 11.6), M['cu'])
        c.objects.link(bpy.context.active_object)
    box("ASM_SSR散热片", 30,30,10, (AX-30, 106, 13), M['al'])
    c.objects.link(bpy.context.active_object)

    # --- 机箱外壳 (完整围合) ---
    # 左侧板: X=AX-174, 从 Y=-174 到 Y=174, Z=4 到 454
    box("ASM_P05_左侧板", 2, 348, 450, (AX-174, 0, 4), M['s2'])
    c.objects.link(bpy.context.active_object)
    # 右侧板: X=AX+174
    box("ASM_P05_右侧板", 2, 348, 450, (AX+174, 0, 4), M['s2'])
    c.objects.link(bpy.context.active_object)

    # 前面板: Y=-174, 从 X=AX-174 到 X=AX+174, Z=324 到 454
    box("ASM_P03_前面板", 348, 2, 130, (AX, -174, 324), M['s2'])
    c.objects.link(bpy.context.active_object)

    # 后盖板: Y=174, Z=324 到 454
    box("ASM_P04_后盖板", 348, 2, 130, (AX, 174, 324), M['s2'])
    c.objects.link(bpy.context.active_object)

    # 顶盖: Z=452
    box("ASM_P02_顶盖", 350, 350, 2, (AX, 0, 452), M['s2'])
    c.objects.link(bpy.context.active_object)

    # --- TFT 屏幕 (前面板外侧) ---
    box("ASM_TFT_框", 74,58,5, (AX, -173, 350), M['sc'])
    c.objects.link(bpy.context.active_object)
    box("ASM_TFT_显示", 66,50,.5, (AX, -173, 353), M['so'])
    c.objects.link(bpy.context.active_object)

    # --- 急停按钮 (前面板右上) ---
    cyl("ASM_急停_底座", 15,10, (AX+120, -174, 365), M['rd'])
    c.objects.link(bpy.context.active_object)
    cyl("ASM_急停_蘑菇头", 18,6, (AX+120, -176, 372), M['rd'])
    c.objects.link(bpy.context.active_object)

    # --- 操作按钮 ×3 + LED ×3 ---
    for bi,bx in enumerate([-50,0,50]):
        mtb=[M['bw'],M['ba'],M['bw']][bi]
        cyl(f"ASM_按钮{bi+1}", 10,6, (AX+bx, -175, 390), mtb)
        c.objects.link(bpy.context.active_object)
    for li,lx in enumerate([-120,-90,-60]):
        mtl=[M['lg'],M['la'],M['lg']][li]
        cyl(f"ASM_LED{li+1}", 2,2, (AX+lx, -174, 398), mtl)
        c.objects.link(bpy.context.active_object)

    # --- 蠕动泵 ×3 (底板左侧后部) ---
    for pi,pn in enumerate(["酸液泵","碱液泵","补料泵"]):
        py=-60+pi*60
        box(f"ASM_P14_支架{pi+1}", 10,40,50, (AX-145, py, 4), M['al'])
        c.objects.link(bpy.context.active_object)
        box(f"ASM_P15_{pn}", 50,40,30, (AX-115, py, 29), M['pu'])
        c.objects.link(bpy.context.active_object)
        cyl(f"ASM_P15_{pn}_泵头", 12,12, (AX-90, py, 39), M['pp'])
        c.objects.link(bpy.context.active_object)

    # --- 气泵 P-16 ---
    box("ASM_P16_气泵", 40,30,25, (AX-130, 100, 4), M['pu'])
    c.objects.link(bpy.context.active_object)

    # --- 流量计 P-19 (右侧外挂) ---
    cyl("ASM_P19_流量计", 10,60, (AX+185, 0, 20), M['gl'])
    c.objects.link(bpy.context.active_object)

    # --- 管路 ---
    cyl("ASM_管路1", 3,80, (AX-90, -40, 49), M['tu'])
    c.objects.link(bpy.context.active_object)
    cyl("ASM_管路2", 3,80, (AX-90, 20, 49), M['tu'])
    c.objects.link(bpy.context.active_object)


# ============================================================
# 场景设置
# ============================================================

def setup_scene():
    AX = 700

    # 相机：居中俯瞰双版
    bpy.ops.object.camera_add(location=(AX/2+80, -1000, 500))
    cam = bpy.context.active_object
    cam.name = "Camera_Main"
    cam.rotation_euler = (math.radians(58), 0, math.radians(90))
    bpy.context.scene.camera = cam

    # 组装版特写
    bpy.ops.object.camera_add(location=(AX, -400, 280))
    cam2 = bpy.context.active_object
    cam2.name = "Camera_Assembly"
    cam2.rotation_euler = (math.radians(72), 0, math.radians(90))

    # 拆解版俯视
    bpy.ops.object.camera_add(location=(0, -800, 800))
    cam3 = bpy.context.active_object
    cam3.name = "Camera_Top"
    cam3.rotation_euler = (0, 0, 0)

    # 灯光
    bpy.ops.object.light_add(type='AREA', location=(AX/2, -1200, 700))
    bpy.context.active_object.data.energy = 800
    bpy.context.active_object.data.size = 600

    bpy.ops.object.light_add(type='AREA', location=(AX/2, -1200, 300))
    bpy.context.active_object.data.energy = 350
    bpy.context.active_object.data.size = 500

    bpy.ops.object.light_add(type='AREA', location=(-300, -300, 600))
    bpy.context.active_object.data.energy = 200
    bpy.context.active_object.data.size = 300

    # 渲染
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

    world = bpy.context.scene.world
    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.92, 0.90, 0.86, 1.0)
    bg.inputs['Strength'].default_value = 0.3


# ============================================================
# 入口
# ============================================================

if __name__ == "__main__":
    clear_scene()
    init_mat()
    root = bpy.context.scene.collection

    print("=" * 60)
    print("BrewXOS Fermenter Mini - 双版建模")
    print("  拆解爆炸图: 25组零件, Y轴间距150mm")
    print("  整机装配:   完整机箱围合, X=700")
    print("=" * 60)

    build_exploded(root)
    build_assembled(root)
    setup_scene()

    print("完成! Numpad 0=全景, 选Camera_Assembly→Numpad 0=组装特写")
    print("=" * 60)
