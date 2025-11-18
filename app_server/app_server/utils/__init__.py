from sqlalchemy.orm import sessionmaker
from sqlalchemy import and_, create_engine
from sqlalchemy import event
from sqlalchemy import exc
from app_server import app
import os

engine = create_engine('mysql+pymysql://%s:%s@%s:3306/%s?charset=utf8' % ("root", app.config["DB_PASSWORD"], app.config["DB_ADDRESS"], app.config["DATABASE"]),
                       pool_recycle=10600, pool_size=10600, max_overflow=200, isolation_level='READ COMMITTED')


# 多进程相关配置,Pool使用事件来检测自身，以便在子进程中自动使连接无效
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    connection_record.info['pid'] = os.getpid()


@event.listens_for(engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    pid = os.getpid()
    if connection_record.info['pid'] != pid:
        connection_record.connection = connection_proxy.connection = None
        raise exc.DisconnectionError(
            "Connection record belongs to pid %s, "
            "attempting to check out in pid %s" %
            (connection_record.info['pid'], pid)
        )


def get_session():
    session_class = sessionmaker(bind=engine)
    session = session_class()

    return session
