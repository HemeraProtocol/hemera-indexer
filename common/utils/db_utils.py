def build_entities(model, columns):
    if columns == "*":
        entities = [attr for attr in model.__table__.columns]
    else:
        entities = []
        for column in columns:
            if isinstance(column, tuple):
                col, alias = column
                entities.append(getattr(model, col).label(alias))
            else:
                entities.append(getattr(model, column))

    return entities
