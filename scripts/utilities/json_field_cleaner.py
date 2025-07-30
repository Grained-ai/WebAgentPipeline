#!/usr/bin/env python3
"""
Generic JSON Field Cleaner for WebAgent Data Pipeline

This tool provides a configurable way to clean JSON files by removing specified fields.
It supports both configuration-driven and programmatic field removal.
"""

import json
import os
import yaml
from typing import Dict, List, Any, Union, Set
from pathlib import Path
import argparse
from dataclasses import dataclass

@dataclass
class CleaningStats:
    """Statistics for cleaning operation"""
    removed_fields: int = 0
    original_size: int = 0
    cleaned_size: int = 0
    
    @property
    def size_reduction(self) -> int:
        return self.original_size - self.cleaned_size
    
    @property
    def reduction_percentage(self) -> float:
        if self.original_size == 0:
            return 0.0
        return (self.size_reduction / self.original_size) * 100

class JSONFieldCleaner:
    """Generic JSON field cleaner with configuration support"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.fields_to_remove: Set[str] = set()
        self.load_config()
    
    def load_config(self):
        """Load cleaning configuration from YAML file"""
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                self.fields_to_remove = set(config.get('remove_fields', []))
    
    def add_fields_to_remove(self, fields: List[str]):
        """Add additional fields to removal list"""
        self.fields_to_remove.update(fields)
    
    def remove_fields_recursively(self, obj: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
        """Recursively remove specified fields from JSON object/array"""
        if isinstance(obj, dict):
            cleaned_dict = {}
            for key, value in obj.items():
                if key not in self.fields_to_remove:
                    cleaned_dict[key] = self.remove_fields_recursively(value)
            return cleaned_dict
        elif isinstance(obj, list):
            return [self.remove_fields_recursively(item) for item in obj]
        else:
            return obj
    
    def count_fields_to_remove(self, obj: Union[Dict, List, Any]) -> int:
        """Count how many field instances will be removed"""
        count = 0
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in self.fields_to_remove:
                    count += 1
                count += self.count_fields_to_remove(value)
        elif isinstance(obj, list):
            for item in obj:
                count += self.count_fields_to_remove(item)
        return count
    
    def clean_file(self, file_path: str, create_backup: bool = True) -> CleaningStats:
        """Clean a JSON file and return statistics"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Load JSON data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Calculate statistics
        stats = CleaningStats()
        stats.removed_fields = self.count_fields_to_remove(data)
        stats.original_size = os.path.getsize(file_path)
        
        # Create backup if requested
        if create_backup:
            backup_path = f"{file_path}.backup"
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Clean the data
        cleaned_data = self.remove_fields_recursively(data)
        
        # Save cleaned data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        stats.cleaned_size = os.path.getsize(file_path)
        return stats

def main():
    """Command line interface for JSON field cleaner"""
    parser = argparse.ArgumentParser(description='Clean JSON files by removing specified fields')
    parser.add_argument('file_path', help='Path to JSON file to clean')
    parser.add_argument('--config', '-c', help='Path to YAML configuration file')
    parser.add_argument('--fields', '-f', nargs='+', help='Additional fields to remove')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backup file')
    
    args = parser.parse_args()
    
    # Initialize cleaner
    cleaner = JSONFieldCleaner(args.config)
    
    # Add additional fields if specified
    if args.fields:
        cleaner.add_fields_to_remove(args.fields)
    
    # Default WebAgent fields if no config provided
    if not args.config and not args.fields:
        default_fields = [
            'drop', 'mask', 'model', 'tabId', 'path', 'favicon', 'hostTitle',
            'movementX', 'movementY', 'orderList', 'attributes', 'buttonText',
            'cancelable', 'imgMarkValue', 'isShowGuideModelMedia',
            'screenshot', 'marked_screenshot', 'annotations', 'recrop_rect',
            'matchRuleSetting', 'actionRuleSetting'
        ]
        cleaner.add_fields_to_remove(default_fields)
    
    try:
        # Clean the file
        stats = cleaner.clean_file(args.file_path, not args.no_backup)
        
        # Print results
        print(f"✅ JSON文件清理完成!")
        print(f"📊 统计信息:")
        print(f"   - 删除的字段实例数: {stats.removed_fields:,}")
        print(f"   - 原始文件大小: {stats.original_size:,} bytes")
        print(f"   - 清理后文件大小: {stats.cleaned_size:,} bytes")
        print(f"   - 减少大小: {stats.size_reduction:,} bytes ({stats.reduction_percentage:.1f}%)")
        
        if not args.no_backup:
            print(f"   - 备份文件: {args.file_path}.backup")
            
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())