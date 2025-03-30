import json
import os
import sqlite3
from typing import Dict, List, Set, Tuple, Optional
from heapq import heappush, heappop
from datetime import datetime

class JumpPathFinder:
    def __init__(self, json_file_path: str, db_path: str):
        """初始化寻路器"""
        self.graph: Dict[int, List[Tuple[int, float]]] = {}  # 邻接表表示的图
        self.system_names: Dict[int, str] = {}  # 星系ID到名称的映射
        self.load_jump_map(json_file_path)
        self.load_system_names(db_path)
    
    def load_system_names(self, db_path: str) -> None:
        """从数据库加载星系名称"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 查询所有星系ID和名称
            cursor.execute("""
                SELECT solarSystemID, solarSystemName 
                FROM solarsystems
            """)
            
            for system_id, system_name in cursor.fetchall():
                self.system_names[system_id] = system_name
            
            print(f"已加载 {len(self.system_names)} 个星系名称")
            conn.close()
            
        except Exception as e:
            print(f"加载星系名称时出错: {e}")
            raise
    
    def find_system_id(self, system_name: str) -> Optional[int]:
        """根据星系名称查找星系ID"""
        try:
            conn = sqlite3.connect('output/db/item_db_en.sqlite')
            cursor = conn.cursor()
            
            # 使用LIKE进行模糊查询
            cursor.execute("""
                SELECT solarSystemID, solarSystemName 
                FROM solarsystems 
                WHERE solarSystemName LIKE ?
            """, (f"%{system_name}%",))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return None
            elif len(results) == 1:
                return results[0][0]
            else:
                print("\n找到多个匹配的星系:")
                for i, (system_id, name) in enumerate(results, 1):
                    print(f"{i}. {name} (ID: {system_id})")
                while True:
                    try:
                        choice = int(input("\n请选择星系编号: "))
                        if 1 <= choice <= len(results):
                            return results[choice-1][0]
                        print("无效的选择，请重试")
                    except ValueError:
                        print("请输入有效的数字")
                
        except Exception as e:
            print(f"查询星系时出错: {e}")
            return None
    
    def load_jump_map(self, json_file_path: str) -> None:
        """加载跳跃地图数据"""
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 构建邻接表
            for pair in data['jump_pairs']:
                source_id = pair['source_id']
                dest_id = pair['dest_id']
                distance = pair['distance_ly']
                
                # 添加双向边（因为可以双向跳跃）
                if source_id not in self.graph:
                    self.graph[source_id] = []
                if dest_id not in self.graph:
                    self.graph[dest_id] = []
                
                self.graph[source_id].append((dest_id, distance))
                self.graph[dest_id].append((source_id, distance))
            
            print(f"已加载 {len(self.graph)} 个星系节点")
            
        except Exception as e:
            print(f"加载JSON文件时出错: {e}")
            raise
    
    def heuristic(self, current_id: int, end_id: int) -> Tuple[int, float]:
        """
        启发式函数：返回(估计剩余跳跃次数, 估计剩余距离)
        这个估计值一定小于等于实际值，满足A*算法的可采纳性
        """
        # 如果当前节点和终点之间有直接连接，返回(1, 实际距离)
        for neighbor_id, distance in self.graph[current_id]:
            if neighbor_id == end_id:
                return (1, distance)
                
        # 否则，找到当前节点到所有邻居节点的最小距离
        min_distance = float('inf')
        for _, distance in self.graph[current_id]:
            min_distance = min(min_distance, distance)
            
        # 如果找到了最小距离，返回(2, 最小距离)作为估计值
        if min_distance != float('inf'):
            return (2, min_distance)
            
        # 如果连最小距离都找不到，返回一个较大的估计值
        return (10, 100.0)

    def find_path_astar(self, start_id: int, end_id: int, max_jump_distance: float) -> Tuple[List[int], float]:
        """
        使用A*算法寻找最短路径，优先考虑跳跃次数最少，其次考虑总距离最短
        
        Args:
            start_id: 起点星系ID
            end_id: 终点星系ID
            max_jump_distance: 最大跳跃距离（光年）
            
        Returns:
            Tuple[List[int], float]: (路径星系ID列表, 总距离)
        """
        if start_id not in self.graph or end_id not in self.graph:
            raise ValueError("起点或终点星系不存在")
        
        # 初始化开放列表和关闭列表
        open_set = [(0, 0, start_id)]  # (估计总跳跃次数, 估计总距离, node_id)
        closed_set = set()
        came_from = {}
        g_score = {start_id: (0, 0)}  # (跳跃次数, 总距离)
        f_score = {start_id: self.heuristic(start_id, end_id)}  # (估计剩余跳跃次数, 估计剩余距离)
        
        while open_set:
            current_f_jumps, current_f_dist, current_id = heappop(open_set)
            
            # 如果到达终点
            if current_id == end_id:
                break
                
            # 将当前节点加入关闭列表
            closed_set.add(current_id)
            
            # 遍历所有相邻节点
            for neighbor_id, jump_distance in self.graph[current_id]:
                # 跳过已访问的节点
                if neighbor_id in closed_set:
                    continue
                    
                # 检查跳跃距离是否在限制内
                if jump_distance > max_jump_distance:
                    continue
                
                # 计算从起点经过当前节点到邻居节点的距离和跳跃次数
                current_jumps, current_dist = g_score[current_id]
                tentative_jumps = current_jumps + 1
                tentative_dist = current_dist + jump_distance
                
                # 如果找到更好的路径（跳跃次数更少，或者在相同跳跃次数下距离更短）
                if (neighbor_id not in g_score or 
                    tentative_jumps < g_score[neighbor_id][0] or 
                    (tentative_jumps == g_score[neighbor_id][0] and tentative_dist < g_score[neighbor_id][1])):
                    
                    came_from[neighbor_id] = current_id
                    g_score[neighbor_id] = (tentative_jumps, tentative_dist)
                    
                    # 计算f_score
                    h_jumps, h_dist = self.heuristic(neighbor_id, end_id)
                    f_jumps = tentative_jumps + h_jumps
                    f_dist = tentative_dist + h_dist
                    
                    heappush(open_set, (f_jumps, f_dist, neighbor_id))
        
        # 如果找不到路径
        if end_id not in came_from:
            raise ValueError("找不到符合条件的路径")
        
        # 重建路径
        path = []
        current = end_id
        while current is not None:
            path.append(current)
            current = came_from.get(current)
        path.reverse()
        
        return path, g_score[end_id][1]  # 返回路径和总距离

def main():
    json_path = "output/jump_map/jump_map.json"
    
    # 创建寻路器实例
    path_finder = JumpPathFinder(json_path, 'output/db/item_db_en.sqlite')
    
    # 测试寻路
    try:
        # 获取起点星系
        while True:
            start_name = input("请输入起点星系名称: ")
            start_id = path_finder.find_system_id(start_name)
            if start_id:
                break
            print("未找到匹配的星系，请重试")
        
        # 获取终点星系
        while True:
            end_name = input("请输入终点星系名称: ")
            end_id = path_finder.find_system_id(end_name)
            if end_id:
                break
            print("未找到匹配的星系，请重试")
        
        # 获取最大跳跃距离
        while True:
            try:
                max_distance = float(input("请输入最大跳跃距离（光年）: "))
                if max_distance > 0:
                    break
                print("请输入大于0的距离")
            except ValueError:
                print("请输入有效的数字")
        
        # 查找路径
        path, total_distance = path_finder.find_path_astar(start_id, end_id, max_distance)
        
        # 显示结果
        print("\n找到路径:")
        print(f"总距离: {total_distance:.2f} 光年")
        print(f"跳跃次数: {len(path) - 1}")
        print("\n路径详情:")
        for i, system_id in enumerate(path):
            system_name = path_finder.system_names.get(system_id, f"未知星系 {system_id}")
            if i < len(path) - 1:
                next_system_id = path[i + 1]
                # 获取当前星系到下一个星系的距离
                for neighbor_id, distance in path_finder.graph[system_id]:
                    if neighbor_id == next_system_id:
                        print(f"{i+1}. {system_name} -> {path_finder.system_names.get(next_system_id, f'未知星系 {next_system_id}')} ({distance:.2f} 光年)")
                        break
            else:
                print(f"{i+1}. {system_name}")
            
    except ValueError as e:
        print(f"错误: {e}")
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    main() 