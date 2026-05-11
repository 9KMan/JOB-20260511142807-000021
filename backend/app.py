from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy.orm import Session
from sqlalchemy import text
from models import Product, Cluster, MatchEdge, init_db, engine
from importer import import_csv
from matching import find_duplicates_tfidf, match_products_with_embeddings, create_clusters, generate_embedding
from config import Config
import numpy as np

app = Flask(__name__)
CORS(app)

@app.route('/api/import', methods=['POST'])
def import_products():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    supplier_id = request.form.get('supplier_id', 'unknown')
    column_mapping = request.form.get('column_mapping')

    import io
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
        file.save(tmp.name)
        count = import_csv(tmp.name, supplier_id)

    return jsonify({'success': True, 'imported': count})

@app.route('/api/products', methods=['GET'])
def list_products():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    search = request.args.get('search', '')

    with Session(engine) as session:
        query = session.query(Product)
        if search:
            query = query.filter(Product.normalized_name.ilike(f'%{search}%'))
        total = query.count()
        products = query.offset((page - 1) * per_page).limit(per_page).all()

        return jsonify({
            'products': [{
                'id': str(p.id),
                'supplier_id': p.supplier_id,
                'original_name': p.original_name,
                'normalized_name': p.normalized_name,
                'description': p.description,
                'category': p.category,
                'created_at': p.created_at.isoformat() if p.created_at else None
            } for p in products],
            'total': total,
            'page': page,
            'per_page': per_page
        })

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    with Session(engine) as session:
        product = session.query(Product).filter_by(id=product_id).first()
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        edges = session.query(MatchEdge).filter(
            (MatchEdge.product_a_id == product_id) | (MatchEdge.product_b_id == product_id)
        ).all()

        return jsonify({
            'id': str(product.id),
            'supplier_id': product.supplier_id,
            'original_name': product.original_name,
            'normalized_name': product.normalized_name,
            'description': product.description,
            'category': product.category,
            'metadata': product.metadata,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'matches': [{
                'id': str(e.id),
                'other_product_id': str(product.id == e.product_a_id and e.product_b_id or e.product_a_id),
                'similarity_score': e.similarity_score,
                'status': e.status
            } for e in edges]
        })

@app.route('/api/clusters', methods=['GET'])
def list_clusters():
    with Session(engine) as session:
        clusters = session.query(Cluster).all()
        return jsonify({
            'clusters': [{
                'id': str(c.id),
                'canonical_product_id': str(c.canonical_product_id),
                'size': c.size,
                'created_at': c.created_at.isoformat() if c.created_at else None
            } for c in clusters]
        })

@app.route('/api/clusters/<cluster_id>', methods=['GET'])
def get_cluster(cluster_id):
    with Session(engine) as session:
        cluster = session.query(Cluster).filter_by(id=cluster_id).first()
        if not cluster:
            return jsonify({'error': 'Cluster not found'}), 404

        canonical = session.query(Product).filter_by(id=cluster.canonical_product_id).first()
        edges = session.query(MatchEdge).filter(
            (MatchEdge.product_a_id.in_([cluster.canonical_product_id])) |
            (MatchEdge.product_b_id.in_([cluster.canonical_product_id]))
        ).all()

        member_ids = set()
        for e in edges:
            member_ids.add(e.product_a_id)
            member_ids.add(e.product_b_id)

        members = session.query(Product).filter(Product.id.in_(member_ids)).all() if member_ids else []

        return jsonify({
            'id': str(cluster.id),
            'canonical_product': {
                'id': str(canonical.id),
                'original_name': canonical.original_name
            } if canonical else None,
            'members': [{
                'id': str(m.id),
                'original_name': m.original_name,
                'supplier_id': m.supplier_id
            } for m in members],
            'size': cluster.size,
            'created_at': cluster.created_at.isoformat() if cluster.created_at else None
        })

@app.route('/api/match-edges', methods=['POST'])
def update_match_edge():
    data = request.json
    edge_id = data.get('edge_id')
    action = data.get('action')

    if not edge_id or action not in ['confirm', 'reject']:
        return jsonify({'error': 'Invalid request'}), 400

    with Session(engine) as session:
        edge = session.query(MatchEdge).filter_by(id=edge_id).first()
        if not edge:
            return jsonify({'error': 'Edge not found'}), 404

        edge.status = 'confirmed' if action == 'confirm' else 'rejected'
        session.commit()

        if action == 'confirm':
            create_clusters(session)

        return jsonify({'success': True, 'status': edge.status})

@app.route('/api/search', methods=['POST'])
def search_products():
    data = request.json
    query_text = data.get('query', '')
    limit = data.get('limit', 10)

    if not query_text:
        return jsonify({'error': 'Query text required'}), 400

    embedding = generate_embedding(query_text)

    with Session(engine) as session:
        result = engine.execute(
            text("SELECT id, original_name, normalized_name, description, supplier_id, 1 - (embedding <=> :query_embedding) AS similarity FROM products ORDER BY embedding <=> :query_embedding LIMIT :limit"),
            {'query_embedding': embedding.tolist(), 'limit': limit}
        )
        rows = result.fetchall()

        return jsonify({
            'results': [{
                'id': str(row[0]),
                'original_name': row[1],
                'normalized_name': row[2],
                'description': row[3],
                'supplier_id': row[4],
                'similarity': float(row[5])
            } for row in rows]
        })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    with Session(engine) as session:
        total_products = session.query(Product).count()
        total_clusters = session.query(Cluster).count()
        pending_matches = session.query(MatchEdge).filter_by(status='pending').count()
        confirmed_matches = session.query(MatchEdge).filter_by(status='confirmed').count()

        return jsonify({
            'total_products': total_products,
            'total_clusters': total_clusters,
            'pending_matches': pending_matches,
            'confirmed_matches': confirmed_matches
        })

@app.route('/api/dedupe', methods=['POST'])
def run_dedupe():
    with Session(engine) as session:
        tfidf_count = len(find_duplicates_tfidf(session))
        embedding_count = match_products_with_embeddings(session)
        return jsonify({
            'success': True,
            'tfidf_duplicates': tfidf_count,
            'embedding_matches': embedding_count
        })

if __name__ == '__main__':
    init_db()
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000)