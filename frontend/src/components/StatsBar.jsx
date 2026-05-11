function StatsBar({ stats }) {
  return (
    <div className="stats-bar">
      <div className="stat-card">
        <h3>Total Products</h3>
        <div className="value">{stats.total_products || 0}</div>
      </div>
      <div className="stat-card">
        <h3>Clusters</h3>
        <div className="value">{stats.total_clusters || 0}</div>
      </div>
      <div className="stat-card">
        <h3>Pending Matches</h3>
        <div className="value">{stats.pending_matches || 0}</div>
      </div>
      <div className="stat-card">
        <h3>Confirmed Matches</h3>
        <div className="value">{stats.confirmed_matches || 0}</div>
      </div>
    </div>
  )
}

export default StatsBar