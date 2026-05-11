import os
import numpy as np
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session
from models import Product, Cluster, MatchEdge, init_db, engine
from config import Config

client = OpenAI(api_key=Config.OPENAI_API_KEY)

def generate_embedding(text):
    if not text:
        text = '[MISSING]'
    response = client.embeddings.create(
        model='text-embedding-ada-002',
        input=text
    )
    return np.array(response.data[0].embedding)

def compute_tfidf_similarity(products):
    texts = [p.normalized_name or '' for p in products]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(texts)
    return cosine_similarity(tfidf_matrix)

def find_duplicates_tfidf(session, threshold=0.7):
    products = session.query(Product).all()
    if len(products) < 2:
        return []

    similarity_matrix = compute_tfidf_similarity(products)
    duplicates = []

    for i in range(len(products)):
        for j in range(i + 1, len(products)):
            if similarity_matrix[i][j] > threshold:
                edge = MatchEdge(
                    product_a_id=products[i].id,
                    product_b_id=products[j].id,
                    similarity_score=float(similarity_matrix[i][j]),
                    status='pending'
                )
                duplicates.append(edge)

    return duplicates

def match_products_with_embeddings(session, threshold=0.85):
    products = session.query(Product).all()
    matches = []

    for i, p1 in enumerate(products):
        if p1.embedding is None:
            text = f"{p1.normalized_name or ''} {p1.description or ''}"
            p1.embedding = generate_embedding(text)

        for j in range(i + 1, len(products)):
            p2 = products[j]
            if p2.embedding is None:
                text = f"{p2.normalized_name or ''} {p2.description or ''}"
                p2.embedding = generate_embedding(text)

            similarity = cosine_similarity(
                p1.embedding.reshape(1, -1),
                p2.embedding.reshape(1, -1)
            )[0][0]

            if similarity > threshold:
                match = MatchEdge(
                    product_a_id=p1.id,
                    product_b_id=p2.id,
                    similarity_score=float(similarity),
                    status='pending'
                )
                matches.append(match)

    session.add_all(matches)
    session.commit()
    return len(matches)

def create_clusters(session):
    pending_edges = session.query(MatchEdge).filter_by(status='confirmed').all()
    cluster_map = {}
    products_map = {p.id: p for p in session.query(Product).all()}

    for edge in pending_edges:
        for pid in [edge.product_a_id, edge.product_b_id]:
            if pid not in cluster_map:
                cluster_map[pid] = set()
            cluster_map[pid].add(edge.product_a_id)
            cluster_map[pid].add(edge.product_b_id)

    clusters = []
    visited = set()
    for root_pid in cluster_map:
        if root_pid in visited:
            continue
        members = cluster_map[root_pid]
        visited.update(members)

        if len(members) > 1:
            canonical_id = root_pid
            cluster = Cluster(
                canonical_product_id=canonical_id,
                size=len(members)
            )
            clusters.append(cluster)

    session.add_all(clusters)
    session.commit()
    return len(clusters)