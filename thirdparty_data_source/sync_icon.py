import os
import requests
from ruamel.yaml import YAML

def read_types_yaml():
    """读取types.yaml文件并返回所有type ID，排除特定groupID的类型和不存在的ID"""
    EXCLUDED_GROUP_IDS = {1950, 1951, 1952, 1953, 1954, 1955, 4040}
    
    # 读取not_exist.txt中的ID
    not_exist_ids = set()
    if os.path.exists('not_exist.txt'):
        with open('not_exist.txt', 'r') as f:
            not_exist_ids = {int(line.strip()) for line in f if line.strip().isdigit()}
    
    # 首先检查是否存在缓存的typeids.txt
    if os.path.exists('typeids.txt'):
        print("从缓存文件读取type IDs...")
        with open('typeids.txt', 'r') as f:
            type_ids = [int(line.strip()) for line in f.readlines()]
            # 过滤掉不存在的ID
            return [tid for tid in type_ids if tid not in not_exist_ids]
    
    print("从types.yaml读取type IDs...")
    yaml = YAML(typ='safe')
    with open('../Data/sde/fsd/types.yaml', 'r', encoding='utf-8') as file:
        types_data = yaml.load(file)
    
    # 过滤掉指定groupID的type和404列表中的ID
    type_ids = []
    for type_id, type_info in types_data.items():
        if isinstance(type_info, dict) and 'groupID' in type_info:
            if type_info['groupID'] not in EXCLUDED_GROUP_IDS and type_id not in not_exist_ids:
                type_ids.append(type_id)
    
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
        max_retries = 5  # 增加到5次重试
        while retry_count < max_retries:
            try:
                response = requests.get(url, timeout=TIMEOUT)
                if response.status_code == 200:
                    if b"bad category or variation" in response.content:
                        if url == urls[0]:
                            break
                        break
                    else:
                        both_bad_category = False
                        os.makedirs(save_dir, exist_ok=True)
                        with open(save_path, 'wb') as f:
                            f.write(response.content)
                        return True
                else:
                    # 有响应但不是200，记录到not_exist.txt
                    with open('not_exist.txt', 'a') as f:
                        f.write(f"{type_id}\n")
                    return 'not_exist'
                    
            except (requests.exceptions.RequestException, IOError) as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"\n网络连接错误 {e}，等待1秒后进行第{retry_count + 1}次重试...")
                else:
                    # 5次重试后仍然失败，记录到failed.txt
                    with open('failed.txt', 'a') as f:
                        f.write(f"{type_id}\n")
                    return 'failed'
    
    # 如果两个基本URL都返回bad category，尝试获取变体
    if both_bad_category:
        try:
            variants_url = f'https://images.evetech.net/types/{type_id}/'
            response = requests.get(variants_url, timeout=TIMEOUT)
            if response.status_code == 200:
                try:
                    variants = response.json()
                    if variants and len(variants) > 0:
                        variant_url = f'https://images.evetech.net/types/{type_id}/{variants[0]}'
                        variant_response = requests.get(variant_url, timeout=TIMEOUT)
                        if variant_response.status_code == 200 and b"bad category or variation" not in variant_response.content:
                            os.makedirs(save_dir, exist_ok=True)
                            with open(save_path, 'wb') as f:
                                f.write(variant_response.content)
                            return True
                        else:
                            # 变体请求响应不是200
                            with open('not_exist.txt', 'a') as f:
                                f.write(f"{type_id}\n")
                            return 'not_exist'
                except (ValueError, IndexError):
                    with open('not_exist.txt', 'a') as f:
                        f.write(f"{type_id}\n")
                    return 'not_exist'
                
        except (requests.exceptions.RequestException, IOError):
            # 网络错误，记录到failed.txt
            with open('failed.txt', 'a') as f:
                f.write(f"{type_id}\n")
            return 'failed'
    
    # 所有尝试都失败
    with open('not_exist.txt', 'a') as f:
        f.write(f"{type_id}\n")
    return 'not_exist'

def main(skip_existing=True):
    # 获取所有type ID
    type_ids = read_types_yaml()
    print(f"总共发现 {len(type_ids)} 个type ID")
    print(f"跳过已存在文件: {'是' if skip_existing else '否'}")
    
    # 创建计数器
    success_count = 0
    not_exist_count = 0
    failed_count = 0
    skip_count = 0
    
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
        elif result == 'not_exist':
            not_exist_count += 1
            print(" - 资源不存在")
        elif result == 'failed':
            failed_count += 1
            print(" - 网络错误")
    
    print(f"\n下载完成！")
    print(f"成功: {success_count}")
    print(f"资源不存在: {not_exist_count}")
    print(f"网络错误: {failed_count}")
    print(f"已存在跳过: {skip_count}")

if __name__ == '__main__':
    main(skip_existing=False)  # 在这里直接指定是否跳过已存在文件
