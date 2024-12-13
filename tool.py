import random
from datetime import datetime
import sqlite3
from typing import Optional, List, Dict
import json

class QueryLogger:
    """查询日志管理类"""
    def __init__(self, db_path: str = 'query_logs.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库，创建查询记录表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建查询记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS query_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_time TIMESTAMP,
                ip_address TEXT,
                query_param TEXT,
                is_success INTEGER,
                vehicle_count INTEGER DEFAULT 0,
                param_type TEXT,
                response_data TEXT,
                is_export INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()

    def log_query(self, 
                 ip_address: str, 
                 query_param: str, 
                 is_success: bool, 
                 response_data: dict,
                 param_type: str,
                 vehicle_count: int = 0,
                 is_export: int = 0) -> bool:
        """记录查询日志"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO query_records 
                (query_time, ip_address, query_param, is_success, vehicle_count, param_type, response_data, is_export)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                ip_address,
                query_param,
                1 if is_success else 0,
                vehicle_count,
                param_type,
                json.dumps(response_data, ensure_ascii=False),
                is_export
            ))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"记录日志时发生错误: {str(e)}")
            return False

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

# 创建全局的日志记录器实例
query_logger = QueryLogger()
