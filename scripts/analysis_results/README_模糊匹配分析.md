# 模糊匹配分析报告

## 概述
本脚本用于检查 `QC_WebAgent_缺漏检查_待确认.xlsx` 中的指令是否存在于 `QC_WebAgent_交付表_20250714_交付表.xlsx` 的 `flow_title` 列中，使用文字距离进行模糊匹配。

## 文件说明

### 输入文件
- **QC_WebAgent_缺漏检查_待确认.xlsx**: 包含279行待检查的指令
  - 主要列: `instruction` (待检查的指令)
- **QC_WebAgent_交付表_20250714_交付表.xlsx**: 包含1006行交付数据
  - 主要列: `flow_title` (用于匹配的标题)

### 生成的文件
- **fuzzy_match_checker.py**: 主要的模糊匹配脚本
- **generate_readable_results.py**: 生成可读CSV结果的辅助脚本
- **模糊匹配结果.xlsx**: Excel格式的匹配结果
- **模糊匹配结果.csv**: CSV格式的匹配结果（便于查看）

## 匹配算法

### 相似度计算
- 使用 `difflib.SequenceMatcher` 计算两个文本的相似度
- 相似度范围: 0.0 - 1.0 (1.0表示完全匹配)
- 匹配阈值: 0.6 (可调整)

### 匹配逻辑
1. 将文本转换为小写并去除首尾空格
2. 计算待检查item与所有flow_title的相似度
3. 选择相似度最高且超过阈值的匹配
4. 记录匹配结果、相似度和索引位置

## 分析结果

### 总体统计
- **总检查数量**: 279个指令
- **成功匹配**: 206个 (73.8%)
- **未找到匹配**: 73个 (26.2%)

### 匹配质量分布
- **高相似度匹配** (>0.8): 148个
- **中等相似度匹配** (0.6-0.8): 58个

### 典型匹配示例

#### 高质量匹配 (相似度 > 0.9)
```
待检查: "Search for hotels in \"Barstow\" and sort the hotel list by price from low to high, then add the demand for air conditioning to the filter."
最佳匹配: "Search for hotels in \"Barstow\" and sort the hotel list by price from low to high, then add the demand for air conditioning in the filter."
相似度: 0.985
```

#### 中等质量匹配 (相似度 0.6-0.8)
```
待检查: "Search for \"Hideo Kojima\" on The New York Times website, set the type to \"Article,\" and quote the publication date of the first result."
最佳匹配: "Search for \"Tesla\" on The New York Times website, set the date range to yesterday, and quote the title of the second result."
相似度: 0.764
```

### 未匹配的指令类型
未匹配的指令主要包括:
1. 特定网站功能操作 (如CNBC订阅、NASA社交媒体)
2. 特定酒店操作 (如Sierra Motor Lodge评论)
3. 特定平台功能 (如Airbnb行程管理)
4. 特定页面内容引用 (如隐私政策)

## 使用方法

### 运行主脚本
```bash
cd /Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts
python fuzzy_match_checker.py
```

### 生成CSV结果
```bash
python generate_readable_results.py
```

## 结果文件格式

### CSV文件列说明
- **序号**: 检查顺序
- **待检查item**: 原始指令文本
- **是否找到匹配**: 是/否
- **最佳匹配**: 匹配到的flow_title文本
- **相似度**: 0.000-1.000的相似度分数
- **匹配索引**: 在交付表中的行索引

## 参数调整

### 相似度阈值
可以在脚本中调整 `threshold` 参数:
- 提高阈值 (如0.7): 更严格匹配，减少误匹配
- 降低阈值 (如0.5): 更宽松匹配，增加匹配数量

### 文本预处理
当前预处理包括:
- 转换为小写
- 去除首尾空格
- 可扩展: 去除标点符号、词干提取等

## 建议

1. **人工审核**: 对相似度在0.6-0.8之间的匹配进行人工确认
2. **阈值优化**: 根据实际需求调整相似度阈值
3. **文本标准化**: 考虑对指令文本进行更深度的标准化处理
4. **增量更新**: 定期运行脚本检查新增的指令

## 技术依赖

- Python 3.x
- pandas: Excel文件读写
- difflib: 文本相似度计算
- pathlib: 文件路径处理

---

*生成时间: 2025年1月*
*脚本版本: 1.0*