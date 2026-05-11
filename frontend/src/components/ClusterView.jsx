import { useState, useEffect } from 'react'

function ClusterView({ clusters, selectedCluster, onSelectCluster, onConfirmMatch, onRejectMatch }) {
  const [clusterDetail, setClusterDetail] = useState(null)

  useEffect(() => {
    if (selectedCluster) {
      fetch(`/api/clusters/${selectedCluster}`)
        .then(res => res.json())
        .then(data => setClusterDetail(data))
        .catch(err => console.error('Failed to load cluster:', err))
    }
  }, [selectedCluster])

  if (selectedCluster && clusterDetail) {
    return (
      <div className="cluster-view">
        <button
          className="btn"
          onClick={() => { onSelectCluster(null); setClusterDetail(null); }}
          style={{ marginBottom: '15px' }}
        >
          Back to Clusters
        </button>

        <div className="cluster-card">
          <div className="cluster-header">
            Cluster Size: {clusterDetail.size}
          </div>
          {clusterDetail.canonical_product && (
            <div style={{ marginBottom: '10px' }}>
              <strong>Canonical Product:</strong> {clusterDetail.canonical_product.original_name}
            </div>
          )}
          <div>
            <strong>Members:</strong>
            <ul style={{ marginTop: '10px' }}>
              {clusterDetail.members?.map(m => (
                <li key={m.id} style={{ marginBottom: '5px' }}>
                  {m.original_name} ({m.supplier_id})
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="cluster-view">
      {clusters.length === 0 ? (
        <div className="loading">No clusters found</div>
      ) : (
        clusters.map((cluster) => (
          <div
            key={cluster.id}
            className="cluster-card"
            onClick={() => onSelectCluster(cluster.id)}
            style={{ cursor: 'pointer' }}
          >
            <div className="cluster-header">
              Cluster {cluster.id.substring(0, 8)}...
            </div>
            <p>Size: {cluster.size}</p>
            <p>Created: {cluster.created_at}</p>
          </div>
        ))
      )}
    </div>
  )
}

export default ClusterView