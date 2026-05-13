from app_server import db
from app_server.model.AppMemberModel import AppMember

account = '0918918918'
new_passwd = 'Abc123123'

app_member = AppMember.query.filter_by(username = account).first()
if app_member:
    app_member.set_psw(new_passwd)

db.session.commit()