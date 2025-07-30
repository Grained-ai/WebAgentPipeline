#!/usr/bin/env python3
"""
Script to remove specified fields from booking_2025-07-14.json
"""

import json
import os
from typing import Dict, List, Any, Union

def remove_fields_recursively(obj: Union[Dict, List, Any], fields_to_remove: set) -> Union[Dict, List, Any]:
    """
    Recursively remove specified fields from a JSON object or array.
    
    Args:
        obj: The JSON object/array to process
        fields_to_remove: Set of field names to remove
        
    Returns:
        The cleaned object/array
    """
    if isinstance(obj, dict):
        # Create a new dict without the unwanted fields
        cleaned_dict = {}
        for key, value in obj.items():
            if key not in fields_to_remove:
                cleaned_dict[key] = remove_fields_recursively(value, fields_to_remove)
        return cleaned_dict
    elif isinstance(obj, list):
        # Process each item in the list
        return [remove_fields_recursively(item, fields_to_remove) for item in obj]
    else:
        # Return primitive values as-is
        return obj

def clean_booking_json():
    """
    Clean the booking JSON file by removing specified fields.
    """
    # Define the fields to remove (including both lowercase and camelCase versions)
    fields_to_remove = {
        'drop',
        'mask', 
        'model',
        'tabid', 'tabId',  # Handle both cases
        'path',
        'favicon',
        'hosttitle', 'hostTitle',  # Handle both cases
        'movementx', 'movementX',  # Handle both cases
        'movementy', 'movementY',  # Handle both cases
        'orderlist', 'orderList',  # Handle both cases
        'attributes',
        'buttontext', 'buttonText',  # Handle both cases
        'cancelable',
        'imgMarkValue',
        'isShowGuideModelMedia',
        'screenshot',
        'marked_screenshot',
        'annotations',
        'recrop_rect',
        'matchRuleSetting',
        'actionRuleSetting'
    }
    
    # File path
    json_file_path = '/Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts/adhoc/booking_2025-07-14.json'
    
    print(f"开始处理文件: {json_file_path}")
    
    # Check if file exists
    if not os.path.exists(json_file_path):
        print(f"错误: 文件不存在 {json_file_path}")
        return
    
    try:
        # Load the JSON file
        print("正在加载JSON文件...")
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"JSON文件加载成功，包含 {len(data)} 个顶级元素")
        
        # Count fields before cleaning (for statistics)
        removed_count = 0
        
        def count_removed_fields(obj, fields_set):
            nonlocal removed_count
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in fields_set:
                        removed_count += 1
                    count_removed_fields(value, fields_set)
            elif isinstance(obj, list):
                for item in obj:
                    count_removed_fields(item, fields_set)
        
        print("正在统计要删除的字段数量...")
        count_removed_fields(data, fields_to_remove)
        print(f"将要删除 {removed_count} 个字段实例")
        
        # Clean the data
        print("正在清理JSON数据...")
        cleaned_data = remove_fields_recursively(data, fields_to_remove)
        
        # Create backup of original file
        backup_path = json_file_path + '.backup'
        print(f"正在创建备份文件: {backup_path}")
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Save the cleaned data back to the original file
        print("正在保存清理后的JSON文件...")
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        print("✅ JSON文件清理完成!")
        print(f"📊 统计信息:")
        print(f"   - 删除的字段实例数: {removed_count}")
        print(f"   - 备份文件: {backup_path}")
        print(f"   - 清理后文件: {json_file_path}")
        
        # Calculate file size reduction
        original_size = os.path.getsize(backup_path)
        new_size = os.path.getsize(json_file_path)
        size_reduction = original_size - new_size
        reduction_percent = (size_reduction / original_size) * 100 if original_size > 0 else 0
        
        print(f"   - 原始文件大小: {original_size:,} bytes")
        print(f"   - 清理后文件大小: {new_size:,} bytes")
        print(f"   - 减少大小: {size_reduction:,} bytes ({reduction_percent:.1f}%)")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON解析错误: {e}")
    except Exception as e:
        print(f"❌ 处理过程中出现错误: {e}")

if __name__ == "__main__":
    clean_booking_json()