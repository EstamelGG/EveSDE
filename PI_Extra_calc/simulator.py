import json
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from queue import PriorityQueue
from enum import Enum, auto
from dataclasses import dataclass

class SimulationEndCondition(Enum):
    UNTIL_NOW = auto()
    UNTIL_WORK_ENDS = auto()

class PinStatus(Enum):
    STATIC = auto()
    EXTRACTING = auto()
    PRODUCING = auto()
    NOT_SETUP = auto()
    INPUT_NOT_ROUTED = auto()
    OUTPUT_NOT_ROUTED = auto()
    EXTRACTOR_EXPIRED = auto()
    EXTRACTOR_INACTIVE = auto()
    STORAGE_FULL = auto()
    FACTORY_IDLE = auto()

class RoutedState(Enum):
    UNROUTED = auto()
    ROUTED = auto()
    PARTIALLY_ROUTED = auto()

@dataclass
class ColonyStatus:
    is_working: bool
    pins: List['Pin']
    order: Optional[int] = None

    def to_dict(self) -> dict:
        """将ColonyStatus对象转换为可序列化的字典"""
        return {
            'is_working': self.is_working,
            'pins': [pin.to_dict() for pin in self.pins],
            'order': self.order
        }

class Pin:
    def __init__(self, pin_id: int, type_id: int, contents: Dict[int, int]):
        self.pin_id = pin_id
        self.type_id = type_id
        self.contents = contents
        self.last_run_time = None
        self._is_active = False
        self.status = PinStatus.NOT_SETUP
        self.input_routes = []
        self.output_routes = []
        
    def can_activate(self) -> bool:
        return False
        
    @property
    def is_active(self) -> bool:
        return self._is_active
        
    @is_active.setter
    def is_active(self, value: bool):
        self._is_active = value
        
    def can_run(self, end_time: Optional[datetime]) -> bool:
        if not self.is_active and not self.can_activate():
            return False
        next_run_time = self.get_next_run_time()
        if next_run_time is None:
            return False
        if end_time is None:
            return True
        return next_run_time <= end_time
        
    def get_next_run_time(self) -> Optional[datetime]:
        if not self.is_active and not self.can_activate():
            return None
        return self.last_run_time + self.get_cycle_time() if self.last_run_time else None
        
    def get_cycle_time(self) -> timedelta:
        return timedelta(0)
        
    def run(self, current_time: datetime) -> Dict[int, int]:
        self.last_run_time = current_time
        return {}

    def is_routed(self) -> RoutedState:
        """检查设施的路由状态"""
        if not self.input_routes and not self.output_routes:
            return RoutedState.UNROUTED
        
        all_routed = True
        for route in self.input_routes + self.output_routes:
            if route['quantity'] <= 0:
                all_routed = False
                break
        
        return RoutedState.ROUTED if all_routed else RoutedState.PARTIALLY_ROUTED

    def to_dict(self) -> dict:
        """将Pin对象转换为可序列化的字典"""
        return {
            'pin_id': self.pin_id,
            'type_id': self.type_id,
            'contents': self.contents,
            'status': self.status.name,
            'is_active': self.is_active
        }

class Factory(Pin):
    def __init__(self, pin_id: int, type_id: int, contents: Dict[int, int], 
                 schematic_id: Optional[int] = None):
        super().__init__(pin_id, type_id, contents)
        self.schematic_id = schematic_id
        self.schematic = None
        self.last_cycle_start_time = None
        self.has_received_inputs = False
        self.received_inputs_last_cycle = False
        
    def can_activate(self) -> bool:
        if not self.schematic:
            return False
        if self.is_active:
            return True
        if self.has_received_inputs or self.received_inputs_last_cycle:
            return True
        return self.has_enough_inputs()
        
    def has_enough_inputs(self) -> bool:
        if not self.schematic:
            return False
        for input_type, input_amount in self.schematic['input'].items():
            if input_type not in self.contents:
                return False
            if self.contents[input_type] < input_amount:
                return False
        return True
        
    def get_cycle_time(self) -> timedelta:
        return timedelta(seconds=self.schematic['cycle_time']) if self.schematic else timedelta(0)
        
    def run(self, current_time: datetime) -> Dict[int, int]:
        products = {}
        
        if self.is_active:
            products = {
                self.schematic['output']['type_id']: self.schematic['output']['quantity']
            }
            
        if self.has_enough_inputs():
            # 消耗输入材料
            for input_type, input_amount in self.schematic['input'].items():
                self.contents[input_type] -= input_amount
                if self.contents[input_type] == 0:
                    del self.contents[input_type]
                    
            self.is_active = True
            self.last_cycle_start_time = current_time
        else:
            self.is_active = False
            
        self.received_inputs_last_cycle = self.has_received_inputs
        self.has_received_inputs = False
        self.last_run_time = current_time
        
        return products

    def evaluate_status(self) -> PinStatus:
        """评估工厂状态"""
        if not self.schematic:
            return PinStatus.NOT_SETUP
            
        if not self.is_active and not self.can_activate():
            if self.is_routed() != RoutedState.ROUTED:
                return PinStatus.INPUT_NOT_ROUTED
            return PinStatus.FACTORY_IDLE
            
        return PinStatus.PRODUCING

    def to_dict(self) -> dict:
        """将Factory对象转换为可序列化的字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'schematic_id': self.schematic_id,
            'last_cycle_start_time': self.last_cycle_start_time.isoformat() if self.last_cycle_start_time else None,
            'has_received_inputs': self.has_received_inputs,
            'received_inputs_last_cycle': self.received_inputs_last_cycle
        })
        return base_dict

class Storage(Pin):
    def __init__(self, pin_id: int, type_id: int, contents: Dict[int, int], 
                 capacity: int, type_volumes: Dict[int, float]):
        super().__init__(pin_id, type_id, contents)
        self.capacity = capacity
        self.type_volumes = type_volumes
        self.used_capacity = 0
        self.update_capacity()
        
    def update_capacity(self):
        """更新已使用的容量"""
        self.used_capacity = sum(
            amount * self.type_volumes.get(type_id, 0) 
            for type_id, amount in self.contents.items()
        )
    
    def get_capacity_remaining(self) -> float:
        """获取剩余容量"""
        return max(0.0, float(self.capacity) - self.used_capacity)
    
    def can_accept(self, type_id: int, amount: int) -> int:
        """检查是否可以接受指定数量的物品"""
        volume = self.type_volumes.get(type_id, 0)
        new_volume = volume * amount
        capacity_remaining = self.get_capacity_remaining()
        
        if new_volume > capacity_remaining or amount == -1:
            return int(capacity_remaining / volume)
        return amount

    def add_commodity(self, type_id: int, quantity: int) -> int:
        """添加物品，返回实际添加数量"""
        quantity_to_add = self.can_accept(type_id, quantity)
        if quantity_to_add < 1:
            return 0
            
        volume = self.type_volumes.get(type_id, 0)
        self.used_capacity += quantity_to_add * volume
        
        if type_id not in self.contents:
            self.contents[type_id] = quantity_to_add
        else:
            self.contents[type_id] += quantity_to_add
            
        return quantity_to_add
        
    def remove_commodity(self, type_id: int, quantity: int) -> int:
        """移除物品，返回实际移除数量"""
        if type_id not in self.contents:
            return 0
            
        quantity_removed = min(self.contents[type_id], quantity)
        self.contents[type_id] -= quantity_removed
        
        if self.contents[type_id] == 0:
            del self.contents[type_id]
            
        volume = self.type_volumes.get(type_id, 0)
        self.used_capacity = max(0.0, self.used_capacity - volume * quantity_removed)
        
        return quantity_removed

    def evaluate_status(self) -> PinStatus:
        """评估存储设施状态"""
        if self.used_capacity >= self.capacity:
            return PinStatus.STORAGE_FULL
        return PinStatus.STATIC

    def to_dict(self) -> dict:
        """将Storage对象转换为可序列化的字典"""
        base_dict = super().to_dict()
        base_dict.update({
            'capacity': self.capacity,
            'used_capacity': self.used_capacity
        })
        return base_dict

class ColonySimulator:
    def __init__(self, json_file: str, db_path: str):
        self.facilities: Dict[int, Pin] = {}
        self.routes = []
        self.type_volumes = {}
        self.type_names = {}  # 添加类型名称字典
        self.event_queue = PriorityQueue()
        self.current_time = datetime.now(timezone.utc)
        self.sim_end_time = None
        self.db_path = db_path  # 保存数据库路径
        
        self.load_type_info(db_path)  # 加载类型信息
        self.load_colony_data(json_file)
        self.initialize_simulation()
        
    def load_type_info(self, db_path: str):
        """从数据库加载物品类型信息"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT type_id, volume, name FROM types")
        for row in cursor.fetchall():
            self.type_volumes[row[0]] = row[1]
            self.type_names[row[0]] = row[2]
        conn.close()
        
    def get_type_name(self, type_id: int) -> str:
        """获取类型名称"""
        return self.type_names.get(type_id, f"Unknown Type ({type_id})")
        
    def load_schematic(self, db_path: str, schematic_id: int) -> Dict:
        """从数据库加载工厂配方"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT output_typeid, cycle_time, output_value, 
                   input_typeid, input_value
            FROM planetSchematics 
            WHERE schematic_id = ?
        """, (schematic_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            print(f"No schematic found for id {schematic_id}")
            return None
            
        return {
            'schematic_id': schematic_id,
            'output': {
                'type_id': row[0],
                'quantity': row[2]
            },
            'input': {
                row[3]: row[4]
            },
            'cycle_time': row[1]
        }
        
    def load_colony_data(self, json_file: str):
        """加载殖民地数据"""
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        # 加载设施
        for pin in data['pins']:
            contents = {item['type_id']: item['amount'] 
                       for item in pin.get('contents', [])}
            
            if 'schematic_id' in pin:  # 工厂
                facility = Factory(
                    pin['pin_id'],
                    pin['type_id'],
                    contents,
                    pin.get('schematic_id')
                )
                if facility.schematic_id:
                    facility.schematic = self.load_schematic(
                        '../output/db/item_db_zh.sqlite',
                        facility.schematic_id
                    )
                if 'last_cycle_start' in pin:
                    last_cycle_start = datetime.strptime(
                        pin['last_cycle_start'],
                        "%Y-%m-%dT%H:%M:%SZ"
                    ).replace(tzinfo=timezone.utc)
                    facility.last_cycle_start_time = last_cycle_start
                    facility.last_run_time = last_cycle_start  # 设置最后运行时间
                    facility.is_active = True  # 设置为活动状态
            else:  # 存储设施
                capacity = {
                    2544: 10000,  # Launchpad
                    2524: 500,  # Command Center
                }.get(pin['type_id'], 0)
                
                facility = Storage(
                    pin['pin_id'],
                    pin['type_id'],
                    contents,
                    capacity,
                    self.type_volumes
                )
                
            self.facilities[pin['pin_id']] = facility
            
        # 加载路由
        self.routes = data['routes']
        
    def initialize_simulation(self):
        """初始化模拟"""
        # 为每个设施安排首次运行时间
        for facility in self.facilities.values():
            self.schedule_facility(facility)
            
    def schedule_facility(self, facility: Pin):
        """安排设施的下一次运行时间"""
        next_run_time = facility.get_next_run_time()
        if next_run_time:
            # 检查是否已经在队列中
            existing_time = None
            for time, pin_id in self.event_queue.queue:
                if pin_id == facility.pin_id:
                    existing_time = time
                    break
                    
            if existing_time is not None:
                if next_run_time < existing_time:
                    # 移除旧的事件
                    self.event_queue.queue.remove((existing_time, facility.pin_id))
                else:
                    return
                    
            self.event_queue.put((next_run_time, facility.pin_id))
            
    def transfer_commodities(
        self,
        source_id: int,
        dest_id: int,
        type_id: int,
        quantity: int,
        commodities: Dict[int, int],
        max_amount: Optional[int] = None
    ) -> Tuple[Optional[int], int]:
        """转移资源"""
        source = self.facilities[source_id]
        source_contents = source.contents  # 使用源设施的实际内容
        
        if type_id not in source_contents:
            return None, 0
        
        amount_to_move = min(source_contents[type_id], quantity)
        if max_amount is not None:
            amount_to_move = min(max_amount, amount_to_move)
        
        if amount_to_move <= 0:
            return None, 0
        
        dest = self.facilities[dest_id]
        if isinstance(dest, Storage):
            amount_moved = dest.add_commodity(type_id, amount_to_move)
        elif isinstance(dest, Factory):
            if type_id not in dest.contents:
                dest.contents[type_id] = 0
            dest.contents[type_id] += amount_to_move
            amount_moved = amount_to_move
            dest.has_received_inputs = True
        
        if isinstance(source, Storage):
            source.remove_commodity(type_id, amount_moved)
        else:
            # 非存储设施也需要减少内容
            source_contents[type_id] -= amount_moved
            if source_contents[type_id] == 0:
                del source_contents[type_id]
        
        return type_id, amount_moved
        
    def route_products(self, source_pin_id: int, products: Dict[int, int]):
        """处理产品路由"""
        source_facility = self.facilities[source_pin_id]
        
        # 先将产品添加到源设施
        for type_id, amount in products.items():
            if type_id not in source_facility.contents:
                source_facility.contents[type_id] = amount
            else:
                source_facility.contents[type_id] += amount
        
        # 处理所有路由
        for type_id, amount in list(source_facility.contents.items()):
            routes = [r for r in self.routes 
                     if r['source_pin_id'] == source_pin_id 
                     and r['content_type_id'] == type_id]
                     
            if not routes:
                continue
            
            # 计算每个路由的分配量
            total_route_quantity = sum(r['quantity'] for r in routes)
            if total_route_quantity == 0:
                continue
            
            # 按比例分配
            for route in routes:
                route_share = route['quantity'] / total_route_quantity
                route_amount = int(amount * route_share)
                
                if route_amount <= 0:
                    continue
                
                _, transferred = self.transfer_commodities(
                    source_pin_id,
                    route['destination_pin_id'],
                    type_id,
                    route_amount,
                    source_facility.contents
                )

    def simulate(self, until: SimulationEndCondition) -> datetime:
        # 1. 检查是否需要继续工作
        if until == SimulationEndCondition.UNTIL_WORK_ENDS:
            if not self.get_colony_status(self.current_time).is_working:
                return self.current_time
                
        # 2. 初始化模拟
        self.initialize_simulation()
        
        # 3. 处理事件队列
        while not self.event_queue.empty():
            sim_time, pin_id = self.event_queue.get()
            
            # 4. 检查时间边界
            if until == SimulationEndCondition.UNTIL_NOW:
                current_real_time = datetime.now(timezone.utc)
                if sim_time > current_real_time:
                    return self.current_time
            if self.sim_end_time and sim_time > self.sim_end_time:
                return self.current_time
                
            # 5. 更新时间和处理设施
            self.current_time = sim_time
            facility = self.facilities[pin_id]
            
            # 根据模拟条件设置结束时间
            end_time = None
            if until == SimulationEndCondition.UNTIL_NOW:
                end_time = current_real_time
            elif self.sim_end_time:
                end_time = self.sim_end_time
            
            if not facility.can_run(end_time):
                continue
                
            self.evaluate_pin(facility)
            
        return self.current_time
        
    def evaluate_pin(self, pin: Pin):
        """评估并处理设施"""
        if not pin.can_activate() and not pin.is_active:
            return
            
        # 获取产出
        commodities = pin.run(self.current_time)
        
        # 处理输入路由
        if isinstance(pin, Factory):
            self.route_commodity_input(pin)
            
        # 安排下一次运行
        if pin.is_active or pin.can_activate():
            self.schedule_facility(pin)
            
        # 处理产出路由
        if commodities:
            self.route_commodity_output(pin, commodities)
            
        # 更新设施状态
        pin.status = pin.evaluate_status()

    def route_commodity_input(self, destination_pin: Factory):
        """处理输入路由"""
        routes = [r for r in self.routes if r['destination_pin_id'] == destination_pin.pin_id]
        
        for route in routes:
            source_pin = self.facilities[route['source_pin_id']]
            if not isinstance(source_pin, Storage):
                continue
                
            stored_commodities = source_pin.contents
            if not stored_commodities:
                continue
                
            self.transfer_commodities(
                route['source_pin_id'],
                destination_pin.pin_id,
                route['content_type_id'],
                route['quantity'],
                stored_commodities
            )
            
    def route_commodity_output(self, source_pin: Pin, commodities: Dict[int, int]):
        """处理输出路由"""
        for type_id, amount in commodities.items():
            routes = [r for r in self.routes 
                     if r['source_pin_id'] == source_pin.pin_id 
                     and r['content_type_id'] == type_id]
                     
            if not routes:
                continue
                
            total_quantity = sum(r['quantity'] for r in routes)
            for route in routes:
                share = route['quantity'] / total_quantity
                route_amount = int(amount * share)
                
                if route_amount <= 0:
                    continue
                    
                self.transfer_commodities(
                    source_pin.pin_id,
                    route['destination_pin_id'],
                    type_id,
                    route_amount,
                    commodities
                )

    def get_colony_status(self, current_time: datetime) -> ColonyStatus:
        """获取殖民地状态报告"""
        working_pins = []
        for pin in self.facilities.values():
            if pin.is_active or pin.can_activate():
                working_pins.append(pin)
                pin.status = pin.evaluate_status()  # 更新状态
        return ColonyStatus(bool(working_pins), working_pins)

def main():
    simulator = ColonySimulator(
        'response_1737264298263.json',
        '../output/db/item_db_zh.sqlite'
    )
    
    # 设置模拟开始时间为最早的last_cycle_start
    start_time = None
    for facility in simulator.facilities.values():
        if isinstance(facility, Factory) and facility.last_cycle_start_time:
            if start_time is None or facility.last_cycle_start_time < start_time:
                start_time = facility.last_cycle_start_time
    
    if start_time:
        simulator.current_time = start_time
    else:
        print("No valid start time found")
        return
    
    # 运行模拟到当前时间
    simulator.simulate(SimulationEndCondition.UNTIL_NOW)
    current_time = datetime.now(timezone.utc)
    status = simulator.get_colony_status(current_time)
    
    print(f"\n=== 当前时间: {current_time.isoformat()} ===")
    print(f"殖民地是否工作中: {status.is_working}")
    print("\n设施状态:")
    for facility in simulator.facilities.values():
        print(f"\n设施 ID: {facility.pin_id}")
        print(f"类型 ID: {facility.type_id} ({simulator.get_type_name(facility.type_id)})")
        print(f"状态: {facility.status.name}")
        print("内容物:")
        for type_id, amount in facility.contents.items():
            print(f"  - {simulator.get_type_name(type_id)}: {amount}")
        if isinstance(facility, Factory):
            print(f"配方 ID: {facility.schematic_id}")
            print(f"上次循环开始时间: {facility.last_cycle_start_time}")
            print(f"是否活跃: {facility.is_active}")
            if facility.schematic:
                print(f"循环时间: {facility.schematic['cycle_time']}秒")
                print("输入材料:")
                for type_id, amount in facility.schematic['input'].items():
                    print(f"  - {simulator.get_type_name(type_id)}: {amount}")
                print("输出产品:")
                output = facility.schematic['output']
                print(f"  - {simulator.get_type_name(output['type_id'])}: {output['quantity']}")
        elif isinstance(facility, Storage):
            print(f"容量: {facility.capacity}")
            print(f"已使用容量: {facility.used_capacity}")
            print(f"剩余容量: {facility.get_capacity_remaining()}")

if __name__ == "__main__":
    main() 