# -*- coding: utf-8 -*-
"""
全局日志管理模块
提供统一的日志记录功能
"""
import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime


class Logger:
    """日志管理类"""

    def __init__(self, name='ox2mm_app_server', log_level=None):
        """
        初始化日志管理器
        :param name: 日志名称
        :param log_level: 日志级别，从环境变量LOG_LEVEL读取，默认INFO
        """
        self.logger = logging.getLogger(name)

        # 从环境变量读取日志级别
        if log_level is None:
            log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

        # 设置日志级别
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        self.logger.setLevel(level_map.get(log_level, logging.INFO))

        # 避免重复添加handler
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """配置日志处理器"""
        # 日志格式
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 从环境变量读取是否启用文件日志
        enable_file_log = os.getenv('LOG_TO_FILE', 'True').lower() == 'true'

        if enable_file_log:
            # 日志目录
            log_dir = os.getenv('LOG_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs'))
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            # 获取日志文件名前缀
            log_file_prefix = os.getenv('LOG_FILE_PREFIX', 'app')

            # 按日期轮转的日志文件
            log_file = os.path.join(log_dir, f'{log_file_prefix}.log')

            # 按日期轮转的文件处理器（每天一个文件，保留30天）
            timed_handler = TimedRotatingFileHandler(
                log_file,
                when='midnight',
                interval=1,
                backupCount=int(os.getenv('LOG_BACKUP_COUNT', 30)),
                encoding='utf-8'
            )
            timed_handler.suffix = '%Y-%m-%d.log'
            timed_handler.setFormatter(formatter)
            self.logger.addHandler(timed_handler)

            # 错误日志单独记录
            error_log_file = os.path.join(log_dir, f'{log_file_prefix}_error.log')
            error_handler = RotatingFileHandler(
                error_log_file,
                maxBytes=int(os.getenv('LOG_MAX_BYTES', 10 * 1024 * 1024)),  # 默认10MB
                backupCount=int(os.getenv('LOG_BACKUP_COUNT', 10)),
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            self.logger.addHandler(error_handler)

    def get_logger(self):
        """获取logger实例"""
        return self.logger

    def debug(self, msg, *args, **kwargs):
        """记录DEBUG级别日志"""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """记录INFO级别日志"""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """记录WARNING级别日志"""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """记录ERROR级别日志"""
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """记录CRITICAL级别日志"""
        self.logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """记录异常信息"""
        self.logger.exception(msg, *args, **kwargs)


# 创建全局logger实例
_global_logger = None


def get_logger(name=None):
    """
    获取全局日志实例
    :param name: 日志名称，如果为None则使用默认名称
    :return: logging.Logger实例（标准库logger，确保显示正确的调用位置）
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger(name or 'ox2mm_app_server')
    # 返回标准的logging.Logger对象，而不是Logger包装类，这样可以正确显示调用位置
    return _global_logger.get_logger()


# 便捷函数
def debug(msg, *args, **kwargs):
    """记录DEBUG级别日志"""
    get_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """记录INFO级别日志"""
    get_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """记录WARNING级别日志"""
    get_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """记录ERROR级别日志"""
    get_logger().error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """记录CRITICAL级别日志"""
    get_logger().critical(msg, *args, **kwargs)


def exception(msg, *args, **kwargs):
    """记录异常信息"""
    get_logger().exception(msg, *args, **kwargs)
