from datetime import datetime

from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.sqltypes import DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

quote_m2m_tag = Table(
    "quote_m2m_tag",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("tag", Integer, ForeignKey("tags.id")),
    Column("quote", Integer, ForeignKey("quotes.id")),
)


class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    fullname = Column(String(50), nullable=False, unique=True)
    born_date = Column(DateTime, nullable=True)
    bio = Column(String(10000), nullable=True)
    born_location = Column(String(250), nullable=True)
    created = Column(DateTime, default=datetime.now())


class Quote(Base):
    __tablename__ = "quotes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey(Author.id, ondelete="CASCADE"))
    content = Column(String(2500))
    tags = relationship("Tag", secondary=quote_m2m_tag, backref="quotes")
    created = Column(DateTime, default=datetime.now())

    def __repr__(self):
        return f"{self.author}: " + ", ".join([str(x) for x in self.tags])


class Tag(Base):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String(25), nullable=False, unique=True)

    def __repr__(self) -> str:
        return self.name


