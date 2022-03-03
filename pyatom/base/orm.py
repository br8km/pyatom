# -*- coding: utf-8 -*-

"""
    Database Object-Relational Mapping
"""

# mypy: ignore-errors

from pathlib import Path
from typing import Any, List

import arrow

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import Column, Integer, String, Boolean

from pyatom.config import DIR_DEBUG


__all__ = ("Database",)


Base = declarative_base()


class Database:
    """ORM derive from sqlalchemy."""

    def __init__(self, engine: Engine, future: bool = True) -> None:
        self.engine = engine
        self.session_factory = sessionmaker(bind=self.engine, future=future)
        """create a thread-local safe session"""
        self.session = scoped_session(self.session_factory)

    def create_tables(self) -> None:
        """Create tables."""
        Base.metadata.create_all(self.engine)

    def exit(self) -> None:
        """exit session"""
        self.session.remove()

    @staticmethod
    def log(message: Any) -> None:
        """logging message"""
        now = arrow.now().format("YYYY-MM-DD HH:mm:ss")
        print(f"{now} - {message}")

    @staticmethod
    def tables():
        """return tables"""
        return Base.metadata.tables

    @staticmethod
    def table_names() -> List[str]:
        """return table names"""
        return list(Base.metadata.tables.keys())

    # start query functions

    def core_insert(self, obj_table: Base, dict_item: dict) -> bool:
        """
        Insert data using core function, Native and Fast

        :param obj_table: OBJECT for :class:`obj_table <object>`.
        :param dict_item: ITEM for :class:`<dict>`.

        """
        result = False
        with self.engine.connect() as conn:  # type: ignore
            conn.execute(obj_table.__table__.insert(), dict_item)
            result = True
        return result

    def core_insert_bulk(self, obj_table: Base, dict_items: List[dict]) -> bool:
        """
        Insert Bulk data using core function, Native and Fast

        :param obj_table: OBJECT for :class:`obj_table <object>`.
        :param dict_items: ITEMS for :class:`<list>`.

        """
        result = False
        with self.engine.connect() as conn:  # type: ignore
            conn.execute(obj_table.__table__.insert(), dict_items)
            result = True
        return result

    def core_update(self, obj_table: Base, item_id: int, dict_item: dict) -> bool:
        """
        Update data using core function, Native and Fast

        :param obj_table: OBJECT for :class:`obj_table <object>`.
        :param item_id: ITEM_ID for :class:`id <int>`.
        :param dict_item: ITEM for :class:`<dict>`.

        """
        result = False
        with self.engine.connect() as conn:  # type:ignore
            conn.execute(
                obj_table.__table__.update()
                .where(obj_table.id == item_id)
                .values(dict_item)
            )
            result = True
        return result

    def core_delete(self, obj_table: Base, item_id: int) -> bool:
        """
        Delete data using core function, Native and Fast

        :param obj_table: OBJECT for :class:`obj_table <object>`.
        :param item_id: ITEM_ID for :class:`id <int>`.

        """
        result = False
        with self.engine.connect() as conn:  # type:ignore
            conn.execute(obj_table.__table__.delete().where(obj_table.id == item_id))
            result = True
        return result

    def add(self, obj_table: Base, dict_item: dict) -> int:
        """
        Add data using orm function, thread_safe session method

        :param obj_table: OBJECT for :class:`obj_table <object>`.
        :param dict_item: ITEM for :class:`<dict>`.

        """
        try:
            item = obj_table(**dict_item)
            self.session.add(item)  # type:ignore
            self.session.commit()  # type:ignore
            return item.id
        except SQLAlchemyError as err:
            self.log(err)
            self.session.rollback()  # type:ignore
        return 0

    def add_bulk(self, obj_table: Base, dict_items: List[dict]) -> bool:
        """
        Add bulk data using orm function, thread_safe session method

        :param obj_table: OBJECT for :class:`obj_table <object>`.
        :param dict_items: ITEMS for :class:`<list>`.

        """
        try:
            self.session.bulk_insert_mappings(  # type:ignore
                obj_table, dict_items
            )
            self.session.commit()  # type:ignore
            return True
        except SQLAlchemyError as err:
            self.log(err)
            self.session.rollback()  # type:ignore
        return False

    def update(self, obj_table: Base, item_id: int, dict_item: dict) -> bool:
        """
        Update data using orm function, thread_safe session method

        :param obj_table: OBJECT for :class:`obj_table <object>`.
        :param item_id: ITEM ID for :class:`id <int>`.
        :param dict_items: ITEMS for :class:`<dict>`.

        """
        try:
            result = (
                self.session.query(obj_table)
                .filter(  # type:ignore
                    obj_table.id == item_id
                )
                .update(dict_item)
            )
            self.session.commit()  # type:ignore
            return result == 1
        except SQLAlchemyError as err:
            self.log(err)
            self.session.rollback()  # type:ignore
        return False

    def delete(self, obj_table: Base, item_id: int) -> bool:
        """
        Delete data using orm function, thread_safe session method

        :param obj_table: OBJECT for :class:`obj_table <object>`.
        :param item_id: ITEM ID for :class:`id <int>`.

        """
        try:
            result = (
                self.session.query(obj_table)
                .filter(  # type:ignore
                    obj_table.id == item_id
                )
                .delete()
            )
            self.session.commit()  # type:ignore
            return result == 1
        except SQLAlchemyError as err:
            self.log(err)
            self.session.rollback()  # type:ignore
        return False

    def select(self, obj_table: Base, item_id: int) -> list[Base]:
        """
        Select data using orm function, thread_safe session method

        :param obj_table: OBJECT for :class:`obj_table <object>`.
        :param item_id: ITEM ID for :class:`id <int>`.

        """
        try:
            result = (
                self.session.query(obj_table)
                .filter(  # type:ignore
                    obj_table.id == item_id
                )
                .all()
            )
            self.session.commit()  # type:ignore
            return result
        except SQLAlchemyError as err:
            self.log(err)
            self.session.rollback()  # type:ignore
        return []

    def truncate(self, obj_table: Base) -> bool:
        """
        Truncate data using orm function, thread_safe session method

        :param obj_table: OBJECT for :class:`obj_table <object>`.

        """
        try:
            self.session.query(obj_table).delete()  # type:ignore
            self.session.commit()  # type:ignore
            return True
        except SQLAlchemyError as err:
            self.log(err)
            self.session.rollback()  # type:ignore
        return False

    def drop(self, obj_table: Base) -> bool:
        """
        Drop Table if exists.

        :param obj_table: OBJECT for :class:`obj_table <object>`.

        """
        try:
            obj_table.__table__.drop(self.engine, checkfirst=True)
            return True
        except SQLAlchemyError as err:
            self.log(err)
        return False

    def create(self, obj_table: Base) -> bool:
        """
        Create Table if not exists

        :param obj_table: OBJECT for :class:`obj_table <object>`.

        """
        try:
            obj_table.__table__.create(self.engine, checkfirst=True)
            return True
        except SQLAlchemyError as err:
            self.log(err)
        return False

    def check_args(self, valid: list, incoming: list, update: bool = False) -> bool:
        """check incoming arguments against valid arguments"""
        extra = [arg for arg in incoming if arg not in valid]
        lack = [arg for arg in valid if arg not in incoming]
        if extra:
            self.log(f"extra arguments: {extra}")
        if lack:
            if update:
                return not extra
            self.log(f"missing arguments: {lack}")
        return not extra and not lack


class Sqlite(Database):
    """Sqlite ORM."""

    def __init__(self, db_file: Path, echo: bool = False, future: bool = True) -> None:
        """Init Sqlite."""
        file_str = str(db_file.absolute())
        engine = create_engine(url=f"sqlite:///{file_str}", echo=echo, future=future)

        super().__init__(engine=engine, future=future)
        # self.create_tables()


class PostgreSQL(Database):
    """PostgreSQL ORM."""

    def __init__(
        self,
        db_user: str,
        db_pass: str,
        db_host: str,
        db_name: str,
        driver: str = "psycopg2",
        echo: bool = False,
        future: bool = True,
    ) -> None:
        """Init PostgreSQL."""
        url = f"postgresql+{driver}://{db_user}:{db_pass}@{db_host}/{db_name}"
        engine = create_engine(url, echo=echo, future=future)

        super().__init__(engine=engine, future=future)
        # self.create_tables()


class MySQL(Database):
    """MySQL ORM."""

    def __init__(
        self,
        db_user: str,
        db_pass: str,
        db_host: str,
        db_port: int,
        db_name: str,
        driver: str = "pymysql",
        encoding: str = "latin1",
        echo: bool = False,
        future: bool = True,
    ) -> None:
        """Init MySQL."""
        url = f"mysql+{driver}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
        engine = create_engine(url, encoding=encoding, echo=echo, future=future)

        super().__init__(engine=engine, future=future)
        # self.create_tables()


class TableDomain(Base):
    """Domain table"""

    __tablename__ = "TableDomain"
    __table_args__ = {"comment": "Table.Domain"}

    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    country = Column(String(2), nullable=False, index=True)
    netloc = Column(String(63), nullable=False, index=True)
    root = Column(Boolean, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<TableDomain(id={self.id}, country='{self.country}', netloc='{self.netloc}', root={self.root})>"


class TestDatabase:
    """Test Database ORM Operation."""

    dir_test = DIR_DEBUG

    def test_orm_sqlite(self) -> None:
        """test orm for sqlite3 database."""
        db_file = Path(self.dir_test, "db.sqlite")
        db_file.unlink(missing_ok=True)

        orm = Sqlite(db_file=db_file, echo=True)
        orm.create_tables()

        dict_domain = {"country": "US", "netloc": "www.google.com", "root": False}

        table_id = orm.add(TableDomain, dict_domain)
        assert isinstance(table_id, int)
        assert orm.update(
            TableDomain,
            item_id=table_id,
            dict_item={"netloc": "bing.com", "root": True},
        )
        assert orm.delete(TableDomain, item_id=table_id)
        db_file.unlink(missing_ok=True)

    def test_orm_mysql(self) -> None:
        """test orm for mysql database."""

    def test_orm_postgresql(self) -> None:
        """test orm for postgresql database."""


if __name__ == "__main__":
    TestDatabase()
