from app_server import db, app
from sqlalchemy import Column, String, Integer, Text
from sqlalchemy.dialects.mysql import TINYINT, DATETIME
from datetime import datetime
from app_server.utils.BaseSaasModel import BaseSaasModel
from app_server.utils.DataVo import SysConfigVO, ScraperCfgVo, PlatformOrderCfgVo, AppFrontSettingVo


# 系统业务字典，读取系统配置
class SysBisDict(BaseSaasModel):
    __tablename__ = 'sys_bis_dict'

    id = Column(String(64), primary_key=True, comment="字典ID")
    dict_dir = Column(String(64), nullable=False, server_default='', comment="字典目录（用于某块业务，方便加载所有字典）")
    dict_type = Column(String(50), nullable=False, server_default='', comment="字典类型（KEY：字典，VAL：值）")
    dict_code = Column(String(50), nullable=False, server_default='', comment="字典编码")
    dict_value = Column(String(100), nullable=False, server_default='', comment="字典值")
    dict_label = Column(String(100), nullable=False, server_default='', comment="字典标签（显示用）")
    status = Column(TINYINT, nullable=False, server_default='1', comment="状态: 0-停用, 1-启用")
    sort = Column(Integer, nullable=False, server_default='0', comment="排序序号")
    parent_code = Column(String(50), nullable=False, server_default='', comment="父级字典编码")
    css_class = Column(String(50), nullable=False, server_default='', comment="前端样式类")
    icon_url = Column(String(255), nullable=False, server_default='', comment="图标地址")

    __mapper_args__ = {
        "order_by": sort.asc(),
    }

    @staticmethod
    def get_dict_by_dir(dict_dir, tenant_id=None):
        """
        通过字典目录加载所有字典，并组织成结构化的数据
        返回格式: {
            'KEY类型字典编码': {
                '下级字典编码1': '字典值1',
                '下级字典编码2': '字典值2',
                ...
            },
            ...
        }
        """
        query = SysBisDict.query.filter(
            SysBisDict.dict_dir == dict_dir,
            SysBisDict.status == 1,
            SysBisDict.del_flag == 0
        )
        if tenant_id is not None:
            query = query.filter(SysBisDict.tenant_id == tenant_id)

        all_dicts = query.order_by(SysBisDict.sort.asc()).all()

        result = {}
        key_dicts = {}
        val_dicts = []

        # 先分离KEY和VAL类型的字典
        for item in all_dicts:
            if item.dict_type == 'TYPE':
                key_dicts[item.dict_code] = {
                    'value': item.dict_value,
                    'label': item.dict_label,
                    'children': {}
                }
            elif item.dict_type == 'VAL':
                val_dicts.append(item)
        # 将VAL类型的字典挂载到对应的KEY字典下
        for val_item in val_dicts:
            parent_code = val_item.parent_code
            if parent_code in key_dicts:
                key_dicts[parent_code]['children'][val_item.dict_code] = {
                    'value': val_item.dict_value,
                    'label': val_item.dict_label,
                    'cssClass': val_item.css_class,
                    'iconUrl': val_item.icon_url
                }

        # 转换格式为前端需要的结构
        for key, data in key_dicts.items():
            result[key] = {
                'value': data['value'],
                'label': data['label'],
                'children': data['children']
            }

        return result

    @staticmethod
    def get_flat_dict_by_dir(dict_dir, tenant_id=None):
        """
        获取扁平化的字典映射（只包含KEY类型的字典）
        返回格式: {
            '字典编码1': '字典值1',
            '字典编码2': '字典值2',
            ...
        }
        """
        result = SysBisDict.get_dict_by_dir(dict_dir, tenant_id)
        flat_dict = {}
        for key, data in result.items():
            flat_dict[key] = {}
            for sub_key, sub_data in data['children'].items():
                flat_dict[key][sub_key] = sub_data['value']
        return flat_dict

    # 返回系统配置，定义返回的类型是SysConfigVO
    @staticmethod
    def get_sys_config(tenant_id=None) -> SysConfigVO:
        """
        通过字典编码获取字典值
        """
        dict_list = SysBisDict.get_flat_dict_by_dir('sys_tenant_config', tenant_id)
        sys_config = dict_list.get('sys_config', {})
        sys_config_vo = SysConfigVO().map_from(sys_config)
        return sys_config_vo

    # 返回Scraper配置
    @staticmethod
    def get_scraper_config(tenant_id=None) -> ScraperCfgVo:
        """
        获取Scraper配置
        """
        dict_list = SysBisDict.get_flat_dict_by_dir('scraper', tenant_id)
        scraper_config = dict_list.get('scraper', {})
        scraper_cfg_vo = ScraperCfgVo().map_from(scraper_config)
        return scraper_cfg_vo

    # 返回平台订单配置
    @staticmethod
    def get_platform_order_config(tenant_id=None) -> PlatformOrderCfgVo:
        """
        获取平台订单配置
        """
        dict_list = SysBisDict.get_flat_dict_by_dir('platformOrder', tenant_id)
        platform_order_config = dict_list.get('platformOrder', {})
        platform_order_cfg_vo = PlatformOrderCfgVo().map_from(platform_order_config)
        return platform_order_cfg_vo

    # 返回结算佣金值（让球盘HDP/大小盘OU的单式佣金比例 singleRatio）
    @staticmethod
    def get_single_ratio(tenant_id=None) -> float:
        """
        获取结算佣金值 singleRatio，对应业务字典 platformOrder.single_ratio
        （与 Java 端 BisConfigFactory.getPlatformOrderConfig().getSingleRatio() 一致）
        """
        platform_order_config = SysBisDict.get_platform_order_config(tenant_id)
        return platform_order_config.singleRatio

    # 返回App前端配置
    @staticmethod
    def get_app_front_setting(tenant_id=None) -> AppFrontSettingVo:
        """
        获取App前端配置
        """
        dict_list = SysBisDict.get_flat_dict_by_dir('app_front_setting', tenant_id)
        app_front_setting = dict_list.get('app_front_setting', {})
        app_front_setting_vo = AppFrontSettingVo().map_from(app_front_setting)
        return app_front_setting_vo


db.create_all()