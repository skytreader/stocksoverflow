from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from typing import Any, cast, ClassVar, Iterable, Optional, List, Set, Tuple, Union

@dataclass
class SQLiteDataClass(ABC):

    UPDATE_QUERY = ""
    DELETE_QUERY = ""
    COL_MAPPING: ClassVar[dict[str, str]] = {}

    @staticmethod
    @abstractmethod
    def fetch(cursor, id: Any) -> Optional["SQLiteDataClass"]:
        """
        Fetch one record from the represented table. `id` should be enough to
        fetch a unique record. Most of the time, this can be an integer but, for
        composite keys, it can also be a tuple or an object from which the
        defining attributes can be derived.
        """
        pass

    @staticmethod
    @abstractmethod
    def from_sqlite_record(cursor, record: tuple[Any, ...]) -> "SQLiteDataClass":
        """
        Construct an instance of this class from the result of an SQLite query.
        The order of data in `record` would vary per class and should be noted
        down.

        If you prefer that instances be constructed with the auto-generated
        constructor, throw a `ConstructorPreferred` error.
        """
        pass
    
    @abstractmethod
    def insert(self, cursor, extra_args: Optional[Any] = None) -> Optional[int]:
        """
        Insert this record into the database. Return the id or, for composite
        records, the number of inserted rows.

        > TODO: Make an actual distinction between the two return types?

        Side-effect: overwrite this object's id field with the generated id,
        when applicable.
        """
        pass
    
    @abstractmethod
    def create_update_tuple(self) -> tuple[Any, ...]:
        pass

    @abstractmethod
    def create_delete_tuple(self) -> tuple[Any, ...]:
        pass

    def save(self, cursor) -> bool:
        try:
            cursor.execute(type(self).UPDATE_QUERY, self.create_update_tuple())
            return True
        except:
            return False

    def delete(self, cursor) -> bool:
        try:
            cursor.execute(type(self).DELETE_QUERY, self.create_delete_tuple())
            return True
        except:
            return False
