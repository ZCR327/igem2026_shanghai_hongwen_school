

import bpy
import math
import os

# ============================================================
# 工具函数
# ============================================================

def clear_scene():
    """清空场景"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    # 清空材质
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)

def make_material(name, color, metallic=0.0, roughness=0.5, alpha=1.0, use_nodes=True):
    """创建 PBR 材质（兼容 Blender 3.x / 4.x）"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = use_nodes
    if use_nodes:
        # 兼容不同 Blender 版本：按类型查找 BSDF 节点
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

def make_bbox(name, size, location, material):
    """创建立方体"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0]/2, size[1]/2, size[2]/2)
    obj.data.materials.append(material)
    return obj

def make_cylinder(name, radius, depth, location, material):
    """创建圆柱体"""
    bpy.ops.mesh.primitive_cylinder_add(
        radius=radius, depth=depth, location=location, vertices=64
    )
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material)
    return obj

def make_rounded_box(name, size, location, material, radius=2):
    """创建有倒角的盒子（用 Bevel 修改器）"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0]/2, size[1]/2, size[2]/2)
    obj.data.materials.append(material)
    # 加 Bevel
    bpy.ops.object.modifier_add(type='BEVEL')
    obj.modifiers['Bevel'].width = radius * 0.001  # mm 转 m
    obj.modifiers['Bevel'].segments = 3
    bpy.ops.object.modifier_apply(modifier='Bevel')
    return obj

def make_flat_box(name, size, location, material):
    """创建扁平盒子（底面在 z=0 位置）"""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(
        location[0], location[1], location[2] + size[2]/2
    ))
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (size[0]/2, size[1]/2, size[2]/2)
    obj.data.materials.append(material)
    return obj

def add_bevel(obj, width=0.002, segments=3):
    """给对象添加倒角"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_add(type='BEVEL')
    obj.modifiers['Bevel'].width = width
    obj.modifiers['Bevel'].segments = segments


# ============================================================
# 主建模函数
# ============================================================

def create_all():
    """创建 BrewXOS Fermenter Mini 完整模型"""

    print("=" * 60)
    print("BrewXOS Fermenter Mini - Blender 建模开始")
    print("外型尺寸: 350 x 350 x 450 mm")
    print("=" * 60)

    # --- 材质 ---
    mat_steel_4mm = make_material("Steel_4mm_Base", (0.15, 0.15, 0.16), metallic=0.9, roughness=0.3)
    mat_steel_2mm = make_material("Steel_2mm_Panel", (0.18, 0.18, 0.19), metallic=0.85, roughness=0.35)
    mat_aluminum = make_material("Aluminum_2020", (0.65, 0.65, 0.67), metallic=0.95, roughness=0.25)
    mat_glass = make_material("Glass_GG17", (0.6, 0.85, 0.8), metallic=0.0, roughness=0.05, alpha=0.45)
    mat_pcb_green = make_material("PCB_Green", (0.05, 0.18, 0.12), metallic=0.0, roughness=0.6)
    mat_pcb_red = make_material("PCB_Red", (0.16, 0.06, 0.06), metallic=0.0, roughness=0.6)
    mat_heater = make_material("Heater_Silicone", (0.75, 0.45, 0.25), metallic=0.0, roughness=0.7)
    mat_insulation = make_material("Insulation_Wool", (0.85, 0.82, 0.75), metallic=0.0, roughness=0.9)
    mat_plastic = make_material("Plastic_PP", (0.25, 0.25, 0.27), metallic=0.0, roughness=0.5)
    mat_screen = make_material("TFT_Screen", (0.02, 0.02, 0.05), metallic=0.1, roughness=0.2)
    mat_screen_active = make_material("TFT_Active", (0.12, 0.42, 0.35), metallic=0.0, roughness=0.3)
    mat_rubber = make_material("Rubber_Foot", (0.1, 0.1, 0.1), metallic=0.0, roughness=0.9)
    mat_red_button = make_material("EStop_Red", (0.72, 0.15, 0.15), metallic=0.1, roughness=0.4)
    mat_button = make_material("Button", (0.88, 0.88, 0.89), metallic=0.1, roughness=0.4)
    mat_accent = make_material("Accent_Amber", (0.79, 0.48, 0.25), metallic=0.2, roughness=0.4)
    mat_led_green = make_material("LED_Green", (0.1, 0.9, 0.3), metallic=0.0, roughness=0.1)
    mat_led_amber = make_material("LED_Amber", (1.0, 0.7, 0.1), metallic=0.0, roughness=0.1)
    mat_motor = make_material("Motor_Metal", (0.45, 0.45, 0.47), metallic=0.9, roughness=0.3)
    mat_stainless = make_material("Stainless_304", (0.62, 0.62, 0.64), metallic=0.9, roughness=0.25)
    mat_pump = make_material("Pump_Body", (0.22, 0.22, 0.24), metallic=0.1, roughness=0.5)
    mat_tubing = make_material("Tubing_Silicone", (0.85, 0.82, 0.78), metallic=0.0, roughness=0.5, alpha=0.85)
    mat_copper = make_material("Copper_Trace", (0.85, 0.65, 0.35), metallic=0.6, roughness=0.3)

    # --- 集合 ---
    chassis_coll = bpy.data.collections.new("01_Chassis")
    vessel_coll = bpy.data.collections.new("02_Vessel")
    electronics_coll = bpy.data.collections.new("03_Electronics")
    front_coll = bpy.data.collections.new("04_FrontPanel")
    pumps_coll = bpy.data.collections.new("05_Pumps")
    bpy.context.scene.collection.children.link(chassis_coll)
    bpy.context.scene.collection.children.link(vessel_coll)
    bpy.context.scene.collection.children.link(electronics_coll)
    bpy.context.scene.collection.children.link(front_coll)
    bpy.context.scene.collection.children.link(pumps_coll)

    # ========================================================
    # 01 机箱 Chassis
    # ========================================================
    print("[1/5] 构建机箱...")

    # 底板 P-01: 350×350×4 mm
    base = make_bbox("P01_BasePlate", (350, 350, 4), (0, 0, 2), mat_steel_4mm)
    chassis_coll.objects.link(base)

    # 4× 支脚 P-23: ⌀20×5 mm
    for fx, fy in [(-160, -160), (160, -160), (-160, 160), (160, 160)]:
        foot = make_cylinder("P23_Foot", 10, 5, (fx, fy, -2.5), mat_rubber)
        chassis_coll.objects.link(foot)

    # 侧板 P-05 (左右): 450×130×2 mm at x=±174
    for sx, sname in [(-174, "P05_LeftPanel"), (174, "P05_RightPanel")]:
        side = make_flat_box(sname, (2, 130, 450), (sx, 0, 4), mat_steel_2mm)
        chassis_coll.objects.link(side)

    # 前面板 P-03: 350×130×2 at y=-174
    front = make_flat_box("P03_FrontPanel", (350, 2, 130), (0, -174, 324), mat_steel_2mm)
    chassis_coll.objects.link(front)

    # 后盖板 P-04: 350×130×2 at y=174
    back = make_flat_box("P04_BackPanel", (350, 2, 130), (0, 174, 324), mat_steel_2mm)
    chassis_coll.objects.link(back)

    # 顶盖 P-02: 350×350×2 at z=452
    top = make_flat_box("P02_TopCover", (350, 350, 2), (0, 0, 452), mat_steel_2mm)
    chassis_coll.objects.link(top)

    # ========================================================
    # 02 罐体与加热 Vessel
    # ========================================================
    print("[2/5] 构建罐体系统...")

    # 漏液托盘 P-06: 280×280×3 mm
    tray = make_bbox("P06_LeakTray", (280, 280, 3), (0, 0, 5.5), mat_plastic)
    vessel_coll.objects.link(tray)

    # 罐体支座 P-08: 2020铝型材框架 240×240×25
    for ax, ay in [(-120, -120), (120, -120), (-120, 120), (120, 120)]:
        pillar = make_bbox("P08_Frame", (20, 20, 25), (ax, ay, 19.5), mat_aluminum)
        vessel_coll.objects.link(pillar)
    # 横梁
    for bx in [-120, 120]:
        beam = make_bbox("P08_Beam", (240, 20, 20), (0, bx, 12), mat_aluminum)
        vessel_coll.objects.link(beam)

    # 加热膜 P-09: 绕罐体外壁, 近似为圆柱壳
    bpy.ops.mesh.primitive_cylinder_add(radius=43, depth=80, location=(0, 0, 65), vertices=32)
    heater = bpy.context.active_object
    heater.name = "P09_HeaterFilm"
    heater.data.materials.append(mat_heater)
    heater.scale = (1, 1, 0.02)
    vessel_coll.objects.link(heater)

    # 保温棉 P-10: 包裹加热膜
    bpy.ops.mesh.primitive_cylinder_add(radius=45, depth=82, location=(0, 0, 65), vertices=32)
    insulation = bpy.context.active_object
    insulation.name = "P10_Insulation"
    insulation.data.materials.append(mat_insulation)
    insulation.scale = (1, 1, 0.015)
    vessel_coll.objects.link(insulation)

    # 发酵罐 P-07: ⌀80×100 mm GG-17 玻璃圆柱
    vessel = make_cylinder("P07_Vessel", 40, 100, (0, 0, 65), mat_glass)
    vessel_coll.objects.link(vessel)

    # 罐内液体（可视化）
    liquid = make_cylinder("Liquid_Content", 38, 70, (0, 0, 55), make_material("Liquid", (0.7, 0.55, 0.25), alpha=0.4))
    vessel_coll.objects.link(liquid)

    # 罐盖 P-08法兰盖: ⌀84×6 mm
    lid = make_cylinder("P08_Lid", 42, 6, (0, 0, 118), mat_stainless)
    vessel_coll.objects.link(lid)

    # KF16 法兰接口 (6个, 均匀分布)
    for i in range(6):
        angle = i * math.pi / 3
        fx, fy = 42 * math.cos(angle), 42 * math.sin(angle)
        port = make_cylinder(f"P08_KF16_Port{i+1}", 5, 8, (fx, fy, 121), mat_stainless)
        vessel_coll.objects.link(port)

    # UV-C 灯条 P-18: 环形在罐盖内圈
    bpy.ops.mesh.primitive_torus_add(major_radius=35, minor_radius=2, location=(0, 0, 115))
    uv_ring = bpy.context.active_object
    uv_ring.name = "P18_UVC_Ring"
    uv_ring.data.materials.append(make_material("UVC_Light", (0.5, 0.3, 0.8), metallic=0.0, roughness=0.1))
    vessel_coll.objects.link(uv_ring)

    # 搅拌电机 P-11: JGB37-520, ⌀24×40 mm, 在罐盖上方
    motor_body = make_cylinder("P11_Motor_JGB37", 12, 40, (0, 0, 150), mat_motor)
    vessel_coll.objects.link(motor_body)
    # 电机底座
    motor_base = make_cylinder("P11_MotorBase", 16, 6, (0, 0, 128), mat_aluminum)
    vessel_coll.objects.link(motor_base)

    # 磁力密封 + 搅拌轴 P-12: ⌀6×80 mm  
    shaft = make_cylinder("P12_StirShaft", 3, 80, (0, 0, 85), mat_stainless)
    vessel_coll.objects.link(shaft)

    # 四叶桨叶 P-13: ⌀50 mm (4片)
    for pi in range(4):
        angle = pi * math.pi / 2
        bpy.ops.mesh.primitive_cube_add(size=1, location=(25 * math.cos(angle), 25 * math.sin(angle), 45))
        blade = bpy.context.active_object
        blade.name = f"P13_Blade{pi+1}"
        blade.scale = (18, 2, 12)
        blade.data.materials.append(mat_stainless)
        vessel_coll.objects.link(blade)

    # 空气过滤器 P-17: ⌀25×40 mm (2个, 在罐盖上)
    for fi, (fx, fy) in enumerate([(-25, 0), (25, 0)]):
        f_body = make_cylinder(f"P17_Filter{fi+1}", 12, 40, (fx, fy, 140), mat_plastic)
        vessel_coll.objects.link(f_body)

    # ========================================================
    # 03 板卡 Electronics
    # ========================================================
    print("[3/5] 构建电路板...")

    # 主板 P-?? : 100×80×1.6mm, 装在前面板内侧
    main_pcb = make_flat_box("Board1_Main_PCB", (100, 80, 1.6), (0, -160, 330), mat_pcb_green)
    electronics_coll.objects.link(main_pcb)

    # 主板上的芯片标识
    chip_positions = [
        ("ESP32-S3", -30, -15, 330, 22, 16),
        ("ADS1256", 0, -15, 330, 14, 14),
        ("MAX31865", 20, 10, 330, 12, 10),
        ("PT100_TERM", -20, 20, 330, 10, 8),
    ]
    for cname, cx, cy, cz, cw, cd in chip_positions:
        chip = make_bbox(f"IC_{cname}", (cw, cd, 2), (cx, cy, cz), mat_copper)
        electronics_coll.objects.link(chip)

    # 驱动板 P-?? : 100×80×1.6mm, 在底板后部
    driver_pcb = make_flat_box("Board2_Driver_PCB", (100, 80, 1.6), (0, 130, 10), mat_pcb_red)
    electronics_coll.objects.link(driver_pcb)

    # 驱动板元件
    drv_chips = [
        ("SSR-25DA", -25, 0, 10, 20, 20),
        ("Relay_Module", 10, -15, 10, 15, 12),
        ("LM2596_DCDC", 20, 15, 10, 12, 10),
        ("LDO_AMS1117", -10, 20, 10, 10, 8),
    ]
    for dname, dx, dy, dz, dw, dd in drv_chips:
        dchip = make_bbox(f"D_{dname}", (dw, dd, 3), (dx, dy, dz), mat_copper)
        electronics_coll.objects.link(dchip)

    # SSR 散热片
    heatsink = make_bbox("Heatsink_SSR", (30, 30, 10), (-25, 0, 16), mat_aluminum)
    electronics_coll.objects.link(heatsink)

    # 板间排线 P-?? : 20cm 带状
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -10, 200))
    ribbon = bpy.context.active_object
    ribbon.name = "Ribbon_20P"
    ribbon.scale = (15, 0.5, 80)
    ribbon.data.materials.append(mat_accent)
    electronics_coll.objects.link(ribbon)

    # ========================================================
    # 04 前面板 FrontPanel
    # ========================================================
    print("[4/5] 构建前面板组件...")

    # 3.5" TFT 屏幕: ~70×55×5mm
    tft_frame = make_bbox("TFT_Frame", (74, 58, 6), (0, -173, 360), mat_screen)
    front_coll.objects.link(tft_frame)
    tft_active = make_flat_box("TFT_ActiveArea", (66, 50, 0.5), (0, -173, 363), mat_screen_active)
    front_coll.objects.link(tft_active)

    # 急停按钮 P-?? : ⌀30×15 红色蘑菇头, 前面板右上角
    estop_body = make_cylinder("EStop_Body", 15, 10, (120, -173, 370), mat_red_button)
    front_coll.objects.link(estop_body)
    estop_mushroom = make_cylinder("EStop_Mushroom", 18, 4, (120, -172, 375), mat_red_button)
    front_coll.objects.link(estop_mushroom)

    # 3× 操作按钮: ⌀20×8mm
    btn_colors = [mat_button, mat_accent, mat_button]
    for bi, bx in enumerate([-50, 0, 50]):
        btn = make_cylinder(f"Button_{bi+1}", 10, 6, (bx, -172, 390), btn_colors[bi])
        front_coll.objects.link(btn)

    # 3× LED 指示灯: ⌀4mm
    led_labels = [("LED_RUN", mat_led_green, -120), ("LED_ALM", mat_led_amber, -80), ("LED_PWR", mat_led_green, -40)]
    for lname, lmat, lx in led_labels:
        led = make_cylinder(lname, 2, 2, (lx, -172, 400), lmat)
        front_coll.objects.link(led)

    # USB-C 接口
    usb = make_bbox("USBC_Port", (10, 6, 6), (0, 173, 380), mat_screen)
    electronics_coll.objects.link(usb)

    # 220V 进线孔
    power_in = make_cylinder("Power_Inlet", 10, 8, (-50, 173, 320), mat_plastic)
    electronics_coll.objects.link(power_in)

    # ========================================================
    # 05 蠕动泵 + 管路 Pumps
    # ========================================================
    print("[5/5] 构建泵组和管路...")

    # 3× 蠕动泵 P-15: KPP-DC 12V
    pump_positions = [
        ("P101_Pump", -130, -60, 14),
        ("P102_Pump", -130, 0, 14),
        ("P103_Pump", -130, 60, 14),
    ]
    for pname, px, py, pz in pump_positions:
        # 泵体
        p_body = make_bbox(f"{pname}_Body", (50, 40, 30), (px, py, pz + 15), mat_pump)
        pumps_coll.objects.link(p_body)
        # 泵头
        p_head = make_cylinder(f"{pname}_Head", 12, 12, (px + 25, py, pz + 15), mat_plastic)
        pumps_coll.objects.link(p_head)
        # 支架 P-14
        bracket = make_bbox(f"{pname}_Bracket", (10, 40, 50), (px - 25, py, pz + 25), mat_aluminum)
        pumps_coll.objects.link(bracket)

    # 气泵 P-16: KPM24A
    air_pump = make_bbox("P16_AirPump", (40, 30, 25), (-130, 110, 12.5), mat_pump)
    pumps_coll.objects.link(air_pump)

    # 流量计 P-19: LZB-3
    flowmeter = make_cylinder("P19_FlowMeter", 10, 60, (130, 0, 45), make_material("FlowMeter_Glass", (0.5, 0.75, 0.85), alpha=0.6))
    pumps_coll.objects.link(flowmeter)

    # 硅胶管路 P-20: 若干段
    tube_segments = [
        ((-130, -80, 30), (-130, -60, 30)),   # 泵1进口
        ((-80, -30, 30), (-80, 0, 60)),        # 泵 → 罐
        ((-80, 0, 60), (0, 0, 120)),           # 上升管路
        ((-80, 30, 30), (-80, 50, 30)),        # 泵3出口
    ]
    for ti, (start, end) in enumerate(tube_segments):
        mid = ((start[0]+end[0])/2, (start[1]+end[1])/2, (start[2]+end[2])/2)
        length = math.sqrt(sum((s-e)**2 for s, e in zip(start, end)))
        tube = make_cylinder(f"P20_Tube_{ti+1}", 2, length, mid, mat_tubing)
        # 旋转到正确方向
        dx, dy, dz = end[0]-start[0], end[1]-start[1], end[2]-start[2]
        if abs(dx) > 0.1 or abs(dy) > 0.1:
            angle = math.atan2(math.sqrt(dx*dx+dy*dy), dz)
            tube.rotation_euler = (0, angle, math.atan2(dy, dx))
        pumps_coll.objects.link(tube)

    # ========================================================
    # 相机与灯光
    # ========================================================
    print("设置相机和灯光...")

    # 主相机
    bpy.ops.object.camera_add(location=(500, -500, 400))
    camera = bpy.context.active_object
    camera.name = "Camera_Main"
    camera.rotation_euler = (math.radians(55), 0, math.radians(45))
    bpy.context.scene.camera = camera

    # 顶部相机
    bpy.ops.object.camera_add(location=(0, 0, 600))
    cam_top = bpy.context.active_object
    cam_top.name = "Camera_Top"
    cam_top.rotation_euler = (0, 0, 0)

    # 前面板相机
    bpy.ops.object.camera_add(location=(0, -500, 350))
    cam_front = bpy.context.active_object
    cam_front.name = "Camera_Front"
    cam_front.rotation_euler = (math.radians(90), 0, 0)

    # 区域光（主光）
    bpy.ops.object.light_add(type='AREA', location=(300, -300, 500))
    key_light = bpy.context.active_object
    key_light.name = "Key_Light"
    key_light.data.energy = 800
    key_light.data.size = 300

    # 辅助光
    bpy.ops.object.light_add(type='AREA', location=(-200, 200, 300))
    fill_light = bpy.context.active_object
    fill_light.name = "Fill_Light"
    fill_light.data.energy = 400
    fill_light.data.size = 200

    # 环境光
    bpy.ops.object.light_add(type='AREA', location=(0, 0, 600))
    rim_light = bpy.context.active_object
    rim_light.name = "Rim_Light"
    rim_light.data.energy = 300
    rim_light.data.size = 350

    # 底部补光
    bpy.ops.object.light_add(type='AREA', location=(0, 0, -50))
    bottom_light = bpy.context.active_object
    bottom_light.name = "Bottom_Light"
    bottom_light.data.energy = 150
    bottom_light.data.size = 200

    # 渲染设置
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

    # 世界背景
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
    create_all()
