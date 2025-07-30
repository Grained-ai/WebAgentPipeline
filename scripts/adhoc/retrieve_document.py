import json

def extract_recording_ids(json_file_path):
    """
    从JSON文件中提取所有的recordingId
    """
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    recording_ids = set()  # 使用set来自动去重
    
    # 遍历所有的flow
    for flow in data:
        if 'steps' in flow:
            # 遍历每个flow中的所有steps
            for step in flow['steps']:
                if 'recordingId' in step:
                    recording_ids.add(step['recordingId'])
    
    return sorted(list(recording_ids))  # 转换为排序的列表

# 提取recordingId
json_file_path = '/Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts/adhoc/booking_2025-07-14.json'
recording_ids = extract_recording_ids(json_file_path)

print(f"找到 {len(recording_ids)} 个唯一的recordingId:")
for i, recording_id in enumerate(recording_ids, 1):
    print(f"{i:2d}. {recording_id}")

# 保存结果到文件
output_file = '/Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts/analysis_results/recording_ids.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"从文件提取的recordingId列表\n")
    f.write(f"文件: {json_file_path}\n")
    f.write(f"总计: {len(recording_ids)} 个唯一recordingId\n\n")
    f.write("recordingId列表:\n")
    for i, recording_id in enumerate(recording_ids, 1):
        f.write(f"{i:2d}. {recording_id}\n")

print(f"\n结果已保存到: {output_file}")