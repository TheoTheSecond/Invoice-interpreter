from sqlmodel import SQLModel, Session, create_engine

engine = create_engine("sqlite:///invoices.db", connect_args={"check_same_thread": False})

def create_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
