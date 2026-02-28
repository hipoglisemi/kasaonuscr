
from src.database import get_db_session
from src.models import Bank

def list_banks():
    db = get_db_session()
    try:
        print(f"{'ID':<5} | {'NAME':<30} | {'SLUG':<30}")
        print("-" * 70)
        banks = db.query(Bank).order_by(Bank.name).all()
        for b in banks:
            print(f"{b.id:<5} | {b.name:<30} | {b.slug:<30}")
    finally:
        db.close()

if __name__ == "__main__":
    list_banks()
