from datetime import datetime

def to_dict_helper(instance):
    """Shared utility for converting model instances to dictionaries"""
    d = {}
    for column in instance.__table__.columns:
        value = getattr(instance, column.name)
        if isinstance(value, datetime):
            d[column.name] = value.isoformat()
        else:
            d[column.name] = value
    return d