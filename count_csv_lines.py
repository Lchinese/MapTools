def count_csv_lines(filename):
    # 尝试不同的编码方式
    encodings = ['utf-8', 'gbk', 'gb2312', 'latin-1']
    
    for encoding in encodings:
        try:
            with open(filename, 'r', encoding=encoding, errors='ignore') as file:
                line_count = 0
                for line in file:
                    line_count += 1
            print(f"使用 {encoding} 编码读取文件")
            return line_count
        except Exception as e:
            print(f"使用 {encoding} 编码读取失败: {e}")
            continue
    
    # 如果所有编码都失败，则使用二进制方式读取
    with open(filename, 'rb') as file:
        line_count = 0
        for line in file:
            line_count += 1
    print("使用二进制方式读取文件")
    return line_count

if __name__ == "__main__":
    filename = "corrected_trajectories.csv"
    try:
        lines = count_csv_lines(filename)
        print(f"CSV文件 {filename} 总共有 {lines} 行")
    except Exception as e:
        print(f"读取文件时出错: {e}")