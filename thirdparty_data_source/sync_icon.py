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

def download_icon(type_id, skip_existing=True):
    """下载指定type ID的图标"""
    # 检查文件是否已存在
    save_dir = './icon_from_api'
    save_path = os.path.join(save_dir, f'{type_id}_64.png')
    if os.path.exists(save_path) and skip_existing:
        return 'exists'  # 返回特殊状态表示文件已存在
    
    urls = [
        f'https://images.evetech.net/types/{type_id}/icon',
        f'https://images.evetech.net/types/{type_id}/bp'
    ]
    
    # 需要重试的状态码（服务器临时错误）
    RETRY_STATUS_CODES = {500, 502, 503, 504}
    
    # 设置超时时间：(连接超时, 读取超时)
    TIMEOUT = (5, 10)
    
    # 尝试基本URL
    both_bad_category = True
    for url in urls:
        retry_count = 0
        max_retries = 5
        while retry_count < max_retries:
            try:
                response = requests.get(url, timeout=TIMEOUT)
                if response.status_code == 200:
                    # 检查是否返回"bad category or variation"
                    if b"bad category or variation" in response.content:
                        # 如果是第一个URL，继续尝试第二个URL
                        if url == urls[0]:
                            break
                        # 如果是第二个URL，继续尝试变体
                        break
                    else:
                        both_bad_category = False
                        # 保存成功获取的图标
                        os.makedirs(save_dir, exist_ok=True)
                        with open(save_path, 'wb') as f:
                            f.write(response.content)
                        return True
                elif response.status_code == 404:
                    # 404表示资源不存在，直接尝试下一个URL
                    break
                elif response.status_code in RETRY_STATUS_CODES:
                    # 只有服务器临时错误才重试
                    retry_count += 1
                    if retry_count < max_retries:
                        print(f"\n服务器临时错误（状态码：{response.status_code}），等待1秒后进行第{retry_count + 1}次重试...")
                        time.sleep(1)
                else:
                    # 其他状态码，直接尝试下一个URL
                    break
                    
            except (requests.exceptions.RequestException, IOError) as e:
                # 网络错误时增加重试计数
                retry_count += 1
                if retry_count < max_retries:
                    print(f"\n网络连接错误，等待1秒后进行第{retry_count + 1}次重试...")
                    time.sleep(1)
                else:
                    break
    
    # 如果两个基本URL都返回bad category，尝试获取可用的变体类型
    if both_bad_category:
        try:
            variants_url = f'https://images.evetech.net/types/{type_id}/'
            response = requests.get(variants_url, timeout=TIMEOUT)
            if response.status_code == 200:
                try:
                    variants = response.json()
                    if variants and len(variants) > 0:
                        # 使用第一个变体尝试获取图标
                        variant_url = f'https://images.evetech.net/types/{type_id}/{variants[0]}'
                        variant_response = requests.get(variant_url, timeout=TIMEOUT)
                        if variant_response.status_code == 200 and b"bad category or variation" not in variant_response.content:
                            os.makedirs(save_dir, exist_ok=True)
                            with open(save_path, 'wb') as f:
                                f.write(variant_response.content)
                            return True
                except (ValueError, IndexError):
                    pass
            
            # 如果到这里还没有返回，说明所有尝试都失败了
            with open('/Users/gg/PycharmProjects/EveSDE/thirdparty_data_source/error.txt', 'a') as f:
                f.write(f"{type_id}\n")
            return 'failed'
                
        except (requests.exceptions.RequestException, IOError):
            with open('/Users/gg/PycharmProjects/EveSDE/thirdparty_data_source/error.txt', 'a') as f:
                f.write(f"{type_id}\n")
            return 'failed'
    
    return 'failed'

def main(skip_existing=True):
    # 获取所有type ID
    type_ids = read_types_yaml()
    print(f"总共发现 {len(type_ids)} 个type ID")
    print(f"跳过已存在文件: {'是' if skip_existing else '否'}")
    
    # 创建计数器
    success_count = 0
    fail_count = 0
    skip_count = 0
    retry_fail_count = 0
    
    # 下载所有图标
    for i, type_id in enumerate(type_ids, 1):
        print(f"正在处理 {i}/{len(type_ids)}: Type ID {type_id}", end='')
        
        result = download_icon(type_id, skip_existing)
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
    main(skip_existing=True)  # 在这里直接指定是否跳过已存在文件
