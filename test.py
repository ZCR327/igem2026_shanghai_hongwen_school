import cobra

# Step 1: 加载大肠杆菌模型（iGEM 最常用的"出厂"模型）
model = cobra.io.load_model("iJO1366")
print(f"基因: {len(model.genes)}, 反应: {len(model.reactions)}")

# Step 2: 跑 FBA（找最优生长率）
sol = model.optimize()
print(f"最优生长率: {sol.objective_value:.4f}")

# Step 3: 设置新目标（"我要 XOS 产量最大化"）
# 假设 XOS 是 XOS_export 这个反应（你之后要改成真的 XOS 路径）
# model.objective = "XOS_export"
# print(f"XOS 最大产量: {model.optimize().objective_value:.4f}")

# Step 4: 模拟基因敲除（"如果敲掉这个基因会怎样？"）
with model:
    model.genes.b0008.knock_out()  # 敲掉一个真实存在的基因
    ko_sol = model.optimize()
    print(f"敲掉 b0008 后生长率: {ko_sol.objective_value:.4f}")
    print(f"变化: {(ko_sol.objective_value - sol.objective_value) / sol.objective_value * 100:.1f}%")