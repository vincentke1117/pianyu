"""
Logging module for Content Curator
提供统一的日志配置
"""

import logging
import sys
from datetime import datetime


def setup_logger(name="content_curator", level=None, log_file=None):
    """设置并返回日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别（DEBUG/INFO/WARNING/ERROR）
        log_file: 日志文件路径，None则只输出到控制台

    Returns:
        logging.Logger: 配置好的日志记录器
    """

    # 创建日志记录器
    logger = logging.getLogger(name)

    # 如果已经配置过处理器，直接返回
    if logger.handlers:
        return logger

    # 设置日志级别
    if level is None:
        level = logging.INFO
    elif isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    logger.setLevel(level)

    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    # Windows 兼容: 使用 UTF-8 编码
    try:
        console_handler.stream = open(sys.stdout.fileno(), mode='w', encoding='utf-8', buffering=1)
    except:
        pass
    logger.addHandler(console_handler)

    # 文件处理器（如果指定了log_file）
    if log_file:
        # 确保日志目录存在
        import os
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


class LoggerAdapter:
    """日志适配器，提供额外上下文"""

    def __init__(self, logger, extra=None):
        """
        Args:
            logger: logging.Logger实例
            extra: 额外上下文信息（字典）
        """
        self.logger = logger
        self.extra = extra or {}

    def debug(self, msg, *args, **kwargs):
        """记录DEBUG级别日志"""
        self._log(logging.DEBUG, msg, args, kwargs)

    def info(self, msg, *args, **kwargs):
        """记录INFO级别日志"""
        self._log(logging.INFO, msg, args, kwargs)

    def warning(self, msg, *args, **kwargs):
        """记录WARNING级别日志"""
        self._log(logging.WARNING, msg, args, kwargs)

    def error(self, msg, *args, **kwargs):
        """记录ERROR级别日志"""
        self._log(logging.ERROR, msg, args, kwargs)

    def _log(self, level, msg, args, kwargs):
        """内部日志记录方法"""
        # 合并额外上下文
        extra = self.extra.copy()
        if 'extra' in kwargs:
            extra.update(kwargs['extra'])

        self.logger.log(level, msg, *args, extra=extra, **kwargs)


def get_logger_for_channel(channel_name, base_logger=None):
    """为特定频道创建日志适配器

    Args:
        channel_name: 频道名称
        base_logger: 基础日志记录器，None则创建新的

    Returns:
        LoggerAdapter: 频道专用的日志适配器
    """
    if base_logger is None:
        base_logger = setup_logger()

    return LoggerAdapter(
        base_logger,
        extra={'channel': channel_name}
    )


# 预定义的日志消息模板
LOG_MESSAGES = {
    # 配置相关
    'config_loaded': "配置已加载: {file}",
    'config_created': "配置文件已创建: {file}",
    'config_invalid': "配置文件无效: {error}",

    # 视频处理
    'video_found': "发现 {count} 个视频",
    'video_skipped_short': "跳过短视频: {video_id} ({duration}s < {min_duration}s)",
    'video_skipped_processed': "视频已处理，跳过: {video_id}",
    'video_processed': "✓ 成功处理: {title}",
    'video_failed': "✗ 处理失败: {video_id} - {error}",

    # 字幕相关
    'transcript_fetching': "获取字幕: {video_id}",
    'transcript_empty': "字幕为空或太短，跳过: {video_id}",
    'transcript_failed': "获取字幕失败: {video_id} - {error}",

    # API相关
    'api_rate_limit': "API限流，{delay}s后重试 ({attempt}/{max_attempts})",
    'api_error': "API错误: {error}",

    # 文件操作
    'file_saved': "文件已保存: {path}",
    'directory_created': "目录已创建: {path}",

    # 统计
    'processing_summary': """
=== 处理完成 ===
日期: {date}
频道/UP主: {channels}
视频总数: {total}
成功: {success}
失败: {failed}
==============
"""
}


def log_with_template(logger, template_key, **kwargs):
    """使用预定义模板记录日志

    Args:
        logger: 日志记录器
        template_key: 模板键名
        **kwargs: 模板参数
    """
    template = LOG_MESSAGES.get(template_key)
    if template:
        logger.info(template.format(**kwargs))
    else:
        logger.warning(f"未知的日志模板: {template_key}")


# 导出函数
__all__ = [
    'setup_logger',
    'LoggerAdapter',
    'get_logger_for_channel',
    'log_with_template',
    'LOG_MESSAGES'
]
