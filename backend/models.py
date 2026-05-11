import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, DateTime, ForeignKey, create_engine
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
from pgvector.sqlalchemy import Vector
from config import Config

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(String(255))
    original_name = Column(Text)
    normalized_name = Column(Text)
    description = Column(Text)
    category = Column(String(255))
    embedding = Column(Vector(1536))
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

    clusters = relationship('Cluster', back_populates='canonical_product')
    match_edges_a = relationship('MatchEdge', foreign_keys='MatchEdge.product_a_id', back_populates='product_a')
    match_edges_b = relationship('MatchEdge', foreign_keys='MatchEdge.product_b_id', back_populates='product_b')

class Cluster(Base):
    __tablename__ = 'clusters'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_product_id = Column(UUID(as_uuid=True), ForeignKey('products.id'))
    size = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

    canonical_product = relationship('Product', back_populates='clusters')

class MatchEdge(Base):
    __tablename__ = 'match_edges'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_a_id = Column(UUID(as_uuid=True), ForeignKey('products.id'))
    product_b_id = Column(UUID(as_uuid=True), ForeignKey('products.id'))
    similarity_score = Column(Float)
    status = Column(String(50), default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)

    product_a = relationship('Product', foreign_keys=[product_a_id], back_populates='match_edges_a')
    product_b = relationship('Product', foreign_keys=[product_b_id], back_populates='match_edges_b')

engine = create_engine(Config.DATABASE_URL)

def init_db():
    Base.metadata.create_all(engine)