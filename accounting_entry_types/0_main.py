import os
import subprocess
import sys
import shutil

def run_script(script_name):
    """运行指定的Python脚本"""
    try:
        print(f"\n开始执行 {script_name}...")
        subprocess.run([sys.executable, script_name], check=True)
        print(f"{script_name} 执行完成")
    except subprocess.CalledProcessError as e:
        print(f"执行 {script_name} 时出错: {e}")
        sys.exit(1)


def delete_files():
    """删除指定的文件和目录"""
    files_to_delete = [
        'output/accountingentrytypes_localized.json',
        'output/combined_localization.json',
        'output/en_multi_lang_mapping.json',
    ]
    print("\n开始重新构建数据资源...")
    # 删除文件
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"已删除文件: {file}")
            except Exception as e:
                print(f"删除文件 {file} 时出错: {e}")

if __name__ == "__main__":
    delete_files()
    run_script("1_localization.py")
    run_script("2_unpickle.py")
    run_script("3_localize_accounting_types.py")
    run_script("4_combain.py")