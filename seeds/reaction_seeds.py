from constants import ReactionName
from models import ReactionType


def seed_reactions(db):
    for reaction_name in ReactionName:
        existing = (
            db.query(ReactionType)
            .filter(ReactionType.name == reaction_name.value)
            .first()
        )

        if not existing:
            db.add(ReactionType(name=reaction_name.value))

    db.commit()
