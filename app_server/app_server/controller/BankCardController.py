from app_server import app, db, auth, app_opt
from app_server.model.AppMemberBankModel import AppMemberBank
from flask import g, request, jsonify, Blueprint
from app_server.utils import OrmUttil
import uuid
import hashlib

from app_server.utils.Kits import Kits

bank_card = Blueprint('bank_card', __name__)


@bank_card.route('/get', methods=['GET'])
@auth.login_required
def get_bank_cards():
    """ get_bank_cards API Endpoint
        ---
        tags:
          - bank_card
        responses:
          200:
            description: { 'items': [...], 'total': 100 }
        """
    try:
        bank_cards = AppMemberBank.query.filter_by(mb_id=g.user.id, del_flag=0).order_by(
            AppMemberBank.is_default.desc(),
            AppMemberBank.create_time.asc()).all()
        return jsonify({'items': [u.to_dict() for u in bank_cards]})
    except Exception as e:
        print("user info error:", e)


@bank_card.route('/add', methods=['POST'])
@auth.login_required
def add_bank_card():
    """ add_bank_card API Endpoint
        ---
        tags:
          - bank_card
        parameters:
          - in: body
            name: body
            required: true
            description: bank_card info to add
            schema:
              type: object
              required:
                - acc_number
                - bank_code
                - acc_name
              properties:
                acc_number:
                  type: string
                  description: the acc_number of the bank_card
                  example: ""
                bank_code:
                  type: string
                  description: the bank_code of the bank_card
                  example: ""
                acc_name:
                  type: string
                  description: the acc_name of the bank_card
                  example: ""
        responses:
          500:
            description: System or Technical Error.
          200:
            description: 绑定成功
        """

    args = request.get_json()
    acc_number = args.get("acc_number")
    bank_code = args.get("bank_code")
    acc_name = args.get("acc_name")

    try:
        card = AppMemberBank.query.filter_by(acc_number=acc_number, bank_code=bank_code).one_or_none()
        if card:
            response = jsonify({'message': "The bankcard already exists. Please save with a different bankcard"})
            response.status_code = 400
            return response
        user_card_count = AppMemberBank.query.filter_by(mb_id=g.user.id).count()
        if user_card_count >= 5:
            response = jsonify({'message': "Up to five bank accounts can be added"})
            response.status_code = 429
            return response

        card = AppMemberBank(id=Kits.generate_uuid(), acc_number=acc_number, mb_id=g.user.id, bank_code=bank_code,
                             acc_name=acc_name)
        card_count = AppMemberBank.query.filter_by(mb_id=g.user.id).count()
        if card_count == 0:
            card.is_default = 1
        db.session.add(card)

        db.session.commit()
        return jsonify({'message': "save success"})
    except Exception as e:
        db.session.rollback()
        print("add card error:", e)

    response = jsonify({'message': "System or Technical Error."})
    response.status_code = 500
    return response


@bank_card.route('/edit', methods=['POST'])
@auth.login_required
def edit_bank_card():
    """ edit_bank_card API Endpoint
        ---
        tags:
          - bank_card
        parameters:
          - in: body
            name: body
            required: true
            description: bank_card info to edit
            schema:
              type: object
              required:
                - ID
              properties:
                ID:
                  type: string
                  description: the ID of the bank_card
                  example: ""
                acc_number:
                  type: string
                  description: the acc_number of the bank_card
                  example: ""
                bank_code:
                  type: string
                  description: the bank_code of the bank_card
                  example: ""
                acc_name:
                  type: string
                  description: the acc_name of the bank_card
                  example: ""
        responses:
          500:
            description: System or Technical Error.
          200:
            description: edit successful.
        """
    args = request.get_json()
    edit_id = args.get("ID")

    try:
        card = AppMemberBank.query.filter_by(ID=edit_id).one_or_none()
        args.pop("ID")
        OrmUttil.set_field(card, args)
        db.session.commit()
        return jsonify({'message': "edit successful."})
    except Exception as e:
        db.session.rollback()
        response = jsonify({'message': "System or Technical Error."})
        response.status_code = 500
        return response


@bank_card.route('/delete', methods=['POST'])
@auth.login_required
def delete_bank_card():
    """ delete_bank_card API Endpoint
        ---
        tags:
          - bank_card
        parameters:
          - in: body
            name: body
            required: true
            description: bank_card info to delete
            schema:
              type: object
              required:
                - ID
              properties:
                ID:
                  type: string
                  description: the ID of the bank_card
                  example: ""
        responses:
          500:
            description: System or Technical Error.
          200:
            description: 解绑成功
        """
    args = request.get_json()
    edit_id = args.get("id")

    try:
        AppMemberBank.query.filter_by(id=edit_id).delete()
        db.session.commit()
        return jsonify({'message': "解绑成功"})
    except Exception as e:
        db.session.rollback()
        response = jsonify({'message': "System or Technical Error."})
        response.status_code = 500
        return response


@bank_card.route('/set_default', methods=['POST'])
@auth.login_required
def set_default_bank_card():
    """ set_default_bank_card API Endpoint
        ---
        tags:
          - bank_card
        parameters:
          - in: body
            name: body
            required: true
            description: bank_card info to set default
            schema:
              type: object
              required:
                - ID
              properties:
                ID:
                  type: string
                  description: the ID of the bank_card
                  example: ""
        responses:
          500:
            description: System or Technical Error.
          200:
            description: 设置成功
        """
    args = request.get_json()
    edit_id = args.get("ID")

    try:
        card = AppMemberBank.query.filter_by(ID=edit_id).one_or_none()
        card.PRIMARY_CARD = True
        AppMemberBank.query.filter(AppMemberBank.id == card.id, AppMemberBank.BANK_TYPE == card.BANK_TYPE,
                                   AppMemberBank.ID != card.ID).update({'PRIMARY_CARD': False},
                                                                       synchronize_session=False)
        db.session.commit()
        return jsonify({'message': "设置成功"})
    except Exception as e:
        db.session.rollback()
        response = jsonify({'message': "System or Technical Error."})
        response.status_code = 500
        return response
