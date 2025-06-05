from core.database import init_db, Session, Contract, ContractStatus
from sqlalchemy import text

def migrate_contract_statuses():
    engine = init_db()
    session = Session(bind=engine)
    
    # Обновляем статусы напрямую через SQL
    session.execute(text("UPDATE contracts SET status = 'ACTIVE' WHERE status = 'active'"))
    session.execute(text("UPDATE contracts SET status = 'TERMINATED' WHERE status = 'terminated'"))
    session.execute(text("UPDATE contracts SET status = 'EXPIRED' WHERE status = 'expired'"))
    
    # Обновляем статусы платежей напрямую через SQL
    session.execute(text("UPDATE payments SET status = 'PENDING' WHERE status = 'pending'"))
    session.execute(text("UPDATE payments SET status = 'PAID' WHERE status = 'paid'"))
    session.execute(text("UPDATE payments SET status = 'OVERDUE' WHERE status = 'overdue'"))
    
    session.commit()
    session.close()

if __name__ == "__main__":
    migrate_contract_statuses() 