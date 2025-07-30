import pandas as pd
import re
from urllib.parse import urlparse
import os

def extract_websites_from_excel(file_path):
    """
    从Excel文件中提取所有唯一的网站名称
    通过json_name字段按下划线分割的第一个部分来提取网站
    """
    try:
        # 读取Excel文件的所有工作表
        excel_file = pd.ExcelFile(file_path)
        print(f"发现工作表: {excel_file.sheet_names}")
        
        all_websites = set()
        
        # 遍历所有工作表
        for sheet_name in excel_file.sheet_names:
            print(f"\n正在处理工作表: {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            
            print(f"工作表 '{sheet_name}' 的列名: {list(df.columns)}")
            print(f"数据行数: {len(df)}")
            
            # 检查是否存在json_name列
            if 'json_name' in df.columns:
                print("\n使用json_name字段提取网站名称...")
                for value in df['json_name'].dropna():
                    if isinstance(value, str) and '_' in value:
                        # 按下划线分割，取第一个部分作为网站名称
                        website = value.split('_')[0].strip()
                        if website:
                            all_websites.add(website)
            else:
                print("\n未找到json_name列，使用通用方法提取网站信息...")
                # 查找包含URL或网站信息的列
                for column in df.columns:
                    if df[column].dtype == 'object':  # 只处理文本列
                        for value in df[column].dropna():
                            if isinstance(value, str):
                                # 提取URL中的域名
                                urls = extract_urls_from_text(value)
                                for url in urls:
                                    domain = extract_domain(url)
                                    if domain:
                                        all_websites.add(domain)
                                
                                # 查找可能的网站名称模式
                                websites = extract_website_names(value)
                                all_websites.update(websites)
        
        return sorted(list(all_websites))
        
    except Exception as e:
        print(f"读取Excel文件时出错: {e}")
        return []

def extract_urls_from_text(text):
    """
    从文本中提取URL
    """
    url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
    urls = re.findall(url_pattern, text, re.IGNORECASE)
    return urls

def extract_domain(url):
    """
    从URL中提取域名
    """
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # 移除www前缀
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain if domain else None
    except:
        return None

def extract_website_names(text):
    """
    从文本中提取可能的网站名称
    """
    websites = set()
    
    # 常见的网站名称模式
    patterns = [
        r'\b([a-zA-Z0-9-]+\.(?:com|cn|org|net|edu|gov|io|co|uk|de|fr|jp|kr))\b',
        r'\b(amazon|google|facebook|twitter|instagram|linkedin|youtube|tiktok|weibo|baidu|taobao|tmall|jd|pinduoduo)\b',
        r'\b([a-zA-Z0-9-]+(?:网|站|平台|商城|购物|电商))\b'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                websites.update([m for m in match if m])
            else:
                websites.add(match)
    
    return websites

def main():
    file_path = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts/data_files/QC_WebAgent_交付表_20250714_交付表.xlsx"
    
    if not os.path.exists(file_path):
        print(f"文件不存在: {file_path}")
        return
    
    print(f"正在分析文件: {file_path}")
    print("="*50)
    
    websites = extract_websites_from_excel(file_path)
    
    print("\n" + "="*50)
    print(f"发现的唯一网站数量: {len(websites)}")
    print("\n网站列表:")
    print("-"*30)
    
    for i, website in enumerate(websites, 1):
        print(f"{i:3d}. {website}")
    
    # 保存结果到文件
    output_file = "/Users/anthonyf/projects/grainedAI/WebAgentPipeline/scripts/analysis_results/extracted_websites.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"从文件提取的网站列表\n")
        f.write(f"文件: {file_path}\n")
        f.write(f"提取时间: {pd.Timestamp.now()}\n")
        f.write(f"总计: {len(websites)} 个唯一网站\n")
        f.write("\n网站列表:\n")
        for i, website in enumerate(websites, 1):
            f.write(f"{i:3d}. {website}\n")
    
    print(f"\n结果已保存到: {output_file}")

if __name__ == "__main__":
    main()