# app/petcare/apps.py

from django.apps import AppConfig


class PetcareConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'petcare'
    verbose_name = 'Pet Care & Message System'

    def ready(self):
        """
        App启动时的初始化操作
        """
        import petcare.signals  # 确保signals被加载

        # 可以在这里添加其他初始化逻辑
        self.setup_logging()

    def setup_logging(self):
        """
        设置宠物消息系统的日志配置
        """
        import logging

        # 确保petcare相关的logger存在
        logger = logging.getLogger('petcare')

        # 如果还没有handler，可以添加一个简单的配置
        if not logger.handlers:
            # 这里可以根据需要配置特定的日志处理器
            pass

