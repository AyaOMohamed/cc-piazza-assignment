from database import SessionLocal
from seeds.topic_seeds import seed_topics
from seeds.reaction_seeds import seed_reactions

def seed_database():
    db = SessionLocal()

    try:
        seed_topics(db)
        seed_reactions(db)
        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()