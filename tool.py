import random
from datetime import datetime

def rand() -> str:
    """
    生成一个基于当前日期的4位随机数
    每天生成的随机数相同，不同天生成不同的随机数
    
    返回:
        str: 固定4位长度的随机数字字符串
    """
    # 获取当前日期
    today = datetime.now()
    # 用年月日构造种子
    seed = int(f"{today.year}{today.month:02d}{today.day:02d}")
    # 设置随机种子
    random.seed(seed)
    # 生成0-9999之间的随机数
    num = random.randint(0, 9999)
    # 转为4位字符串，不足补0
    return f"{num:04d}"
