

import bpy
import bmesh
import math


print("=" * 55)
print("=== BrewXOS Assembly v2 START ===")
print("=" * 55)

# ============================================================
# 工具函数 — 不依赖 bpy.ops，全走 bmesh
# ============================================================

def clear_scene():
    if bpy.context.active_object:
        bpy.ops.object.mode_set(mode='OBJECT')
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for mesh in list(bpy.data.meshes):
        bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)
    for coll in list(bpy.data.collections):
        if coll.name != bpy.context.scene.collection.name:
            bpy.data.collections.remove(coll)


def box(name, w, d, h, loc, mt):
    """底面中心在 loc, 返回新建物体"""
    m = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=2.0)  # 边长为2的立方体，原点在中心
    bm.to_mesh(m)
    bm.free()
    obj = bpy.data.objects.new(name, m)
    obj.location = (loc[0], loc[1], loc[2] + h / 2)
    obj.scale = (w / 2, d / 2, h / 2)
    obj.data.materials.append(mt)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def cyl(name, r, h, loc, mt, verts=48):
    m = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=verts,
                          radius1=r, radius2=r, depth=h)
    bm.to_mesh(m)
    bm.free()
    obj = bpy.data.objects.new(name, m)
    obj.location = (loc[0], loc[1], loc[2] + h / 2)
    obj.data.materials.append(mt)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def torus(name, R, r, loc, mt, segs=64, ring_segs=16):
    m = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    # bmesh 无原生 torus，用 Python 手算顶点
    verts, faces = [], []
    for i in range(ring_segs):
        a = 2 * math.pi * i / ring_segs
        for j in range(segs):
            b = 2 * math.pi * j / segs
            x = (R + r * math.cos(b)) * math.cos(a)
            y = (R + r * math.cos(b)) * math.sin(a)
            z = r * math.sin(b)
            verts.append((x, y, z))
    for i in range(ring_segs):
        for j in range(segs):
            i0 = i * segs + j
            i1 = i * segs + (j + 1) % segs
            i2 = ((i + 1) % ring_segs) * segs + (j + 1) % segs
            i3 = ((i + 1) % ring_segs) * segs + j
            faces.append((i0, i1, i2, i3))
    bm = bmesh.new()
    bverts = [bm.verts.new(v) for v in verts]
    bm.verts.ensure_lookup_table()
    for f in faces:
        bm.faces.new([bverts[k] for k in f])
    bm.to_mesh(m)
    bm.free()
    obj = bpy.data.objects.new(name, m)
    obj.location = loc
    obj.data.materials.append(mt)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ============================================================
# 材质
# ============================================================

M = {}

def make_mat(name, color, metallic=0.0, roughness=0.5, alpha=1.0):
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
    if alpha < 1.0:
        bsdf.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
    return m


def init_mat():
    global M
    M['s4'] = make_mat("Steel_4mm",  (0.14,0.14,0.15), 0.90,0.30)
    M['s2'] = make_mat("Steel_2mm",  (0.17,0.17,0.18), 0.85,0.35)
    M['al'] = make_mat("Aluminum",   (0.64,0.64,0.66), 0.95,0.25)
    M['gl'] = make_mat("Glass",      (0.55,0.82,0.76), 0.00,0.05,0.40)
    M['ss'] = make_mat("SS304",      (0.58,0.58,0.60), 0.90,0.28)
    M['pg'] = make_mat("PCB_Green",  (0.04,0.17,0.11), 0.00,0.55)
    M['pr'] = make_mat("PCB_Red",    (0.14,0.05,0.05), 0.00,0.55)
    M['pp'] = make_mat("PP",         (0.24,0.24,0.26), 0.00,0.50)
    M['si'] = make_mat("Silicone",   (0.74,0.44,0.24), 0.00,0.70)
    M['wo'] = make_mat("Wool",       (0.84,0.80,0.73), 0.00,0.88)
    M['rb'] = make_mat("Rubber",     (0.08,0.08,0.08), 0.00,0.92)
    M['sc'] = make_mat("ScreenOff",  (0.02,0.02,0.05), 0.10,0.20)
    M['so'] = make_mat("ScreenOn",   (0.10,0.40,0.33), 0.00,0.30)
    M['rd'] = make_mat("EStop",      (0.70,0.12,0.12), 0.08,0.40)
    M['bw'] = make_mat("BtnWhite",   (0.87,0.87,0.88), 0.08,0.40)
    M['ba'] = make_mat("BtnAmber",   (0.78,0.46,0.23), 0.15,0.38)
    M['lg'] = make_mat("LED_Green",  (0.08,0.85,0.25), 0.00,0.08)
    M['la'] = make_mat("LED_Amber",  (1.00,0.65,0.08), 0.00,0.08)
    M['mo'] = make_mat("Motor",      (0.43,0.43,0.45), 0.88,0.32)
    M['pu'] = make_mat("Pump",       (0.20,0.20,0.22), 0.08,0.52)
    M['cu'] = make_mat("Copper",     (0.82,0.62,0.32), 0.60,0.30)
    M['uv'] = make_mat("UVC",        (0.45,0.25,0.75), 0.00,0.08)
    M['liq']= make_mat("Liquid",     (0.65,0.50,0.20), 0.00,0.20,0.35)
    M['tu'] = make_mat("Tube",       (0.82,0.78,0.73), 0.00,0.48,0.80)


# ============================================================
# 整机装配
# ============================================================

def build():
    # 所有函数内部已 link，直接调用即可

    # ── 底板 350×350×4 ──
    box("P01_底板", 350, 350, 4, (0,0,0), M['s4'])

    # ── 支脚 ×4 ──
    for fx,fy in [(-160,-160),(160,-160),(-160,160),(160,160)]:
        cyl("P23_支脚",10,5,(fx,fy,-5),M['rb'])

    # ── 漏液托盘 ──
    box("P06_托盘",280,280,3,(0,0,4),M['pp'])
    cyl("P06_电极1",2,15,(-25,0,7),M['ss'])
    cyl("P06_电极2",2,15,(25,0,7),M['ss'])

    # ── 罐体支座 ──
    for ax,ay in [(-120,-120),(120,-120),(-120,120),(120,120)]:
        box("P08_立柱",20,20,25,(ax,ay,7),M['al'])
    for b in [-120,120]:
        box("P08_横梁X",240,20,20,(0,b,7),M['al'])
        box("P08_横梁Y",20,240,20,(b,0,7),M['al'])

    # ── 加热膜 + 保温棉 ──
    cyl("P09_加热膜",43,80,(0,0,32),M['si'],32)
    cyl("P10_保温棉",45,82,(0,0,31),M['wo'],24)

    # ── 发酵罐 ⌀80×100 ──
    cyl("P07_发酵罐",40,100,(0,0,32),M['gl'])
    cyl("液体",37,70,(0,0,47),M['liq'])

    # ── 罐盖 + KF16×6 ──
    cyl("P07_罐盖",42,6,(0,0,132),M['ss'])
    for i in range(6):
        a=i*math.pi/3; px=42*math.cos(a); py=42*math.sin(a)
        cyl(f"KF16_{i+1}",5,8,(px,py,135),M['ss'])

    # ── UV-C 灯环 ──
    torus("P18_UVC灯环",30,2,(0,0,130),M['uv'])

    # ── 电机 + 轴 + 密封 ──
    cyl("P11_电机",12,40,(0,0,145),M['mo'])
    cyl("P11_法兰",16,5,(0,0,138),M['al'])
    cyl("P12_搅拌轴",3,80,(0,0,58),M['ss'])
    cyl("P12_密封法兰",15,10,(0,0,128),M['ss'])

    # ── 桨叶 ×4 ──
    for pi in range(4):
        a=pi*math.pi/2; bx=25*math.cos(a); by=25*math.sin(a)
        box(f"P13_桨叶{pi+1}",36,4,24,(bx,by,55),M['ss'])

    # ── 过滤器 ×2 ──
    cyl("P17_过滤器1",12,40,(-30,0,148),M['pp'])
    cyl("P17_过滤器2",12,40,(30,0,148),M['pp'])

    # ── 主板 ──
    box("B1_主板",100,80,2,(0,-148,140),M['pg'])
    for nm,cx,cz,cw,cd in [("ESP32",-30,-15,22,16),("ADS1256",0,-10,14,14),
                            ("MAX31865",20,10,12,10),("PT100",-20,16,10,8)]:
        box(f"IC_{nm}",cw,cd,2,(cx,-148+cz,142),M['cu'])

    # ── 驱动板 ──
    box("B2_驱动板",100,80,2,(0,110,10),M['pr'])
    for nm,dx,dz,dw,dd in [("SSR",-30,-15,22,22),("Relay",10,-10,14,12),
                            ("DCDC",20,10,12,10),("LDO",-10,16,10,8)]:
        box(f"D_{nm}",dw,dd,3,(dx,110+dz,12),M['cu'])
    box("SSR散热片",30,30,10,(-30,96,14),M['al'])

    # ── 外壳四壁 (已去除) ──

    # ── TFT ──
    box("TFT_框",74,58,5,(0,-173,350),M['sc'])
    box("TFT_显示",66,50,.5,(0,-173,353),M['so'])

    # ── 急停 ──
    cyl("急停_底座",15,10,(120,-174,365),M['rd'])
    cyl("急停_蘑菇头",18,6,(120,-176,372),M['rd'])

    # ── 按钮 ×3 + LED ×3 ──
    for bi,bx in enumerate([-50,0,50]):
        cyl(f"按钮{bi+1}",10,6,(bx,-175,390),
            [M['bw'],M['ba'],M['bw']][bi])
    for li,lx in enumerate([-110,-80,-50]):
        cyl(f"LED{li+1}",2.5,2,(lx,-174,398),
            [M['lg'],M['la'],M['lg']][li])

    # ── 泵组 ×3 ──
    for pi,pn in enumerate(["酸液泵","碱液泵","补料泵"]):
        py=-60+pi*60
        box(f"P14_支架{pi+1}",10,40,50,(-145,py,4),M['al'])
        box(f"P15_{pn}",50,40,30,(-115,py,29),M['pu'])
        cyl(f"P15_{pn}_泵头",12,12,(-90,py,39),M['pp'])

    # ── 气泵 ──
    box("P16_气泵",40,30,25,(-125,90,4),M['pu'])

    # ── 流量计 ──
    cyl("P19_流量计",10,60,(185,0,10),M['gl'])

    # ── 管路 ──
    cyl("管路_酸液",3,80,(-90,-30,49),M['tu'])
    cyl("管路_碱液",3,80,(-90,30,49),M['tu'])
    cyl("管路_补料",3,80,(-90,90,49),M['tu'])

    print(f"  零件总数: {len(bpy.data.objects)}")


# ============================================================
# 场景
# ============================================================

def setup_scene():
    bpy.ops.object.camera_add(location=(420,-650,320))
    cam=bpy.context.active_object; cam.name="Camera_Main"
    cam.rotation_euler=(math.radians(64),0,math.radians(58))
    bpy.context.scene.camera=cam

    bpy.ops.object.light_add(type='AREA', location=(300,-600,500))
    bpy.context.active_object.data.energy=800
    bpy.context.active_object.data.size=600

    bpy.ops.object.light_add(type='AREA', location=(-200,300,350))
    bpy.context.active_object.data.energy=400
    bpy.context.active_object.data.size=400

    bpy.context.scene.render.engine='CYCLES'
    bpy.context.scene.cycles.samples=128
    bpy.context.scene.render.resolution_x=1920
    bpy.context.scene.render.resolution_y=1080

    w=bpy.context.scene.world; w.use_nodes=True
    w.node_tree.nodes['Background'].inputs['Color'].default_value=(0.89,0.87,0.83,1.0)
    w.node_tree.nodes['Background'].inputs['Strength'].default_value=0.25


# ============================================================
# 入口
# ============================================================

clear_scene()
init_mat()
build()
setup_scene()

