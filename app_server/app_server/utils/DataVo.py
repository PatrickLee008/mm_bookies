# 使用基础VO
class BaseVO:
    @classmethod
    def from_dict(cls, data: dict):
        """通过字典创建VO对象"""
        vo = cls()
        for key, value in data.items():
            if hasattr(vo, key):
                setattr(vo, key, value)
        return vo

    def to_dict(self) -> dict:
        """将VO对象转为字典"""
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def map_from(self, source, field_mapping: dict = None):
        """
        从源对象映射字段
        :param source: 源对象或字典
        :param field_mapping: 字段映射字典 {源字段: 目标字段}
        """
        if isinstance(source, dict):
            source_dict = source
        else:
            source_dict = source.__dict__

        if field_mapping:
            for src_key, dest_key in field_mapping.items():
                if src_key in source_dict and hasattr(self, dest_key):
                    setattr(self, dest_key, source_dict[src_key])
        else:
            for key, value in source_dict.items():
                if hasattr(self, key):
                    setattr(self, key, value)
        return self


# 租户配置
class SysConfigVO(BaseVO):
    def __init__(self):
        self.member_default_agent_id = None # 会员注册默认代理ID

