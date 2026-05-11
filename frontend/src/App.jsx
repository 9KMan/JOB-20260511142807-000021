import { useState, useEffect } from 'react'
import { fetchStats, fetchProducts, fetchClusters, fetchCluster, updateMatchEdge, searchProducts, runDedupe, importProducts } from './api'
import ProductList from './components/ProductList'
import ClusterView from './components/ClusterView'
import StatsBar from './components/StatsBar'

function App() {
  const [activeTab, setActiveTab] = useState('products')
  const [stats, setStats] = useState({})
  const [products, setProducts] = useState([])
  const [clusters, setClusters] = useState([])
  const [selectedCluster, setSelectedCluster] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      const data = await fetchStats()
      setStats(data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const loadProducts = async (search = '') => {
    setLoading(true)
    try {
      const data = await fetchProducts(1, search)
      setProducts(data.products || [])
    } catch (err) {
      setError('Failed to load products')
    } finally {
      setLoading(false)
    }
  }

  const loadClusters = async () => {
    setLoading(true)
    try {
      const data = await fetchClusters()
      setClusters(data.clusters || [])
    } catch (err) {
      setError('Failed to load clusters')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      setLoading(true)
      try {
        const data = await searchProducts(searchQuery)
        setProducts(data.results || [])
        setActiveTab('products')
      } catch (err) {
        setError('Search failed')
      } finally {
        setLoading(false)
      }
    }
  }

  const handleDedupe = async () => {
    setLoading(true)
    try {
      await runDedupe()
      await loadStats()
      await loadClusters()
    } catch (err) {
      setError('Deduplication failed')
    } finally {
      setLoading(false)
    }
  }

  const handleImport = async (file, supplierId) => {
    setLoading(true)
    try {
      await importProducts(file, supplierId)
      await loadStats()
      await loadProducts()
    } catch (err) {
      setError('Import failed')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmMatch = async (edgeId) => {
    try {
      await updateMatchEdge(edgeId, 'confirm')
      await loadStats()
      if (selectedCluster) {
        const data = await fetchCluster(selectedCluster)
        setSelectedCluster(data)
      }
    } catch (err) {
      setError('Failed to confirm match')
    }
  }

  const handleRejectMatch = async (edgeId) => {
    try {
      await updateMatchEdge(edgeId, 'reject')
      await loadStats()
    } catch (err) {
      setError('Failed to reject match')
    }
  }

  useEffect(() => {
    if (activeTab === 'products') {
      loadProducts(searchQuery)
    } else if (activeTab === 'clusters') {
      loadClusters()
    }
  }, [activeTab])

  return (
    <div>
      <header>
        <div className="container">
          <h1>Product Matcher MVP</h1>
        </div>
      </header>

      <div className="container">
        {error && <div className="error">{error}</div>}

        <StatsBar stats={stats} />

        <ImportSection onImport={handleImport} />

        <div className="search-section">
          <form onSubmit={handleSearch}>
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </form>
          <button className="btn btn-confirm" onClick={handleDedupe} style={{ marginTop: '10px' }}>
            Run Deduplication
          </button>
        </div>

        <div className="tabs">
          <button
            className={`tab ${activeTab === 'products' ? 'active' : ''}`}
            onClick={() => setActiveTab('products')}
          >
            Products
          </button>
          <button
            className={`tab ${activeTab === 'clusters' ? 'active' : ''}`}
            onClick={() => setActiveTab('clusters')}
          >
            Duplicate Clusters
          </button>
        </div>

        {loading ? (
          <div className="loading">Loading...</div>
        ) : activeTab === 'products' ? (
          <ProductList
            products={products}
            onConfirmMatch={handleConfirmMatch}
            onRejectMatch={handleRejectMatch}
          />
        ) : (
          <ClusterView
            clusters={clusters}
            selectedCluster={selectedCluster}
            onSelectCluster={setSelectedCluster}
            onConfirmMatch={handleConfirmMatch}
            onRejectMatch={handleRejectMatch}
          />
        )}
      </div>
    </div>
  )
}

function ImportSection({ onImport }) {
  const [file, setFile] = useState(null)
  const [supplierId, setSupplierId] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (file && supplierId) {
      onImport(file, supplierId)
    }
  }

  return (
    <div className="import-section">
      <h2>Import Products</h2>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".csv"
          onChange={(e) => setFile(e.target.files[0])}
        />
        <input
          type="text"
          placeholder="Supplier ID"
          value={supplierId}
          onChange={(e) => setSupplierId(e.target.value)}
          style={{ marginLeft: '10px', padding: '8px' }}
        />
        <button type="submit" className="btn btn-confirm" style={{ marginLeft: '10px' }}>
          Import CSV
        </button>
      </form>
    </div>
  )
}

export default App