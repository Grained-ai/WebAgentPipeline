import random
import string

def generate_random_id(length):
    """生成指定长度的随机ID"""
    return ''.join(random.choices(string.ascii_letters + string.digits + '-_', k=length))
