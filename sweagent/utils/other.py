
def is_true(value: bool | str) -> bool:
    """either boolean true or stringified true"""
    return (value is True) or (isinstance(value, str) and value.lower() in ["true", "1"])
