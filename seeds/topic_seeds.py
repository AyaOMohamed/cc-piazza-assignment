from constants import TopicName
from models import Topic

def seed_topics(db):
    for topic_name in TopicName:
        existing = (
            db.query(Topic)
            .filter(Topic.name == topic_name.value)
            .first()
        )

        if not existing:
            db.add(Topic(name=topic_name.value))

    db.commit()