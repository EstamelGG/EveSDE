import json
import heapq
import sqlite3
import requests
import pandas as pd
from datetime import datetime

# 读取 jump_map.json
with open("jump_map.json", "r") as f:
    jump_data = json.load(f)

# 构建无向图（邻接表）
graph = {}
for jump in jump_data:
    s, d, ly = jump["s_id"], jump["d_id"], jump["ly"]
    graph.setdefault(s, []).append((d, ly))
    graph.setdefault(d, []).append((s, ly))  # 无向图，双向连接

# 星系名称列表和最大距离
system_list = ["C-J6MT", "VBPT-T"]
max_distance = 6
bypass = ["Q-3HS5","3AE-CP","0-VG7A","EUU-4N","4CJ-AC","A24L-V","67Y-NR","GDHN-K","GK5Z-T","QTME-D","RQN-OO","Q7-FZ8","YPW-M4","L5-UWT","74-VZA","I3CR-F","M4-GJ6","2-Q4YG","AGCP-I","2JT-3Q","5-2PQU","7-JT09","SN9-3Z","XQP-9C","F39H-1","W-6GBI","XKH-6O","V-QXXK","38NZ-1","74L2-U","D-P1EH","HL-VZX","HZ-O18","N-O53U","W-MF6J","5M2-KP","KD-KPR","X0-6LH","LVL-GZ","TTP-2B","N7-BIY","F3-8X2","FN0-QS","F2A-GX","MJ-LGH","VBPT-T","ZO-4AR","KS-1TS","RD-FWY","MSG-BZ","4M-QXK","78-0R6","8-WYQZ","88A-RA","8G-2FP","C-J6MT","0-6VZ5","5C-RPA","7EX-14","CR2-PQ","GB-6X5","J-ZYSZ","N7-KGJ","VD-8QY","FX4L-2","X1-IZ0","27-HP0","RZ-TI6","O-9G5Y","WF4C-8","8EF-58","TZN-2V","7L3-JS","O-7LAI","C8H5-X","4DS-OI","3U-48K","G-EURJ","RERZ-L","X5-0EM","0UBC-R","SHBF-V","1TG7-W","A-TJ0G","R959-U","U-UTU9","0TYR-T","MLQ-O9","R0-DMM","3Q-VZA","A-4JOO","5E-CMA","5Q65-4","30-YOU","384-IN","4F89-U","E-JCUS","G063-U","J7-BDX","LP1M-Q","MKIG-5","W-QN5X","YHEN-G","07-SLO","DUO-51","GPD5-0","GRHS-B","J-RXYN","Z-A8FS","6-L4YC","GPLB-C","M3-KAQ","U104-3","HPBE-D","R4N-LD","TP7-KE","M-MBRT","L-FM3P","8-OZU1","UM-SCG","C-62I5","H-HHTH","JQU-KY","MWA-5Q","UY5A-D","ZH-GKG","X-ARMF","5DE-QS","F-3FOY","OAIG-0","UZ-QXW","GGE-5Q","4-OS2A","F-EM4Q","MN-Q26","XQS-GZ","5NQI-E","7K-NSE","B-WQDP","JEQG-7","L-Z9KJ","OR-7N5","G9L-LP","GM-50Y","5-MQQ7","6-EQYE","JLO-Z3","LQ-OAI","N3-JBX","S1-XTL","DE-A7P","1-7HVI","3S-6VU","OX-S7P","V-F6DQ","Q4C-S5","Q-NA5H","ZDB-HT","4-CM8I","LBC-AW","OAQY-M","Q-K2T7","XV-MWG","FYD-TO","KZFV-4","X2-ZA5","IAK-JW","WO-GC0","SK42-F","V-4DBR","NB-ALM","DG-8VJ","6OU9-U","9N-0HF","WU-FHQ","7-A6XV","H-93YV","O3-4MN","7-P1JO","A-7XFN","DX-TAR","EDQG-L","J-L9MA","T-0JWP","TYB-69","5J4K-9","GC-LTF","3-LJW3","ZLO3-V"]

# 获取主权地图数据
def get_sovereignty_map():
    try:
        response = requests.get("https://esi.evetech.net/sovereignty/map")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"获取主权地图失败: {e}")
        return []

# 获取联盟信息
def get_alliance_info(alliance_id):
    try:
        response = requests.get(f"https://esi.evetech.net/alliances/{alliance_id}")
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"获取联盟信息失败 (ID: {alliance_id}): {e}")
        return None

# 连接数据库获取星系ID
def get_system_ids(system_names):
    conn = sqlite3.connect('/Users/ggestamel/Documents/GitHub/EveSDE/output/db/item_db_zh.sqlite')
    cursor = conn.cursor()
    
    # 构建查询语句
    placeholders = ','.join(['?' for _ in system_names])
    query = f"SELECT solarSystemID, solarSystemName FROM solarsystems WHERE solarSystemName IN ({placeholders})"
    
    cursor.execute(query, system_names)
    results = cursor.fetchall()
    
    # 创建名称到ID的映射
    name_to_id = {row[1]: row[0] for row in results}
    id_to_name = {row[0]: row[1] for row in results}
    
    conn.close()
    return name_to_id, id_to_name

# 获取所有星系名称到ID的映射
def get_all_system_names():
    conn = sqlite3.connect('/Users/ggestamel/Documents/GitHub/EveSDE/output/db/item_db_zh.sqlite')
    cursor = conn.cursor()
    
    cursor.execute("SELECT solarSystemID, solarSystemName FROM solarsystems")
    results = cursor.fetchall()
    
    id_to_name = {row[0]: row[1] for row in results}
    
    conn.close()
    return id_to_name

# 获取星系所属的星域信息
def get_system_region_info(system_ids):
    conn = sqlite3.connect('/Users/ggestamel/Documents/GitHub/EveSDE/output/db/item_db_zh.sqlite')
    cursor = conn.cursor()
    
    # 构建查询语句获取星系所属的星域ID
    placeholders = ','.join(['?' for _ in system_ids])
    query = f"""
    SELECT s.solarSystemID, s.solarSystemName, u.region_id, r.regionName
    FROM solarsystems s
    JOIN universe u ON s.solarSystemID = u.solarsystem_id
    JOIN regions r ON u.region_id = r.regionID
    WHERE s.solarSystemID IN ({placeholders})
    """
    
    cursor.execute(query, system_ids)
    results = cursor.fetchall()
    
    # 创建星系ID到星域信息的映射
    system_region_info = {}
    for row in results:
        system_id, system_name, region_id, region_name = row
        system_region_info[system_id] = {
            'system_name': system_name,
            'region_id': region_id,
            'region_name': region_name
        }
    
    conn.close()
    return system_region_info

# 第一步：获取目标星系ID
print("=== 第一步：获取目标星系信息 ===")
name_to_id, id_to_name = get_system_ids(system_list)
target_ids = [name_to_id[name] for name in system_list if name in name_to_id]

if not target_ids:
    print("未找到指定的星系ID")
    exit()

print(f"目标星系: {[id_to_name[tid] for tid in target_ids]} (ID: {target_ids})")

# 第二步：Dijkstra 最短路径搜索
print("\n=== 第二步：计算最短路径 ===")
def dijkstra(start):
    heap = [(0, start)]
    dist = {start: 0}
    while heap:
        d, node = heapq.heappop(heap)
        for neighbor, weight in graph.get(node, []):
            new_dist = d + weight
            if neighbor not in dist or new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))
    return dist

# 对每个起点 ID，计算所有节点到它的距离
all_distances = {node: dijkstra(node) for node in target_ids}
print(f"已完成从 {len(target_ids)} 个目标星系的最短路径计算")

# 第三步：搜索满足条件的星系
print("\n=== 第三步：搜索满足距离条件的星系 ===")
candidate_ids = set(graph.keys())

# 对每个候选星系，检查是否距离所有目标星系都小于max_distance
valid_candidates = set()
for candidate_id in candidate_ids:
    # 排除目标星系本身
    if candidate_id in target_ids:
        continue
    
    # 检查是否距离所有目标星系都小于max_distance
    is_valid = True
    for target_id in target_ids:
        if candidate_id not in all_distances[target_id] or all_distances[target_id][candidate_id] >= max_distance:
            is_valid = False
            break
    
    if is_valid:
        valid_candidates.add(candidate_id)

print(f"找到 {len(valid_candidates)} 个满足距离条件的星系")

# 第四步：过滤bypass列表
print("\n=== 第四步：过滤bypass列表 ===")
# 获取bypass星系名称对应的ID
bypass_name_to_id, _ = get_system_ids(bypass)
bypass_ids = set(bypass_name_to_id.values())

# 从候选星系中移除bypass列表中的星系
original_count = len(valid_candidates)
valid_candidates = valid_candidates - bypass_ids
filtered_count = len(valid_candidates)

print(f"bypass列表包含 {len(bypass)} 个星系名称，对应 {len(bypass_ids)} 个星系ID")
print(f"过滤前: {original_count} 个候选星系")
print(f"过滤后: {filtered_count} 个候选星系")
print(f"移除了 {original_count - filtered_count} 个bypass星系")

if filtered_count == 0:
    print("所有候选星系都在bypass列表中，没有可用的星系")
    exit()

# 第五步：获取星系详细信息
print("\n=== 第五步：获取星系详细信息 ===")
all_id_to_name = get_all_system_names()
all_system_ids = list(valid_candidates) + target_ids
system_region_info = get_system_region_info(all_system_ids)

# 显示候选星系基本信息
print("\n候选星系列表:")
for candidate_id in sorted(valid_candidates):
    candidate_name = all_id_to_name.get(candidate_id, f"Unknown_{candidate_id}")
    candidate_region = system_region_info.get(candidate_id, {})
    region_name = candidate_region.get('region_name', 'Unknown')
    
    distances = []
    for target_id in target_ids:
        target_name = id_to_name[target_id]
        distance = all_distances[target_id][candidate_id]
        distances.append(f"{target_name}({distance}ly)")
    
    print(f"  {candidate_name} [{region_name}]: 到 {', '.join(distances)}")

# 第六步：获取主权信息
print("\n=== 第六步：获取主权信息 ===")
print("正在获取主权地图数据...")
sovereignty_data = get_sovereignty_map()

# 创建星系ID到主权信息的映射（只针对候选星系）
system_sovereignty = {}
alliance_ids = set()
faction_ids = set()

# 只处理候选星系的主权信息
for item in sovereignty_data:
    system_id = item.get('system_id')
    alliance_id = item.get('alliance_id')
    faction_id = item.get('faction_id')
    
    # 只处理候选星系的主权信息
    if system_id in valid_candidates:
        system_sovereignty[system_id] = {
            'alliance_id': alliance_id,
            'corporation_id': item.get('corporation_id'),
            'faction_id': faction_id
        }
        if alliance_id:
            alliance_ids.add(alliance_id)
        if faction_id:
            faction_ids.add(faction_id)

print(f"候选星系主权信息获取完成，包含 {len(system_sovereignty)} 个候选星系的主权信息")

# 分析候选星系的主权分布
print("\n=== 第七步：分析主权分布 ===")
candidate_sovereignty = {}
no_sovereignty_count = 0

for candidate_id in valid_candidates:
    sovereignty = system_sovereignty.get(candidate_id, {})
    if sovereignty.get('alliance_id'):
        alliance_id = sovereignty['alliance_id']
        candidate_sovereignty[alliance_id] = candidate_sovereignty.get(alliance_id, 0) + 1
    elif sovereignty.get('faction_id'):
        faction_id = sovereignty['faction_id']
        candidate_sovereignty[f"Faction_{faction_id}"] = candidate_sovereignty.get(f"Faction_{faction_id}", 0) + 1
    else:
        no_sovereignty_count += 1

print("候选星系主权分布:")
if no_sovereignty_count > 0:
    print(f"  无主权: {no_sovereignty_count} 个星系")
for sovereignty_id, count in sorted(candidate_sovereignty.items()):
    print(f"  {sovereignty_id}: {count} 个星系")

# 第八步：获取详细的主权信息
print("\n=== 第八步：获取详细主权信息 ===")
if alliance_ids:
    print("正在获取联盟详细信息...")
    alliance_info = {}
    for alliance_id in alliance_ids:
        info = get_alliance_info(alliance_id)
        if info:
            alliance_info[alliance_id] = info
    
    print("联盟详细信息:")
    for alliance_id, info in alliance_info.items():
        name = info.get('name', 'Unknown')
        ticker = info.get('ticker', 'Unknown')
        print(f"  {alliance_id}: {name} [{ticker}]")

# 最终输出：保存到Excel文件
print("\n=== 最终结果：保存到Excel文件 ===")
if valid_candidates:
    # 准备数据
    target_names = [id_to_name[tid] for tid in target_ids]
    data_rows = []
    
    for candidate_id in sorted(valid_candidates):
        candidate_name = all_id_to_name.get(candidate_id, f"Unknown_{candidate_id}")
        
        # 获取主权信息
        sovereignty = system_sovereignty.get(candidate_id, {})
        sovereignty_name = "无主权"
        if sovereignty.get('alliance_id'):
            alliance_id = sovereignty['alliance_id']
            sovereignty_name = alliance_info.get(alliance_id, {}).get('name', f'Unknown({alliance_id})')
        elif sovereignty.get('faction_id'):
            sovereignty_name = f"势力{sovereignty['faction_id']}"
        
        # 获取到各目标星系的距离
        distances = []
        for target_id in target_ids:
            distance = all_distances[target_id][candidate_id]
            distances.append(distance)
        
        # 构建数据行
        row_data = [candidate_name, sovereignty_name] + distances
        data_rows.append(row_data)
    
    # 创建DataFrame
    columns = ["星系名", "势力名"] + [f"到{name}距离(ly)" for name in target_names]
    df = pd.DataFrame(data_rows, columns=columns)
    
    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"jump_center_results_{timestamp}.xlsx"
    
    # 保存到Excel文件
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='星系信息', index=False)
        
        # 添加汇总信息
        summary_data = [
            ["目标星系", ", ".join(system_list)],
        ]
        
        # 添加每个目标星系的最大距离
        for i, target_name in enumerate(target_names):
            summary_data.append([f"到{target_name}最大距离", f"{max_distance} 光年"])
        
        # 添加主权分布信息
        if candidate_sovereignty:
            summary_data.append(["", ""])
            summary_data.append(["主权分布", ""])
            for sovereignty_id, count in sorted(candidate_sovereignty.items()):
                summary_data.append([sovereignty_id, count])
        
        summary_df = pd.DataFrame(summary_data, columns=["项目", "数值"])
        summary_df.to_excel(writer, sheet_name='汇总信息', index=False)
    
    print(f"结果已保存到: {filename}")
    print(f"包含 {len(valid_candidates)} 个星系的信息")
    print(f"Excel文件包含两个工作表:")
    print(f"  - 星系信息: 详细的星系数据")
    print(f"  - 汇总信息: 查询参数和统计信息")
    
    # 显示表格预览
    print("\n数据预览:")
    print(df.head(10).to_string(index=False))
    
else:
    print("未找到满足条件的星系")