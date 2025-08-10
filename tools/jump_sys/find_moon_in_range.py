import json
import heapq
import os
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple


# ------------------------------
# 常量与路径
# ------------------------------
# 按用户规则，数据库相对路径：EVE-Nexus/EVE Nexus/utils/SQLite/item_db_zh.sqlite
REPO_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = REPO_ROOT / "output" / "db" / "item_db_zh.sqlite"

# 跳跃图数据，复用 jump_calc 目录下缓存
JUMP_MAP_PATH = Path(__file__).resolve().parents[1] / "jump_calc" / "jump_map.json"

"""
硬编码参数
"""
START_SYSTEM_NAME = "C-J6MT"  # 起始星系名称
MAX_RANGE = 6.0                # 最大距离(光年)
INCLUDE_START = False          # 是否包含起点自身


# ------------------------------
# 基础工具
# ------------------------------
def ensure_file_exists(path: Path, desc: str) -> None:
    if not path.exists():
        print(f"[x] {desc} 不存在: {path}")
        raise SystemExit(1)


def load_jump_graph() -> Dict[int, List[Tuple[int, float]]]:
    """加载跳跃数据并构建无向图。"""
    ensure_file_exists(JUMP_MAP_PATH, "跳跃数据文件")
    with JUMP_MAP_PATH.open("r", encoding="utf-8") as f:
        jump_data = json.load(f)

    graph: Dict[int, List[Tuple[int, float]]] = {}
    for jump in jump_data:
        s = jump["s_id"]
        d = jump["d_id"]
        ly = jump["ly"]
        graph.setdefault(s, []).append((d, ly))
        graph.setdefault(d, []).append((s, ly))
    return graph


# ------------------------------
# 数据库查询
# ------------------------------
def open_db():
    ensure_file_exists(DB_PATH, "数据库文件")
    return sqlite3.connect(str(DB_PATH))


def get_system_id_by_name(system_name: str) -> Tuple[int, str]:
    """根据星系名称获取其 ID 和名称（名称用于回显）。"""
    conn = open_db()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT solarSystemID, solarSystemName FROM solarsystems WHERE solarSystemName = ?",
            (system_name,),
        )
        row = cursor.fetchone()
        if not row:
            print(f"[x] 未在数据库中找到星系: {system_name}")
            raise SystemExit(1)
        return int(row[0]), str(row[1])
    finally:
        conn.close()


def get_id_to_name(system_ids: List[int]) -> Dict[int, str]:
    conn = open_db()
    try:
        cursor = conn.cursor()
        placeholders = ",".join(["?" for _ in system_ids])
        query = f"SELECT solarSystemID, solarSystemName FROM solarsystems WHERE solarSystemID IN ({placeholders})"
        cursor.execute(query, system_ids)
        return {int(r[0]): str(r[1]) for r in cursor.fetchall()}
    finally:
        conn.close()


def get_system_region_info(system_ids: List[int]) -> Dict[int, Dict[str, object]]:
    """获取星系所属星域信息。"""
    if not system_ids:
        return {}
    conn = open_db()
    try:
        cursor = conn.cursor()
        placeholders = ",".join(["?" for _ in system_ids])
        query = f"""
            SELECT s.solarSystemID, s.solarSystemName, u.region_id, r.regionName
            FROM solarsystems s
            JOIN universe u ON s.solarSystemID = u.solarsystem_id
            JOIN regions r ON u.region_id = r.regionID
            WHERE s.solarSystemID IN ({placeholders})
        """
        cursor.execute(query, system_ids)
        results = cursor.fetchall()
        info: Dict[int, Dict[str, object]] = {}
        for system_id, system_name, region_id, region_name in results:
            info[int(system_id)] = {
                "system_name": str(system_name),
                "region_id": int(region_id),
                "region_name": str(region_name),
            }
        return info
    finally:
        conn.close()


# ------------------------------
# 路径计算
# ------------------------------
def dijkstra_all_distances(graph: Dict[int, List[Tuple[int, float]]], start: int) -> Dict[int, float]:
    heap: List[Tuple[float, int]] = [(0.0, start)]
    dist: Dict[int, float] = {start: 0.0}
    while heap:
        d, node = heapq.heappop(heap)
        if d > dist.get(node, float("inf")):
            continue
        for neighbor, weight in graph.get(node, []):
            new_dist = d + float(weight)
            if new_dist < dist.get(neighbor, float("inf")):
                dist[neighbor] = new_dist
                heapq.heappush(heap, (new_dist, neighbor))
    return dist



def main() -> None:
    # 载图
    graph = load_jump_graph()

    # 起点
    start_id, start_name = get_system_id_by_name(START_SYSTEM_NAME)
    print(f"[!] 起始星系: {start_name} (ID: {start_id})，最大距离: {MAX_RANGE} ly")

    # 计算全图最短路
    distances = dijkstra_all_distances(graph, start_id)

    # 选取范围内星系
    candidates = []
    for system_id, d in distances.items():
        if d <= MAX_RANGE and (INCLUDE_START or system_id != start_id):
            candidates.append((system_id, d))

    # 排序
    candidates.sort(key=lambda x: (x[1], x[0]))
    system_ids = [sid for sid, _ in candidates]

    # 查询名称与星域
    id_to_name = get_id_to_name(system_ids)
    region_info = get_system_region_info(system_ids)

    # 输出
    print(f"[!] 共找到 {len(candidates)} 个星系在 {MAX_RANGE} ly 内")
    for sid, d in candidates:
        name = id_to_name.get(sid, f"Unknown_{sid}")
        region = region_info.get(sid, {})
        region_name = region.get("region_name", "Unknown")
        print(f"  - {name} [{region_name}] : {d:.2f} ly")

    # 最终：仅展示星系名称列表
    if candidates:
        names_only = [id_to_name.get(sid, f"Unknown_{sid}") for sid, _ in candidates]
        print("\n星系名称列表:")
        for n in names_only:
            print(f"{n}")



if __name__ == "__main__":
    main()


