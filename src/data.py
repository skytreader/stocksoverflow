from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from datetime import date
from enum import StrEnum, auto
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


def starfields(cls, noid: bool = False, col_mapping: Optional[dict[str, str]] = None) -> str:
    """
    Return a comma-separated string listing all the fields of this class.
    The order output is consistent with, for example, `from_sqlite_record`.

    NOTE: This assumes that the `dataclasses.fields` function returns the
    declaration order of the fields. The closest guarantee we have is the
    following claim in the docs:

    > The order of the fields in all of the generated methods is the order
    > in which they appear in the class definition.

    But the thing is, `fields` is not a generated method!

    Params:

    cls -- The dataclass we are listing the fields of
    noid -- If True we list the fields omitting a field named "id"
    col_mapping -- A dictionary mapping dataclass field names to SQL columns.
    You only need to specify those that actually differ.
    """
    def _map(name):
        if col_mapping is None:
            return name
        else:
            return col_mapping.get(name, name)

    if noid:
        return ",".join([_map(f.name) for f in fields(cls) if f.name != "id"])
    else:
        return ",".join([_map(f.name) for f in fields(cls)])

@dataclass
class MetadataRecord(SQLiteDataClass):
    key: str
    val: str
    UPDATE_QUERY = """
        UPDATE __metadata
        SET key=?,
        val=?
        WHERE key=?
        LIMIT 1
    """
    DELETE_QUERY = """
        DELETE FROM __metadata
        WHERE key=?
        LIMIT 1
    """

    @staticmethod
    def fetch(cursor, id: str) -> Optional["MetadataRecord"]:
        query = "SELECT key, val FROM __metadata WHERE key=? LIMIT 1"
        result = cursor.execute(query, (id,)).fetchone()
        return MetadataRecord(*result) if result is not None else None

    @staticmethod
    def from_sqlite_record(cursor, record: tuple[Any, ...]) -> "MetadataRecord":
        raise ConstructorPreferred()
    
    def insert(self, cursor, extra_args: Optional[Any] = None) -> Optional[int]:
        """
        Since there is no integer id for this table, this only returns either 1
        or 0 for a successful and unsuccessful insertion respectively.
        """
        try:
            cursor.execute(
                "INSERT INTO __metadata (key, val) VALUES (?, ?)",
                (self.key, self.val)
            )
            return 1
        except:
            return 0

    def create_update_tuple(self) -> tuple[Any, ...]:
        return (self.key, self.val, self.key)

    def create_delete_tuple(self) -> tuple[Any, ...]:
        return (self.key,)


class FundType(StrEnum):
    FUND = auto()
    STOCK = auto()

class StockAssessment(StrEnum):
    STABLE = auto()
    RISKY = auto()

class StockStrategy(StrEnum):
    LONG_TERM = auto()
    SHORT_TERM = auto()

@dataclass
class FundTransactionRecord(SQLiteDataClass):
    id: Optional[int]
    date: date
    fund_name: str
    transaction_price: float
    fund_type: FundType
    shares: Optional[float]
    notes: str
    
    @staticmethod
    def fetch(cursor, id) -> Optional["FundTransactionRecord"]:
        query = f"SELECT {starfields(FundTransactionRecord)} FROM fund_transactions WHERE id=? LIMIT 1"
        result = cursor.execute(query, (id,)).fetchone()
        return FundTransactionRecord.from_sqlite_record(cursor, result) if result is not None else None

    @staticmethod
    def from_sqlite_record(cursor, record: tuple[int, date, str, float, str, float, str]) -> "FundTransactionRecord":
        return FundTransactionRecord(
            record[0],
            record[1],
            record[2],
            record[3],
            FundType(record[4]),
            record[5],
            record[6]
        )

@dataclass
class StockStrategyRecord(SQLiteDataClass):
    stock_name: str
    total_in: float
    total_shares: float
    assessment: StockAssessment
    strategy: StockStrategy

    @staticmethod
    def fetch(cursor, id: str) -> Optional["StockStrategyRecord"]:
        query = f"SELECT {starfields(StockStrategyRecord)} FROM stock_strategies WHERE stock_name=? LIMIT 1"
        result = cursor.execute(query, (id,)).fetchone()
        return StockStrategyRecord.from_sqlite_record(cursor, result) if result is not None else None

    @staticmethod
    def from_sqlite_record(cursor, record: tuple[str, float, float, str, str]) -> "StockStrategyRecord":
        return StockStrategyRecord(
            tuple[0],
            tuple[1],
            tuple[2],
            StockAssessment(tuple[3]),
            StockAssessment(tuple[4])
        )
