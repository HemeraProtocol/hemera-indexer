from typing import Any, List, Literal, Union

from sqlmodel import select

ColumnType = Union[Literal["*"], str, List[str]]


def process_columns(model_class: Any, columns: ColumnType):
    """Helper function to process column input

    Args:
        model_class: SQLModel class to select from
        columns: Can be "*", single column name, or list of column names

    Returns:
        statement: Select statement
    """
    if columns == "*":
        return select(model_class)

    if isinstance(columns, str):
        columns = [col.strip() for col in columns.split(",")]

    return select(*[getattr(model_class, col.strip()) for col in columns])
