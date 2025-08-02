import asyncio
import aiohttp
import os
import re
import json
import yaml
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse

world_map_layout = "https://evemaps.dotlan.net/svg/New_Eden.svg"

class MapGenerator:
    def __init__(self):
        self.maps_dir = Path("maps")
        self.maps_dir.mkdir(exist_ok=True)
        self.regions_data = []
        self.region_links = {}  # 存储星域连接关系
        
    async def download_new_eden_svg(self):
        """下载New Eden SVG地图"""
        print("正在下载New Eden SVG地图...")
        async with aiohttp.ClientSession() as session:
            async with session.get(world_map_layout) as response:
                if response.status == 200:
                    content = await response.text()
                    with open(self.maps_dir / "New_Eden.svg", "w", encoding="utf-8") as f:
                        f.write(content)
                    print("New Eden SVG下载完成")
                    return content
                else:
                    raise Exception(f"下载失败: {response.status}")
    
    def extract_region_links(self, svg_content):
        """从SVG内容中提取星域链接"""
        print("正在提取星域链接...")
        try:
            soup = BeautifulSoup(svg_content, features="xml")
            region_links = {}
            
            # 查找所有href属性包含evemaps.dotlan.net/map/的链接
            links = soup.find_all('a', attrs={'xlink:href': re.compile(r'http://evemaps\.dotlan\.net/map/.*')})
            
            for link in links:
                href = link.get('xlink:href')
                if href:
                    # 提取星域名
                    region_name = href.split('/')[-1]
                    region_links[region_name] = href
                    print(f"找到星域: {region_name}")
            
            print(f"共找到 {len(region_links)} 个星域")
            return region_links
        except Exception as e:
            print(f"解析SVG失败: {e}")
            return {}
    
    async def download_region_svg(self, session, region_name, url):
        """下载单个星域的SVG"""
        try:
            # 修改URL为SVG格式
            svg_url = url.replace('/map/', '/svg/') + '.svg'
            async with session.get(svg_url) as response:
                if response.status == 200:
                    content = await response.text()
                    filename = f"{region_name}.svg"
                    with open(self.maps_dir / filename, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"下载完成: {region_name}")
                    return region_name, content
                else:
                    print(f"下载失败 {region_name}: {response.status}")
                    return region_name, None
        except Exception as e:
            print(f"下载出错 {region_name}: {e}")
            return region_name, None
    
    async def download_all_regions(self, region_links):
        """并发下载所有星域SVG"""
        print("正在并发下载星域SVG...")
        connector = aiohttp.TCPConnector(limit=30)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for region_name, url in region_links.items():
                task = self.download_region_svg(session, region_name, url)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return {name: content for name, content in results if content is not None}
    
    def extract_coordinates_and_relations(self, svg_content):
        """从SVG中提取坐标和连接关系"""
        try:
            soup = BeautifulSoup(svg_content, features="xml")
            
            # 提取系统坐标
            systems = {}
            sysuse_group = soup.find('g', id='sysuse')
            if sysuse_group:
                for system in sysuse_group.find_all('use'):
                    system_id = system.get('id')
                    if system_id and system_id.startswith('sys'):
                        # 提取系统ID（去掉'sys'前缀）
                        actual_system_id = system_id[3:]
                        x = float(system.get('x', 0))
                        y = float(system.get('y', 0))
                        systems[actual_system_id] = {'x': x, 'y': y}
            
            # 提取连接关系
            relations = {}
            jumps_group = soup.find('g', id='jumps')
            if jumps_group:
                for line in jumps_group.find_all('line'):
                    line_id = line.get('id')
                    if line_id and line_id.startswith('j-'):
                        # 解析连接的系统ID
                        parts = line_id.split('-')
                        if len(parts) >= 3:
                            system1 = parts[1]
                            system2 = parts[2]
                            if system1 not in relations:
                                relations[system1] = []
                            if system2 not in relations[system1]:
                                relations[system1].append(system2)
                            
                            if system2 not in relations:
                                relations[system2] = []
                            if system1 not in relations[system2]:
                                relations[system2].append(system1)
            
            return systems, relations
        except Exception as e:
            print(f"解析坐标和关系失败: {e}")
            return {}, {}
    
    def format_region_name(self, region_name):
        """格式化星域名，删除下划线"""
        return region_name.replace('_', '')
    
    def find_region_yaml(self, region_name):
        """查找region.yaml文件"""
        formatted_name = self.format_region_name(region_name)
        
        # 尝试多个可能的路径
        possible_paths = [
            Path(f"../Data/sde/universe/eve/{formatted_name}/region.yaml"),
            Path(f"Data/sde/universe/eve/{formatted_name}/region.yaml"),
            Path(f"../Data/sde/universe/eve/{region_name}/region.yaml"),
            Path(f"Data/sde/universe/eve/{region_name}/region.yaml")
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    

    
    def build_system_to_region_mapping(self):
        """构建系统到区域的映射"""
        print("正在构建系统到区域映射...")
        system_to_region = {}
        region_info = {}
        
        eve_dir = Path("../Data/sde/universe/eve")
        if not eve_dir.exists():
            eve_dir = Path("Data/sde/universe/eve")
        
        for region_dir in eve_dir.iterdir():
            if region_dir.is_dir():
                region_yaml = region_dir / "region.yaml"
                if region_yaml.exists():
                    try:
                        with open(region_yaml, 'r', encoding='utf-8') as f:
                            region_data = yaml.safe_load(f)
                            region_id = region_data.get('regionID')
                            faction_id = region_data.get('factionID', 0)
                            
                            if region_id:
                                region_info[region_id] = {
                                    'name': region_dir.name,
                                    'faction_id': faction_id
                                }
                                
                                # 遍历该区域下的所有系统
                                for system_dir in region_dir.iterdir():
                                    if system_dir.is_dir():
                                        constellation_yaml = system_dir / "constellation.yaml"
                                        if constellation_yaml.exists():
                                            try:
                                                with open(constellation_yaml, 'r', encoding='utf-8') as f:
                                                    constellation_data = yaml.safe_load(f)
                                                    constellation_id = constellation_data.get('constellationID')
                                                    if constellation_id:
                                                        system_to_region[constellation_id] = region_id
                                            except Exception as e:
                                                print(f"读取星座文件失败 {constellation_yaml}: {e}")
                    except Exception as e:
                        print(f"读取区域文件失败 {region_yaml}: {e}")
        
        print(f"构建完成，共找到 {len(region_info)} 个区域，{len(system_to_region)} 个系统映射")
        return system_to_region, region_info
    
    def process_regions_data(self, region_links, region_svgs):
        """处理所有星域数据"""
        print("正在处理星域数据...")
        
        # 构建系统到区域的映射
        system_to_region, region_info = self.build_system_to_region_mapping()
        
        # 存储区域连接关系
        region_connections = {}
        
        for region_name, svg_content in region_svgs.items():
            if not svg_content:
                continue
                
            # 提取坐标和连接关系
            systems, relations = self.extract_coordinates_and_relations(svg_content)
            
            # 查找region.yaml
            yaml_path = self.find_region_yaml(region_name)
            faction_id = 0
            region_id = None
            
            if yaml_path:
                try:
                    with open(yaml_path, 'r', encoding='utf-8') as f:
                        region_data = yaml.safe_load(f)
                        faction_id = region_data.get('factionID', 0)
                        region_id = region_data.get('regionID')
                except Exception as e:
                    print(f"读取 {yaml_path} 失败: {e}")
            
            if not region_id:
                print(f"无法找到区域ID: {region_name}")
                continue
            
            # 计算中心坐标（使用所有系统的平均坐标）
            if systems:
                center_x = sum(sys['x'] for sys in systems.values()) / len(systems)
                center_y = sum(sys['y'] for sys in systems.values()) / len(systems)
                center = {'x': center_x, 'y': center_y}
            else:
                center = {'x': 0, 'y': 0}
            
            # 收集区域间的连接关系
            connected_regions = set()
            for system_id, connected_systems in relations.items():
                # 将系统ID转换为区域ID
                if system_id in system_to_region:
                    current_region = system_to_region[system_id]
                    for connected_system in connected_systems:
                        if connected_system in system_to_region:
                            connected_region = system_to_region[connected_system]
                            if connected_region != current_region:
                                connected_regions.add(connected_region)
            
            region_data = {
                "region_id": region_id,
                "faction_id": faction_id,
                "center": center,
                "relations": list(connected_regions),
                "systems_count": len(systems)
            }
            
            self.regions_data.append(region_data)
            region_connections[region_id] = list(connected_regions)
            print(f"处理完成: {region_name} (ID: {region_id})")
        
        # 验证连接关系的完整性
        self.validate_connections(region_connections)
    
    def validate_connections(self, region_connections):
        """验证连接关系的完整性"""
        print("正在验证连接关系...")
        for region_id, connections in region_connections.items():
            for connected_region in connections:
                if connected_region in region_connections:
                    if region_id not in region_connections[connected_region]:
                        # 添加反向连接
                        region_connections[connected_region].append(region_id)
                        print(f"添加反向连接: {connected_region} -> {region_id}")
        
        # 更新regions_data中的relations
        for region_data in self.regions_data:
            region_id = region_data["region_id"]
            if region_id in region_connections:
                region_data["relations"] = region_connections[region_id]
    
    def save_to_json(self, filename="regions_data.json"):
        """保存数据到JSON文件"""
        output_path = self.maps_dir / filename
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.regions_data, f, ensure_ascii=False, indent=2)
        print(f"数据已保存到: {output_path}")
    
    async def run(self):
        """运行完整的地图生成流程"""
        try:
            # 1. 下载New Eden SVG
            svg_content = await self.download_new_eden_svg()
            
            # 2. 提取星域链接
            region_links = self.extract_region_links(svg_content)
            
            # 3. 并发下载所有星域SVG
            region_svgs = await self.download_all_regions(region_links)
            
            # 4. 处理星域数据
            self.process_regions_data(region_links, region_svgs)
            
            # 5. 保存到JSON
            self.save_to_json()
            
            print("地图生成完成！")
            
        except Exception as e:
            print(f"处理过程中出错: {e}")

async def main():
    generator = MapGenerator()
    await generator.run()

if __name__ == "__main__":
    asyncio.run(main())