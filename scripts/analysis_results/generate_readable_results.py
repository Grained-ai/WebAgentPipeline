#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成可读的匹配结果CSV文件
"""

import pandas as pd
from pathlib import Path

def main():
    script_dir = Path(__file__).parent
    excel_file = script_dir / "模糊匹配结果.xlsx"
    csv_file = script_dir / "模糊匹配结果.csv"
    
    if not excel_file.exists():
        print(f"错误：文件不存在 {excel_file}")
        return
    
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_file)
        
        # 保存为CSV文件（UTF-8编码，便于查看中文）
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"CSV文件已生成: {csv_file}")
        
        # 显示统计信息
        total = len(df)
        matched = len(df[df['是否找到匹配'] == '是'])
        unmatched = len(df[df['是否找到匹配'] == '否'])
        
        print(f"\n=== 统计信息 ===")
        print(f"总数: {total}")
        print(f"匹配: {matched} ({matched/total*100:.1f}%)")
        print(f"未匹配: {unmatched} ({unmatched/total*100:.1f}%)")
        
        # 显示高相似度匹配（>0.8）
        high_similarity = df[df['相似度'].astype(float) > 0.8]
        print(f"\n高相似度匹配 (>0.8): {len(high_similarity)} 个")
        
        # 显示中等相似度匹配（0.6-0.8）
        medium_similarity = df[(df['相似度'].astype(float) >= 0.6) & (df['相似度'].astype(float) <= 0.8)]
        print(f"中等相似度匹配 (0.6-0.8): {len(medium_similarity)} 个")
        
        # 显示未匹配的前10个item
        unmatched_items = df[df['是否找到匹配'] == '否']['待检查item'].head(10)
        print(f"\n=== 未匹配的前10个item ===")
        for i, item in enumerate(unmatched_items, 1):
            print(f"{i}. {item}")
            
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")

if __name__ == "__main__":
    main()