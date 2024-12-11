import os
import requests
from ruamel.yaml import YAML
import time

def read_types_yaml():
    """读取types.yaml文件并返回所有type ID"""
    # 首先检查是否存在缓存的typeids.txt
    if os.path.exists('typeids.txt'):
        print("从缓存文件读取type IDs...")
        with open('typeids.txt', 'r') as f:
            return [int(line.strip()) for line in f.readlines()]
    
    print("从types.yaml读取type IDs...")
    yaml = YAML(typ='safe')
    with open('../Data/sde/fsd/types.yaml', 'r', encoding='utf-8') as file:
        types_data = yaml.load(file)
    
    # 获取并保存type IDs到文件
    type_ids = list(types_data.keys())
    print("保存type IDs到缓存文件...")
    with open('typeids.txt', 'w') as f:
        for type_id in type_ids:
            f.write(f"{type_id}\n")
    
    return type_ids

def download_icon(type_id):
    """下载指定type ID的图标"""
    # 检查文件是否已存在
    save_dir = './icon_from_api'
    save_path = os.path.join(save_dir, f'{type_id}_64.png')
    if os.path.exists(save_path):
        return 'exists'  # 返回特殊状态表示文件已存在
    
    url = f'https://images.evetech.net/types/{type_id}/icon'
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            response = requests.get(url)
            # 如果请求成功（无论状态码是什么）
            if response.status_code == 200:
                os.makedirs(save_dir, exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                return False  # 状态码不是200，但不需要重试
                
        except (requests.exceptions.RequestException, IOError) as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"\n请求失败，等待1秒后进行第{retry_count + 1}次重试...")
                time.sleep(1)
            else:
                # 记录失败的type ID
                with open('geticon_fail.txt', 'a') as f:
                    f.write(f"{type_id}\n")
                return 'failed'  # 返回特殊状态表示重试失败
    
    return 'failed'

def main():
    # 获取所有type ID
    type_ids = read_types_yaml()
    print(f"总共发现 {len(type_ids)} 个type ID")
    
    # 创建计数器
    success_count = 0
    fail_count = 0
    skip_count = 0
    retry_fail_count = 0
    
    # 下载所有图标
    for i, type_id in enumerate(type_ids, 1):
        print(f"正在处理 {i}/{len(type_ids)}: Type ID {type_id}", end='')
        
        result = download_icon(type_id)
        if result == 'exists':
            skip_count += 1
            print(" - 已存在，跳过")
        elif result is True:
            success_count += 1
            print(" - 成功")
            time.sleep(0.1)
        elif result == 'failed':
            retry_fail_count += 1
            print(" - 重试5次后失败")
        else:
            fail_count += 1
            print(" - 未找到图标")

    
    print(f"\n下载完成！")
    print(f"成功: {success_count}")
    print(f"失败（非200）: {fail_count}")
    print(f"重试失败: {retry_fail_count}")
    print(f"已存在跳过: {skip_count}")

if __name__ == '__main__':
    main()
