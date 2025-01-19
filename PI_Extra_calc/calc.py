import math


class ExtractorCalculator:
    def __init__(self, quantity_per_cycle):
        self.quantity_per_cycle = quantity_per_cycle
        self.phase_shift = math.pow(quantity_per_cycle, 0.7)
        self.decay_factor = 0.012 # ecuDecayFactor 的 defaultValue
        self.noise_factor = 0.8 # ecuNoiseFactor 的 defaultValue
        self.f1 = 1.0 / 12.0
        self.f2 = 1.0 / 5.0
        self.f3 = 1.0 / 2.0

    def calculate_yield(self, cycle_index):
        """计算指定周期的产量"""
        t = (cycle_index + 0.5) * 16

        # 计算衰减
        decay = self.quantity_per_cycle / (1.0 + t * self.decay_factor)

        # 计算余弦波动
        sina = math.cos(self.phase_shift + t * self.f1)
        sinb = math.cos(self.phase_shift / 2 + t * self.f2)
        sinc = math.cos(t * self.f3)

        # 计算波动值
        sins = max((sina + sinb + sinc) / 3.0, 0.0)

        # 计算每小时产量
        hourly_yield = decay * (1.0 + self.noise_factor * sins)

        # 返回总产量（16小时）
        return round(16 * hourly_yield)

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


def main(quantity_per_cycle):
    # 创建计算器实例
    calculator = ExtractorCalculator(quantity_per_cycle)

    # 计算前100个周期的产量
    results = calculator.calculate_range(0, 83)

    # 打印结果
    print("周期\t产量")
    print("-" * 20)
    for result in results:
        print(f"{result['cycle']}\t{result['yield']}")


if __name__ == "__main__":
    quantity_per_cycle = 5620
    main(quantity_per_cycle)