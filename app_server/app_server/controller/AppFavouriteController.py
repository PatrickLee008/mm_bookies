from app_server import app, db, auth, app_opt
from app_server.model.AppFavouriteModel import AppFavourite
from flask import g, request, jsonify, Blueprint
from app_server.utils import OrmUttil
import ipaddress
import uuid
import hashlib
import datetime

from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import json
from app_server.utils.Kits import Kits

favourite = Blueprint('favourite', __name__)


# 收藏夹
@favourite.route('/list', methods=['POST'])
@auth.login_required
def favourite_list():
    # 获取用户收藏夹，按添加时间排序
    mbid = g.user.id
    list = AppFavourite.query.filter_by(mb_id=mbid).order_by(AppFavourite.create_time.desc()).all()
    # 转换为字典列表
    list_dict = [item.to_dict() for item in list]
    return Kits.rt_data(list_dict)


# 允许所有类型请请
@favourite.route('/add', methods=['POST'])
@auth.login_required
def favourite_add():
    """ favourite_add API Endpoint
        ---
        tags:
          - favourite
        parameters:
          - in: body
            name: body
            required: true
            description: Favourite Info To Add
            schema:
              type: object
              required:
                - league
              properties:
                league:
                  type: string
                  description: the league of the favourite
                  example: ""
                team:
                  type: string
                  description: the team of the favourite
                  example: ""
        responses:
          500:
            description: league and team is already exist
          500:
            description: league is already exist
          200:
            description: add success
        """
    # 添加
    # 获取联赛和球队名称
    args = request.get_json()
    league = args.get('league')
    team = args.get('team')
    mbid = g.user.id
    # 检查是否已经收藏过
    if Kits.is_empty(league):
        return Kits.rt_error("league is null")

    if Kits.is_empty(team):
        # 仅添加league
        obj = AppFavourite.query.filter_by(league=league, mb_id=mbid).first()
        if obj is None:
            obj = AppFavourite(id=Kits.generate_uuid(), league=league, mb_id=mbid)
            db.session.add(obj)
            db.session.commit()
            return Kits.rt_ok("add success")
        else:
            return Kits.rt_error("league is already exist")
    else:
        # 添加league和team
        obj = AppFavourite.query.filter_by(league=league, team=team, mb_id=mbid).first()
        if obj is None:
            obj = AppFavourite(id=Kits.generate_uuid(), league=league, team=team, mb_id=mbid)
            db.session.add(obj)
            db.session.commit()
            return Kits.rt_ok("add success")
        else:
            return Kits.rt_error("league and team is already exist")


@favourite.route('/delete', methods=['POST'])
@auth.login_required
def favourite_delete():
    """ favourite_delete API Endpoint
        ---
        tags:
          - favourite
        parameters:
          - in: body
            name: body
            required: true
            description: Favourite Info To Delete
            schema:
              type: object
              properties:
                id:
                  type: string
                  description: the id of the favourite
                  example: ""
                league:
                  type: string
                  description: the league of the favourite
                  example: ""
        responses:
          500:
            description: favourite is not exist
          200:
            description: delete success
        """
    args = request.get_json()
    id = args.get('id')
    league = args.get('league')
    mbid = g.user.id
    if id:
        obj = AppFavourite.query.filter_by(id=id, mb_id=mbid).first()
    else:
        obj = AppFavourite.query.filter_by(mb_id=mbid, league=league).first()
    if obj is None:
        return Kits.rt_error("favourite is not exist")
    db.session.delete(obj)
    db.session.commit()
    return Kits.rt_ok("delete success")
