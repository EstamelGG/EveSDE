import os
import subprocess
import sys
import shutil
import datetime

def delete_files():
    """删除指定的文件和目录"""
    files_to_delete = [
        '../icon_md5_map.txt',
        'typeids.txt',
        'not_exist.txt',
        'bp_id.txt',
        'failed.txt'
    ]
    choice = input("是否确实要重新构建图片资源？(y/n)(y:完全重新下载图片资源, n:复用现有图片资源): ").lower().strip()
    if choice != 'y':
        return
    print("\n开始重新构建图片资源...")
    # 删除文件
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"已删除文件: {file}")
            except Exception as e:
                print(f"删除文件 {file} 时出错: {e}")
    
    # 删除icon_from_api目录
    icon_dir = 'icon_from_api'
    if os.path.exists(icon_dir):
        try:
            shutil.rmtree(icon_dir)
            print(f"已删除目录: {icon_dir}")
        except Exception as e:
            print(f"删除目录 {icon_dir} 时出错: {e}")

def update_typeids():
    """删除typeids.txt以强制更新typeid列表"""
    typeids_file = 'typeids.txt'
    if os.path.exists(typeids_file):
        try:
            os.remove(typeids_file)
            print(f"已删除文件: {typeids_file}，将获取最新的typeid列表")
        except Exception as e:
            print(f"删除文件 {typeids_file} 时出错: {e}")

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
    print("欢迎使用图标同步工具")
    choice = input("请选择操作模式：\n(y: 完全重新下载图片资源\nu: 复用现有图片资源但拉取最新的全部typeid以获取增量图片\nn: 完全复用现有图片资源)\n请输入选择(y/u/n): ").lower().strip()
    
    if choice == 'y':
        delete_files()
    elif choice == 'u':
        update_typeids()
        print("\n将复用现有图片资源，但拉取最新的全部typeid以获取增量图片...")
    else:
        print("\n跳过重新构建，直接执行同步...")

    run_script('sync_icon.py')
    run_script('replace_icon.py')
    
    # 记录当前时间戳到文件
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("./last_fetch.txt", "w") as f:
        f.write(timestamp)
    print(f"\n已记录完成时间: {timestamp}")
    
    print("\n所有操作已完成！")

if __name__ == "__main__":
    main() 