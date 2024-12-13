from fastapi import FastAPI, Body, Request
from sqlmodel import SQLModel, create_engine, Session, select, Field, or_, not_
from sqlalchemy import func
import oracledb
import traceback
from tool import rand, query_logger
from fastapi.middleware.cors import CORSMiddleware

# FastAPI 应用实例化
app = FastAPI(
    title="车辆信息查询服务",
    description="提供基于身份证号的车辆信息查询后端服务",
    version="1.0.0"
)

# 添加CORS中间件，允许所有来源、所有方法和所有头
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源
    allow_credentials=True,  # 允许凭证，如cookies
    allow_methods=["*"],  # 允许所有HTTP方法
    allow_headers=["*"],  # 允许所有请求头
)
# 数据模型定义
class Vehicle(SQLModel, table=True):
    """
    车辆信息数据模型
    
    属性:
        xh (int): 序号，主键
        hphm (str): 号牌号码
        hpzl (str): 号牌种类
        clsbdh (str): 车辆识别代号
        sfzmhm (str): 身份证明号码
        dybj (str): 抵押标记
        zt (str): 状态
    """
    xh: int = Field(primary_key=True)
    hphm: str
    syr:str
    hpzl: str
    clsbdh: str
    sfzmhm: str
    dybj: int
    zt: str

# 数据库连接配置
oracledb.init_oracle_client()  # 初始化Oracle客户端

DATABASE_URL = "oracle+oracledb://trff_app:trff_app@192.168.1.115:1521/?service_name=orcl"
engine = create_engine(
    DATABASE_URL,
    echo=True,
)

@app.get("/status")
async def status():
    """
    服务状态检查接口
    
    返回:
        dict: 包含服务器状态信息的字典
    """
    return {"message": "服务器已启动"}

@app.get("/test")
async def test(hphm: str):
    """
    根据车牌号查询车辆信息的测试接口
    
    参数:
        hphm (str): 车牌号码
        
    返回:
        dict: 包含查询状态和结果的字典
    """
    try:
        with Session(engine) as session:
            # 执行查询
            statement = select(Vehicle).where(Vehicle.hphm == hphm)
            results = session.exec(statement)
            data = results.all()
            
            # 处理空结果
            if not data:
                return {"status": "success", "data": "null"}
                
            return {"status": "success", "data": data}
    
    except Exception as e:
        return {"status": "error", "data": str(e)}

#@app.get("/bysfzmhm")
async def get_by_sfzmhm(sfzmhm: str):
    """
    根据身份证号查询车辆信息接口
    
    参数:
        sfzmhm (str): 身份证明号码
        
    返回:
        dict: 包含查询状态和结果的字典，结果中排除状态包含'B'和'E'的记录
    """
    try:
        with Session(engine) as session:
            # 构建查询条件：匹配身份证号且状态不包含'B'和'E'
            statement = select(Vehicle).where(
                Vehicle.sfzmhm == sfzmhm,
                func.instr(Vehicle.zt, 'B') == 0,
                func.instr(Vehicle.zt, 'E') == 0
            )
            results = session.exec(statement)
            data = results.all()
            
            # 处理空结果
            if not data:
                return {"status": "success", "data": "null"}
            
            # 格式化返回数据
            formatted_data = [
                {
                    "hpzl": item.hpzl,
                    "hphm": item.hphm,
                    "clsbdh": item.clsbdh,
                    "syr": item.syr,
                    "dybj": item.dybj,
                    "zt": item.zt
                }
                for item in data
            ]
            
            return {"status": "success", "data": formatted_data}
    
    except Exception as e:
        # 返回详细的错误信息
        return {"status": "error", "data": traceback.format_exc()}

@app.post("/validate_code")
async def validate_code(data: dict = Body(...),):
    """
    验证身份证号的合法性
    
    参数:
        code (str): 待验证的身份证号码
        
    返回:
        dict: 包含验证结果的字典
        data: 1 - 身份证号正确
              2 - 身份证号错误
    """
    try:
        # 去除空格
        code = data.get("sfzmhm")
        
        # 基本格式验证
        if len(code) != 18:
            return {"status": "success", "data": 3}
        
        # 验证是否都是数字且最后一位可以是X
        if not (code[:-1].isdigit() and (code[-1].isdigit() or code[-1].upper() == 'X')):
            return {"status": "success", "data": 3}
        
        # 加权因子
        weight = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        # 校验码映射
        check_code_map = '10X98765432'
        
        # 计算加权和
        sum = 0
        for i in range(17):
            sum += int(code[i]) * weight[i]
        
        # 计算校验码
        check = check_code_map[sum % 11]
        
        # 验证校验码
        if check == code[-1].upper():
            return {"status": "success", "data": 1}  # 身份证号正确
        else:
            return {"status": "success", "data": 2}  # 身份证号错误
        
    except Exception as e:
        return {"status": "Error", "data": traceback.format_exc()}  

@app.get("/rd")
async def get_random():
    """
    生成4位随机数
    
    返回:
        dict: 包含生成的4位随机数的字典
    """
    try:
        random_num = rand()
        return {"status": "success", "data": random_num}
    except Exception as e:
        return {"status": "error", "data": traceback.format_exc()}



@app.post("/check")
async def check(
    request: Request,
    data: dict = Body(...)
):
    """
    验证码校验并查询车辆信息接口
    """
    sfzmhm = data.get("sfzmhm")
    input_code = data.get("input_code")
    
    try:

        # 获取当前正确的验证码
        random_result = await get_random()
        if random_result["status"] != "success":
            return {"status": "error", "data": "获取验证码失败"}
            
        correct_code = random_result["data"]
        
        # 验证码校验
        if input_code != correct_code:
            return {"status": "success", "data": "验证码错误"}
                        
        # 查询车辆信息
        query_result = await get_by_sfzmhm(sfzmhm)
        query_logger.log_query(
            ip_address=request.client.host,
            query_param=sfzmhm,
            is_success=query_result["status"] == "success",
            response_data=query_result,
            vehicle_count=len(query_result["data"]) if query_result["data"] != "null" else 0,
            param_type='sfzmhm'
        )
        
        return query_result
        
    except Exception as e:
        error_result = {"status": "error", "data": traceback.format_exc()}
        query_logger.log_query(
            ip_address=request.client.host,
            query_param=sfzmhm,
            is_success=False,
            response_data=error_result,
            param_type='sfzmhm'
        )
        return error_result

# 新增根据车辆识别代号查询车辆信息接口
#@app.get("/byclsbdh")
async def get_by_clsbdh(clsbdh: str):
    """
    根据车辆识别代号查询车辆信息接口
    
    参数:
        clsbdh (str): 车辆识别代号
        
    返回:
        dict: 包含查询状态和结果的字典
    """
    try:
        with Session(engine) as session:
            # 执行查询
            statement = select(Vehicle).where(Vehicle.clsbdh == clsbdh)
            results = session.exec(statement)
            data = results.all()
            
            # 处理空结果
            if not data:
                return {"status": "success", "data": "null"}
            
            # 格式化返回数据
            formatted_data = [
                {
                    "hpzl": item.hpzl,
                    "hphm": item.hphm,
                    "clsbdh": item.clsbdh,
                    "syr": item.syr,
                    "dybj": item.dybj,
                    "zt": item.zt
                }
                for item in data
            ]
            
            return {"status": "success", "data": formatted_data}
    
    except Exception as e:
        # 返回详细的错误信息
        return {"status": "error", "data": traceback.format_exc()}

# 新增验证码校验并查询车辆识别代号接口
@app.post("/checkclsbdh")
async def check_clsbdh(
    data: dict = Body(...),
    request: Request = None  # Added default value for request parameter
):
    """
    验证码校验并查询车辆识别代号接口
    """
    clsbdh = data.get("clsbdh")
    input_code = data.get("input_code")
    
    try:
        # 获取当前正确的验证码
        random_result = await get_random()
        if random_result["status"] != "success":
            return {"status": "error", "data": "获取验证码失败"}
            
        correct_code = random_result["data"]
        
        # 验证码校验
        if input_code != correct_code:
            return {"status": "success", "data": "验证码错误"}
                        
        # 查询车辆信息
        query_result = await get_by_clsbdh(clsbdh)
        # 记录查询日志
        ip_address = request.client.host  # 获取请求的IP地址
        is_success = query_result["status"] == "success"
        print(len(query_result["data"]) if query_result["data"] != "null" else 0)
        
        query_logger.log_query(
            ip_address=ip_address,
            query_param=clsbdh,
            is_success=is_success,
            response_data=query_result,
            param_type='clsbdh',
            vehicle_count=len(query_result["data"]) if query_result["data"] != "null" else 0,
        )
        return query_result
        
    except Exception as e:
        return {"status": "error", "data": traceback.format_exc()}



# 直接运行服务器的入口点
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8004,
        reload=True  # 开发模式下启用热重载
    )
