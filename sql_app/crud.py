from sqlalchemy.orm import Session

from . import models, schemas


# --------------- CI/CD Nodes --------------- #

def create_ci_cd_node(db: Session, node: schemas.CI_CD_Node_Create):
    db_ci_cd_node = models.CI_CD_Node(ip=node.ip, username=node.username, password=node.password, service_id=node.service_id, testbed_id=node.testbed_id)
    db.add(db_ci_cd_node)
    db.commit()
    db.refresh(db_ci_cd_node)
    print("Created ci_cd_node")
    return db_ci_cd_node


def update_ci_cd_node(db: Session, node: schemas.CI_CD_Node_Create):
    db_ci_cd_node = db.query(models.CI_CD_Node).filter(models.CI_CD_Node.service_id == node.service_id).first()
    db_ci_cd_node.ip=node.ip
    db_ci_cd_node.username=node.username
    db_ci_cd_node.password=node.password
    db_ci_cd_node.testbed_id=node.testbed_id
    db.commit()
    db.refresh(db_ci_cd_node)
    print("Updated ci_cd_node")
    return db_ci_cd_node


def get_ci_cd_node_by_id(db: Session, id: int):
    return db.query(models.CI_CD_Node).filter(models.CI_CD_Node.id == id).first()


def get_ci_cd_node_by_service_id(db: Session, service_id: str):
    return db.query(models.CI_CD_Node).filter(models.CI_CD_Node.service_id == service_id).first()

def get_all_nodes(db: Session, skip: int = 0, limit: int = 500):
    return db.query(models.CI_CD_Node).offset(skip).limit(limit).all()


# --------------- end of CI/CD Nodes --------------- #



'''
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
    print(db.add(db_user))
    print(db.commit())
    print(db.refresh(db_user))
    print("CREATED")
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
'''