function ProductList({ products, onConfirmMatch, onRejectMatch }) {
  const getBadgeClass = (score) => {
    if (score >= 0.85) return 'high'
    if (score >= 0.7) return 'review'
    if (score >= 0.5) return 'medium'
    return 'low'
  }

  return (
    <div className="product-list">
      {products.length === 0 ? (
        <div className="loading">No products found</div>
      ) : (
        products.map((product) => (
          <div key={product.id} className="product-item">
            <div className="product-info">
              <h3>{product.original_name}</h3>
              <p>Supplier: {product.supplier_id || 'N/A'} | Category: {product.category || 'N/A'}</p>
              {product.description && product.description !== '[MISSING]' && (
                <p>{product.description.substring(0, 100)}...</p>
              )}
            </div>
            <div>
              {product.similarity !== undefined && (
                <span className={`badge ${getBadgeClass(product.similarity)}`}>
                  {Math.round(product.similarity * 100)}% match
                </span>
              )}
            </div>
          </div>
        ))
      )}
    </div>
  )
}

export default ProductList