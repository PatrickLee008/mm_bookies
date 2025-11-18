from app_server import Redis, app
from app_server.model.SysBankcardModel import SysBankcard


def initialize_cards():
    # 从数据库中获取所有启用的卡，并按RANK字段排序
    enabled_cards_kbz = SysBankcard.query.filter_by(ENABLE=1, VISIBLE=0, BANK_CODE='KBZ').order_by(
        SysBankcard.RANK).all()
    enabled_cards_wave = SysBankcard.query.filter_by(ENABLE=1, VISIBLE=0, BANK_CODE='WaveMoney').order_by(
        SysBankcard.RANK).all()

    # 清空现有的Redis队列和集合
    Redis.delete('cards_queue_kbz', 'visible_cards_kbz')
    Redis.delete('cards_queue_wave', 'visible_cards_wave')

    # 将所有启用的卡添加到Redis队列
    for card in enabled_cards_kbz:
        Redis.rpush('cards_queue_kbz', card.ID)

    for card in enabled_cards_wave:
        Redis.rpush('cards_queue_wave', card.ID)

    # 从数据库中获取所有启用且VISIBLE为1的卡
    visible_cards_kbz = SysBankcard.query.filter_by(ENABLE=1, VISIBLE=1, BANK_CODE='KBZ').order_by(
        SysBankcard.RANK).all()
    visible_cards_wave = SysBankcard.query.filter_by(ENABLE=1, VISIBLE=1, BANK_CODE='WaveMoney').order_by(
        SysBankcard.RANK).all()

    # 将VISIBLE为1的卡添加到Redis集合
    for card in visible_cards_kbz:
        Redis.sadd('visible_cards_kbz', card.ID)

    for card in visible_cards_wave:
        Redis.sadd('visible_cards_wave', card.ID)


@app.before_first_request
def before_first_request():
    initialize_cards()
