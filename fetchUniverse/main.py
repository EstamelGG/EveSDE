import os
import shutil
import sys
from pathlib import Path
import subprocess
import datetime

def run_script(script_name):
    """运行指定的Python脚本"""
    try:
        print(f"\n开始执行 {script_name}...")
        subprocess.run([sys.executable, script_name], check=True)
        print(f"{script_name} 执行完成")
    except subprocess.CalledProcessError as e:
        print(f"执行 {script_name} 时出错: {e}")
        sys.exit(1)

def main():
    # 获取用户输入
    user_input = input("是否需要重新获取宇宙数据？(y/n): ").strip().lower()
    
    if user_input == 'y':
        # 删除缓存目录
        cache_dir = Path("cache")
        if cache_dir.exists():
            try:
                print("正在删除缓存目录...")
                shutil.rmtree(cache_dir)
                print("已删除缓存目录")
            except Exception as e:
                print(f"删除缓存目录时出错: {e}")
                sys.exit(1)
    
    # 执行 fetchUniverse.py
    print("开始获取宇宙数据...")
    run_script("fetchUniverse.py")
    
    # 记录当前时间戳到文件
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("./last_fetch.txt", "w") as f:
        f.write(timestamp)
    print(f"\n已记录完成时间: {timestamp}")
    
    print("宇宙数据获取完成！")

if __name__ == "__main__":
    main() 