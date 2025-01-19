import math
from datetime import datetime, timezone


class ExtractorCalculator:
    def __init__(self, quantity_per_cycle, cycle_time):
        self.quantity_per_cycle = quantity_per_cycle
        self.cycle_time = cycle_time
        # 转换周期时间为15分钟单位数
        self.w_count = cycle_time / 900  # 900秒 = 15分钟
        self.phase_shift = math.pow(quantity_per_cycle, 0.7)
        self.decay_factor = 0.012  # ecuDecayFactor 的 defaultValue
        self.noise_factor = 0.8  # ecuNoiseFactor 的 defaultValue
        self.f1 = 1.0 / 12.0
        self.f2 = 1.0 / 5.0
        self.f3 = 1.0 / 2.0

    def calculate_yield(self, cycle_index):
        """计算指定周期的产量"""
        # 使用15分钟为基本单位计算时间
        t = (cycle_index + 0.5) * self.w_count

        # 计算衰减
        decay = self.quantity_per_cycle / (1.0 + t * self.decay_factor)

        # 计算余弦波动
        sina = math.cos(self.phase_shift + t * self.f1)
        sinb = math.cos(self.phase_shift / 2 + t * self.f2)
        sinc = math.cos(t * self.f3)

        # 计算波动值
        sins = max((sina + sinb + sinc) / 3.0, 0.0)

        # 计算产量
        hourly_yield = decay * (1.0 + self.noise_factor * sins)

        # 返回总产量
        return int(self.w_count * hourly_yield)

    def calculate_range(self, start_cycle, end_cycle):
        """计算一个范围内的所有周期产量"""
        results = []
        for cycle in range(start_cycle, end_cycle + 1):
            yield_value = self.calculate_yield(cycle)
            results.append({
                'cycle': cycle + 1,  # 显示从1开始的周期编号
                'yield': yield_value
            })
        return results


def calculate_total_cycles(install_time, expiry_time, cycle_time):
    """计算总周期数"""
    # 将时间字符串转换为datetime对象
    install_dt = datetime.strptime(install_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    expiry_dt = datetime.strptime(expiry_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    # 计算总秒数
    total_seconds = (expiry_dt - install_dt).total_seconds()

    # 计算总周期数
    total_cycles = int(total_seconds / cycle_time)

    return total_cycles - 1  # 减1是因为周期从0开始


def get_current_cycle(install_time, cycle_time):
    """获取当前周期"""
    # 将安装时间转换为datetime对象
    install_dt = datetime.strptime(install_time, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

    # 获取当前UTC时间
    current_dt = datetime.now(timezone.utc)

    # 计算从安装到现在经过的秒数
    elapsed_seconds = (current_dt - install_dt).total_seconds()

    # 计算当前周期
    current_cycle = int(elapsed_seconds / cycle_time)

    return current_cycle


def main(quantity_per_cycle, cycle_time, install_time, expiry_time):
    # 计算总周期数
    total_cycles = calculate_total_cycles(install_time, expiry_time, cycle_time)

    # 获取当前周期
    current_cycle = get_current_cycle(install_time, cycle_time)

    # 创建计算器实例
    calculator = ExtractorCalculator(quantity_per_cycle, cycle_time)

    # 计算所有周期的产量
    results = calculator.calculate_range(0, total_cycles)

    # 打印结果
    print(f"基础产量: {quantity_per_cycle}")
    print(f"周期时间: {cycle_time}秒 ({cycle_time / 3600}小时)")
    print(f"15分钟单位数: {cycle_time / 900}")
    print(f"总周期数: {total_cycles + 1}")  # +1是为了显示实际周期数
    print(f"当前周期: {current_cycle + 1}")  # +1是为了显示从1开始的周期编号
    print("\n周期\t产量")
    print("-" * 20)
    for result in results:
        cycle_marker = " <--" if result['cycle'] == current_cycle + 1 else ""
        print(f"{result['cycle']}\t{result['yield']}{cycle_marker}")


if __name__ == "__main__":
    quantity_per_cycle = 7313  # from esi response: pins.extractor_details.qty_per_cycle
    cycle_time = 3600  # from esi response: pins.extractor_details.cycle_time
    expiry_time = "2025-01-21T19:49:51Z"
    install_time = "2025-01-19T09:49:51Z"
    main(quantity_per_cycle, cycle_time, install_time, expiry_time)