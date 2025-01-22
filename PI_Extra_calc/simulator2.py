import sqlite3
import json
from datetime import datetime, timezone
from typing import Dict, Tuple, Optional, List, Union
from dataclasses import dataclass
from enum import Enum

class DataProvider:
    def __init__(self, db_path: str = "/Users/gg/PycharmProjects/EveSDE/output/db/item_db_zh.sqlite"):
        """初始化数据提供者
        
        Args:
            db_path: SQLite数据库路径
        """
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # 让查询结果可以通过列名访问
        
    def get_schematic_info(self, schematic_id: int) -> Optional[Dict]:
        """获取图纸信息
        
        Args:
            schematic_id: 图纸ID
            
        Returns:
            包含以下信息的字典:
            - cycle_time: 生产周期（秒）
            - output_typeid: 产出物品ID
            - output_value: 产出数量
            - input_typeid: 投入物品ID
            - input_value: 投入数量
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT schematic_id, output_typeid, cycle_time, output_value, 
                   input_typeid, input_value
            FROM planetSchematics 
            WHERE schematic_id = ?
        """, (schematic_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        return {
            'cycle_time': row['cycle_time'],
            'output_typeid': row['output_typeid'],
            'output_value': row['output_value'],
            'input_typeid': row['input_typeid'],
            'input_value': row['input_value']
        }
    
    def get_type_info(self, type_id: int) -> Optional[Dict]:
        """获取物品类型信息
        
        Args:
            type_id: 物品类型ID
            
        Returns:
            包含以下信息的字典:
            - name: 物品名称
            - volume: 物品体积
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, volume 
            FROM types 
            WHERE type_id = ?
        """, (type_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
            
        return {
            'name': row['name'],
            'volume': row['volume']
        }

    def get_storage_capacity(self, type_id: int) -> Optional[float]:
        """获取存储设施的容量
        
        Args:
            type_id: 建筑物类型ID
            
        Returns:
            存储容量（立方米）
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT capacity 
            FROM types 
            WHERE type_id = ?
        """, (type_id,))
        row = cursor.fetchone()
        
        if not row or 'capacity' not in row.keys():
            return 10000.0  # 默认容量
            
        return float(row['capacity'])

class PinStatus(Enum):
    """设施状态"""
    IDLE = "idle"           # 空闲
    RUNNING = "running"     # 运行中
    BLOCKED = "blocked"     # 阻塞（等待资源或存储空间）

@dataclass
class Schematic:
    """生产图纸"""
    schematic_id: int
    cycle_time: int
    input_type_id: int
    input_value: int
    output_type_id: int
    output_value: int

@dataclass
class PinBase:
    """设施基础信息"""
    pin_id: int
    type_id: int
    contents: Dict[int, int]  # type_id -> amount
    last_cycle_start: Optional[datetime]
    latitude: float
    longitude: float
    status: PinStatus = PinStatus.IDLE

@dataclass
class Extractor:
    """提取器"""
    base: PinBase
    cycle_time: int
    quantity_per_cycle: int
    product_type_id: int
    expiry_time: datetime
    install_time: datetime

@dataclass
class Factory:
    """工厂设施"""
    base: PinBase
    schematic_id: int
    schematic: Optional[Schematic] = None  # 完整的图纸信息

@dataclass
class Storage:
    """存储设施"""
    base: PinBase
    capacity: float

Pin = Union[Extractor, Factory, Storage]

@dataclass
class Route:
    """运输路线"""
    source_pin_id: int
    destination_pin_id: int
    content_type_id: int
    quantity: int

@dataclass
class Colony:
    """殖民地"""
    pins: List[Pin]
    routes: List[Route]
    current_time: datetime

class ColonyLoader:
    """殖民地数据加载器"""
    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider

    def load_from_json(self, json_file: str) -> Colony:
        """从JSON文件加载殖民地数据"""
        with open(json_file, 'r') as f:
            data = json.load(f)

        # 加载所有设施
        pins = []
        for pin_data in data['pins']:
            pin = self._create_pin(pin_data)
            if pin:
                # 如果是工厂，加载完整的图纸信息
                if isinstance(pin, Factory):
                    schematic_info = self.data_provider.get_schematic_info(pin.schematic_id)
                    if schematic_info:
                        pin.schematic = Schematic(
                            schematic_id=pin.schematic_id,
                            cycle_time=schematic_info['cycle_time'],
                            input_type_id=schematic_info['input_typeid'],
                            input_value=schematic_info['input_value'],
                            output_type_id=schematic_info['output_typeid'],
                            output_value=schematic_info['output_value']
                        )
                pins.append(pin)

        # 加载所有路线
        routes = []
        for route_data in data['routes']:
            route = Route(
                source_pin_id=route_data['source_pin_id'],
                destination_pin_id=route_data['destination_pin_id'],
                content_type_id=route_data['content_type_id'],
                quantity=int(route_data['quantity'])
            )
            routes.append(route)

        # 使用最早的last_cycle_start作为当前时间
        current_time = None
        for pin in pins:
            if pin.base.last_cycle_start:
                if current_time is None or pin.base.last_cycle_start < current_time:
                    current_time = pin.base.last_cycle_start

        if not current_time:
            current_time = datetime.now(timezone.utc)

        return Colony(pins=pins, routes=routes, current_time=current_time)

    def _create_pin(self, data: dict) -> Optional[Pin]:
        """根据JSON数据创建Pin对象"""
        pin_id = data['pin_id']
        type_id = data['type_id']
        
        # 解析通用字段
        contents = {}
        for item in data.get('contents', []):
            contents[item['type_id']] = item['amount']
            
        last_cycle_start = None
        if 'last_cycle_start' in data:
            last_cycle_start = datetime.strptime(
                data['last_cycle_start'],
                "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
            
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))

        # 创建基础设施对象
        base = PinBase(
            pin_id=pin_id,
            type_id=type_id,
            contents=contents,
            last_cycle_start=last_cycle_start,
            latitude=latitude,
            longitude=longitude
        )

        # 创建提取器
        if 'extractor_details' in data:
            extractor_data = data['extractor_details']
            expiry_time = datetime.strptime(
                data['expiry_time'],
                "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
            install_time = datetime.strptime(
                data['install_time'],
                "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=timezone.utc)
            
            return Extractor(
                base=base,
                cycle_time=extractor_data['cycle_time'],
                quantity_per_cycle=extractor_data['qty_per_cycle'],
                product_type_id=extractor_data['product_type_id'],
                expiry_time=expiry_time,
                install_time=install_time
            )
            
        # 创建工厂
        elif 'schematic_id' in data:
            return Factory(
                base=base,
                schematic_id=data['schematic_id']
            )
            
        # 创建存储设施
        else:
            capacity = self.data_provider.get_storage_capacity(type_id)
            return Storage(
                base=base,
                capacity=capacity
            )

def test_colony_loading():
    """测试殖民地数据加载"""
    provider = DataProvider()
    loader = ColonyLoader(provider)
    
    # 加载殖民地数据
    colony = loader.load_from_json('/Users/gg/PycharmProjects/EveSDE/PI_Extra_calc/response_1737264298263.json')
    
    # 打印殖民地信息
    print(f"\n当前时间: {colony.current_time}")
    print(f"设施数量: {len(colony.pins)}")
    print(f"路线数量: {len(colony.routes)}")
    
    # 打印每个设施的信息
    for pin in colony.pins:
        print(f"\n设施ID: {pin.base.pin_id}")
        print(f"类型: {type(pin).__name__}")
        print(f"类型ID: {pin.base.type_id}")
        print(f"状态: {pin.base.status.value}")
        
        if pin.base.contents:
            print("库存:")
            for type_id, amount in pin.base.contents.items():
                type_info = provider.get_type_info(type_id)
                name = type_info['name'] if type_info else f"Unknown({type_id})"
                print(f"  - {name}: {amount}")
                
        if isinstance(pin, Factory):
            if pin.schematic:
                print(f"图纸信息:")
                print(f"  - 周期: {pin.schematic.cycle_time}秒")
                print(f"  - 输入: {pin.schematic.input_value} x type_id({pin.schematic.input_type_id})")
                print(f"  - 输出: {pin.schematic.output_value} x type_id({pin.schematic.output_type_id})")
        
        elif isinstance(pin, Extractor):
            print(f"提取器信息:")
            print(f"  - 周期: {pin.cycle_time}秒")
            print(f"  - 产量: {pin.quantity_per_cycle}/周期")
            print(f"  - 产品: type_id({pin.product_type_id})")
            print(f"  - 安装时间: {pin.install_time}")
            print(f"  - 到期时间: {pin.expiry_time}")

        elif isinstance(pin, Storage):
            print(f"存储设施信息:")
            print(f"  - 容量: {pin.capacity}立方米")

if __name__ == "__main__":
    test_colony_loading() 