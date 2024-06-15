from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import Session

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    balance = Column(Integer, default=0)
    increment = Column(Integer, default=1)


Base.metadata.create_all(bind=engine)


'''БД users СОСТОИТ ИЗ id(id пользователя) username(ник пользователя) balance(баланс) increment(кол-во монет за тап)'''


def get_user(db: Session, user_id: int):
    '''функция возвращает информацию о пользователе по его id'''
    return db.query(User).filter(User.id == user_id).first()


def create_user(db, user_id: int, username: str):
    '''добавление пользоваеля в бд'''
    db_user = User(id=user_id, username=username)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_balance(db: Session, user_id: int, amount: int):
    '''обновление баланса пользователя'''
    db_user = get_user(db, user_id)
    if db_user:
        db_user.balance += amount
        db.commit()
        db.refresh(db_user)
        return db_user


def get_top_users(db: Session):
    '''функция для топа'''
    return db.query(User).order_by(User.balance.desc()).limit(10).all()


def initialize_users(db: Session):
    '''инициализация тапов пользователя. дефолт 1🥮 за тап'''
    users = db.query(User).all()
    for user in users:
        if user.increment is None:
            user.increment = 1
    db.commit()


db = SessionLocal()
initialize_users(db)







