#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模糊匹配检查脚本
检查QC_WebAgent_缺漏检查_待确认.xlsx中的item是否存在于QC_WebAgent_交付表_20250714_交付表.xlsx的flow_title中
使用文字距离进行模糊匹配
"""

import pandas as pd
import difflib
from pathlib import Path
import sys

def calculate_similarity(text1, text2):
    """
    计算两个文本的相似度
    使用SequenceMatcher计算相似度比率
    """
    if pd.isna(text1) or pd.isna(text2):
        return 0.0
    
    text1 = str(text1).strip().lower()
    text2 = str(text2).strip().lower()
    
    return difflib.SequenceMatcher(None, text1, text2).ratio()

def find_best_match(target_text, candidate_list, threshold=0.6):
    """
    在候选列表中找到最佳匹配
    返回最佳匹配的文本、相似度和索引
    """
    best_match = None
    best_score = 0.0
    best_index = -1
    
    for i, candidate in enumerate(candidate_list):
        if pd.isna(candidate):
            continue
            
        score = calculate_similarity(target_text, candidate)
        if score > best_score and score >= threshold:
            best_score = score
            best_match = candidate
            best_index = i
    
    return best_match, best_score, best_index

def main():
    # 文件路径
    script_dir = Path(__file__).parent
    check_file = script_dir / "QC_WebAgent_缺漏检查_待确认.xlsx"
    delivery_file = script_dir / "QC_WebAgent_交付表_20250714_交付表.xlsx"
    
    # 检查文件是否存在
    if not check_file.exists():
        print(f"错误：文件不存在 {check_file}")
        sys.exit(1)
    
    if not delivery_file.exists():
        print(f"错误：文件不存在 {delivery_file}")
        sys.exit(1)
    
    try:
        # 读取Excel文件
        print("正在读取Excel文件...")
        check_df = pd.read_excel(check_file)
        delivery_df = pd.read_excel(delivery_file)
        
        print(f"缺漏检查文件包含 {len(check_df)} 行数据")
        print(f"交付表文件包含 {len(delivery_df)} 行数据")
        
        # 显示列名以便用户确认
        print("\n缺漏检查文件的列名：")
        print(list(check_df.columns))
        
        print("\n交付表文件的列名：")
        print(list(delivery_df.columns))
        
        # 检查是否存在flow_title列
        if 'flow_title' not in delivery_df.columns:
            print("\n错误：交付表文件中未找到'flow_title'列")
            print("可用的列名：", list(delivery_df.columns))
            sys.exit(1)
        
        # 获取flow_title列的数据
        flow_titles = delivery_df['flow_title'].dropna().tolist()
        print(f"\n交付表中有 {len(flow_titles)} 个非空的flow_title")
        
        # 假设缺漏检查文件的第一列是要检查的item
        # 用户可以根据实际情况修改列名
        item_column = check_df.columns[0]  # 使用第一列
        print(f"\n将检查缺漏文件中的'{item_column}'列")
        
        items_to_check = check_df[item_column].dropna().tolist()
        print(f"需要检查 {len(items_to_check)} 个item")
        
        # 进行模糊匹配
        results = []
        threshold = 0.6  # 相似度阈值，可以调整
        
        print(f"\n开始模糊匹配（阈值：{threshold}）...")
        
        for i, item in enumerate(items_to_check):
            if pd.isna(item):
                continue
                
            best_match, best_score, best_index = find_best_match(item, flow_titles, threshold)
            
            result = {
                '序号': i + 1,
                '待检查item': item,
                '是否找到匹配': '是' if best_match else '否',
                '最佳匹配': best_match if best_match else '',
                '相似度': f"{best_score:.3f}" if best_match else '0.000',
                '匹配索引': best_index if best_match else -1
            }
            
            results.append(result)
            
            # 显示进度
            if (i + 1) % 10 == 0 or i == len(items_to_check) - 1:
                print(f"已处理 {i + 1}/{len(items_to_check)} 个item")
        
        # 创建结果DataFrame
        results_df = pd.DataFrame(results)
        
        # 统计结果
        matched_count = len(results_df[results_df['是否找到匹配'] == '是'])
        unmatched_count = len(results_df[results_df['是否找到匹配'] == '否'])
        
        print(f"\n=== 匹配结果统计 ===")
        print(f"总共检查: {len(results)} 个item")
        print(f"找到匹配: {matched_count} 个 ({matched_count/len(results)*100:.1f}%)")
        print(f"未找到匹配: {unmatched_count} 个 ({unmatched_count/len(results)*100:.1f}%)")
        
        # 保存结果到Excel文件
        output_file = script_dir / "模糊匹配结果.xlsx"
        results_df.to_excel(output_file, index=False)
        print(f"\n结果已保存到: {output_file}")
        
        # 显示前几个结果作为示例
        print("\n=== 前10个结果示例 ===")
        print(results_df.head(10).to_string(index=False))
        
        # 显示未匹配的item
        unmatched_df = results_df[results_df['是否找到匹配'] == '否']
        if len(unmatched_df) > 0:
            print(f"\n=== 未找到匹配的item ({len(unmatched_df)}个) ===")
            for item in unmatched_df['待检查item'].head(20):  # 只显示前20个
                print(f"- {item}")
            if len(unmatched_df) > 20:
                print(f"... 还有 {len(unmatched_df) - 20} 个未显示")
        
    except Exception as e:
        print(f"处理过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()