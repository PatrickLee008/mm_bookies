"""
环境配置文件
根据 .env 文件中的 APP_ENV 自动加载对应的环境配置
类似 Vue 项目的配置方式
"""
import os
from pathlib import Path

# 获取项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 尝试加载 python-dotenv
try:
    from dotenv import load_dotenv

    # 1. 先加载 .env 文件，获取当前环境
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ 已加载环境控制文件: {env_file}")
    else:
        print(f"⚠ 未找到 .env 文件，使用默认环境: development")

    # 2. 获取当前环境
    current_env = os.getenv('APP_ENV', 'development')

    # 3. 加载对应环境的配置文件
    env_specific_file = BASE_DIR / f'.env.{current_env}'
    if env_specific_file.exists():
        load_dotenv(env_specific_file, override=True)
        print(f"✓ 已加载环境配置文件: {env_specific_file}")
    else:
        print(f"⚠ 未找到环境配置文件: {env_specific_file}")

except ImportError:
    print("⚠ 未安装 python-dotenv 库")
    print("安装方法: pip install python-dotenv")
    current_env = os.getenv('APP_ENV', 'development')


def str_to_bool(value):
    """将字符串转换为布尔值"""
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('true', '1', 'yes', 'on')


def get_env_int(key, default=0):
    """获取整数类型的环境变量"""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_env_bool(key, default=False):
    """获取布尔类型的环境变量"""
    value = os.getenv(key)
    if value is None:
        return default
    return str_to_bool(value)


def get_env_list(key, default=None):
    """获取列表类型的环境变量，支持逗号分隔"""
    value = os.getenv(key)
    if value is None or value.strip() == '':
        return default if default is not None else []
    # 支持逗号分隔的列表
    return [item.strip() for item in value.split(',') if item.strip()]


class Config:
    """统一配置类 - 从环境变量读取配置"""

    # 当前环境
    ENV = current_env

    # 基础配置
    DEBUG = get_env_bool('DEBUG', True)

    # 爬虫账号
    SCRAPER_USERNAME = os.getenv('SCRAPER_USERNAME', '')
    SCRAPER_PASSWORD = os.getenv('SCRAPER_PASSWORD', '')

    # 代理配置
    # 原有代理配置（保留）
    PROXY_HOST = os.getenv('PROXY_HOST', '127.0.0.1')
    PROXY_PORT = os.getenv('PROXY_PORT', '7890')

    # Decodo（原 Smartproxy）代理配置（新增）
    DECODO_PROXY_USERNAME = os.getenv('DECODO_PROXY_USERNAME', '')
    DECODO_PROXY_PASSWORD = os.getenv('DECODO_PROXY_PASSWORD', '')
    DECODO_PROXY_HOST = os.getenv('DECODO_PROXY_HOST', '')
    DECODO_PROXY_PORT = os.getenv('DECODO_PROXY_PORT', '')

    # 选择使用哪个代理: local(原有代理) 或 decodo(Decodo代理)
    USE_PROXY = os.getenv('USE_PROXY', 'local')

    # 根据配置构建代理URL
    if USE_PROXY == 'decodo' and DECODO_PROXY_HOST:
        # 使用 Decodo 代理（带认证）
        PROXY_URL = f"http://{DECODO_PROXY_USERNAME}:{DECODO_PROXY_PASSWORD}@{DECODO_PROXY_HOST}:{DECODO_PROXY_PORT}"
        print(f"✓ 使用 Decodo 代理: {DECODO_PROXY_HOST}:{DECODO_PROXY_PORT}")
    else:
        # 使用原有代理（无认证）
        PROXY_URL = f"http://{PROXY_HOST}:{PROXY_PORT}"
        print(f"✓ 使用本地代理: {PROXY_HOST}:{PROXY_PORT}")

    PROXY = {
        'http': PROXY_URL,
        'https': PROXY_URL
    }

    # HTTP请求头
    HEADERS = {
        'x-forwarded-for': '37.111.7.124',
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.55"
    }

    # 数据库配置
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = get_env_int('DB_PORT', 3306)
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'database')
    DB_CHARSET = os.getenv('DB_CHARSET', 'utf8mb4')

    # 数据库连接池配置
    DB_POOL_SIZE = get_env_int('DB_POOL_SIZE', 10)
    DB_MAX_OVERFLOW = get_env_int('DB_MAX_OVERFLOW', 20)
    DB_POOL_TIMEOUT = get_env_int('DB_POOL_TIMEOUT', 30)
    DB_POOL_RECYCLE = get_env_int('DB_POOL_RECYCLE', 3600)
    DB_POOL_PRE_PING = get_env_bool('DB_POOL_PRE_PING', True)

    # Redis配置
    REDIS_HOST = os.getenv('REDIS_HOST', '127.0.0.1')
    REDIS_PORT = get_env_int('REDIS_PORT', 6379)
    REDIS_DB = get_env_int('REDIS_DB', 0)
    REDIS_DECODE_RESPONSES = get_env_bool('REDIS_DECODE_RESPONSES', True)
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD') or None

    # 缓存配置
    CACHE_EXPIRE_TIME = get_env_int('CACHE_EXPIRE_TIME', 720)  # 默认720秒（12分钟）

    # 测试配置
    TEST_LEAGUE_NAME = get_env_list('TEST_LEAGUE_NAME', [''])  # 测试联赛名称列表
    TEST_CHECK_MATCH_LIST = get_env_list('TEST_CHECK_MATCH_LIST', [''])  # 测试比赛名称列表

    # ibet_runner2配置
    API_URL = os.getenv('API_URL', '')
    API_TOKEN = os.getenv('API_TOKEN', '')
    SYNC_STATUS_FILE = os.getenv('SYNC_STATUS_FILE', 'sync_status.json')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')

    @classmethod
    def get_database_uri(cls):
        """获取数据库连接字符串"""
        return f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}?charset={cls.DB_CHARSET}"

    @classmethod
    def print_config(cls):
        """打印当前配置（隐藏敏感信息）"""
        print("\n" + "="*50)
        print(f"当前环境: {cls.ENV}")
        print("="*50)
        print(f"数据库: {cls.DB_USER}@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}")
        print(f"Redis: {cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}")

        # 显示当前使用的代理
        if cls.USE_PROXY == 'decodo':
            print(f"代理类型: Decodo (原 Smartproxy)")
            print(f"代理地址: {cls.DECODO_PROXY_HOST}:{cls.DECODO_PROXY_PORT}")
            print(f"代理账号: {cls.DECODO_PROXY_USERNAME}")
        else:
            print(f"代理类型: 本地代理")
            print(f"代理地址: {cls.PROXY_HOST}:{cls.PROXY_PORT}")

        print(f"爬虫账号: {cls.SCRAPER_USERNAME}")
        
        # 显示ibet_runner2 API配置
        print(f"API地址: {cls.API_URL}")
        print(f"API Token: {'***' + cls.API_TOKEN[-4:] if cls.API_TOKEN else ''}")
        print(f"同步状态文件: {cls.SYNC_STATUS_FILE}")
        print(f"日志目录: {cls.LOG_DIR}")
        
        print("="*50 + "\n")


# 打印当前配置（可选，用于调试）
if __name__ == '__main__':
    Config.print_config()
