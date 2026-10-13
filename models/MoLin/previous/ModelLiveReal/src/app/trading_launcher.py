# trading_launcher.py
from process_manager import get_process_pool
from typing import Dict, Any, Tuple

def launch_trading_process(config: Dict[str, Any]) -> Tuple[bool, Any]:
    """
    启动交易进程的极简函数
    
    Args:
        config: 配置字典，必须包含:
            - config_name: 配置名称（必须）
            - username: 用户名（必须）
            - quant_id: 策略ID（必须）
            - account: 账户号（必须）
            
    Returns:
        tuple: (是否成功, 进程ID或错误信息)
        
    Examples:
        >>> config = {
        ...     "config_name": "迅投QMT_001",
        ...     "username": "quruyi0101",
        ...     "quant_id": "QI68397284",
        ...     "account": "1662119706"
        ... }
        >>> success, result = launch_trading_process(config)
        >>> if success:
        ...     print(f"进程ID: {result}")
        ... else:
        ...     print(f"错误: {result}")
    """
    try:
        # 1. 验证必要参数
        required_fields = ["config_name", "username", "quant_id", "account"]
        missing = [f for f in required_fields if f not in config]
        if missing:
            return False, f"缺少必要参数: {missing}"
        
        # 2. 设置默认值
        full_config = {
            "script_path": "xtqmt_trader.py",  # 固定脚本路径
            "assets": "total",
            "server_url": "http://10.10.98.51/test/sys/qi/qi00002/qi04635C/MQDataAPICtest.php",
            "socketio_sender_url": "http://10.10.98.51:3211",
            "socketio_receiver_url": "http://10.10.98.51:3210",
        }
        
        # 3. 合并用户配置
        full_config.update(config)
        
        # 4. 自动设置目录路径（如果未提供）
        account = str(config["account"])
        if "mq_dir" not in full_config:
            full_config["mq_dir"] = f"Z:/{account}"
        if "out_dir" not in full_config:
            full_config["out_dir"] = f"Z:/{account}"
        
        # 5. 获取进程池并创建进程
        pool = get_process_pool()
        process_id = pool.create_process(full_config)
        
        return True, process_id
        
    except Exception as e:
        return False, str(e)


# 可选：为了方便使用，可以添加几个快捷函数
def launch_with_defaults(**kwargs) -> Tuple[bool, Any]:
    """
    使用默认参数快速启动
    
    Examples:
        >>> success, pid = launch_with_defaults(
        ...     config_name="策略1",
        ...     username="user1",
        ...     quant_id="QI123",
        ...     account="10001",
        ...     quant_name="测试策略"
        ... )
    """
    config = kwargs.copy()
    return launch_trading_process(config)


def launch_multiple_processes(configs: list) -> Dict[str, Any]:
    """
    批量启动多个进程
    
    Returns:
        Dict: {"success": [...], "failed": [...]}
    """
    results = {"success": [], "failed": []}
    
    for config in configs:
        success, result = launch_trading_process(config)
        if success:
            results["success"].append({
                "config_name": config.get("config_name"),
                "process_id": result
            })
        else:
            results["failed"].append({
                "config_name": config.get("config_name"),
                "error": result
            })
    
    return results