#!/usr/bin/python3
# -*- coding: utf-8 -*-

from functools import partial

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import orm


class RoutingSession(orm.Session):
    def __init__(self, db, autocommit=False, autoflush=True, **options):
        self.app = db.get_app()
        self.db = db
        self._bind_name = None
        orm.Session.__init__(
            self,
            autocommit=autocommit,
            autoflush=autoflush,
            bind=db.engine,
            binds=db.get_binds(self.app),
            **options,
        )

    def get_bind(self, mapper=None, clause=None):
        # try:
        #     state = get_state(self.app)
        # except (AssertionError, AttributeError, TypeError) as err:
        #     current_app.logger.info("cant get configuration. default bind. Error:" + err)
        #     return orm.Session.get_bind(self, mapper, clause)

        # If there are no binds configured, use default SQLALCHEMY_DATABASE_URI
        if not self.app.config["SQLALCHEMY_BINDS"]:
            return orm.Session.get_bind(self, mapper, clause)

        # if want to user exact bind
        # if self._bind_name:
        #     return state.db.get_engine(self.app, bind=self._bind_name)
        # else:
        # if no bind is used connect to default
        return orm.Session.get_bind(self, mapper, clause)

    def using_bind(self, name):
        bind_session = RoutingSession(self.db)
        vars(bind_session).update(vars(self))
        bind_session._bind_name = name
        return bind_session


class RouteSQLAlchemy(SQLAlchemy):
    def __init__(self, *args, **kwargs):
        SQLAlchemy.__init__(self, *args, **kwargs)
        self.session.using_bind = lambda s: self.session().using_bind(s)

    def create_scoped_session(self, options=None):
        if options is None:
            options = {}
        scopefunc = options.pop("scopefunc", None)
        return orm.scoped_session(
            partial(RoutingSession, self, **options),
            scopefunc=scopefunc,
        )
