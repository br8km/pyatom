# -*- coding: utf-8 -*-

"""
    Object-Relational Mapping for database
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


__all__ = ("ORM",)


Base = declarative_base()


class ORM:
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


class Sqlite(ORM):
    """Sqlite ORM."""

    def __init__(self, db_file: Path, echo: bool = False, future: bool = True) -> None:
        url = f"sqlite:///{db_file.absolute()}"
        engine = create_engine(url, echo=echo, future=future)

        super().__init__(engine=engine, future=future)
        # self.create_tables()


class PostgreSQL(ORM):
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
        url = f"postgresql+{driver}://{db_user}:{db_pass}@{db_host}/{db_name}"
        engine = create_engine(url, echo=echo, future=future)

        super().__init__(engine=engine, future=future)
        # self.create_tables()


class MySQL(ORM):
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
        url = f"mysql+{driver}://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"
        engine = create_engine(url, encoding=encoding, echo=echo, future=future)

        super().__init__(engine=engine, future=future)
        # self.create_tables()
