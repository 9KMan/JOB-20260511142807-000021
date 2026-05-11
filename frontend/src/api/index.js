import { useState, useEffect } from 'react'

const API_BASE = '/api'

export async function fetchStats() {
  const res = await fetch(`${API_BASE}/stats`)
  return res.json()
}

export async function fetchProducts(page = 1, search = '') {
  const res = await fetch(`${API_BASE}/products?page=${page}&per_page=50&search=${encodeURIComponent(search)}`)
  return res.json()
}

export async function fetchClusters() {
  const res = await fetch(`${API_BASE}/clusters`)
  return res.json()
}

export async function fetchCluster(clusterId) {
  const res = await fetch(`${API_BASE}/clusters/${clusterId}`)
  return res.json()
}

export async function updateMatchEdge(edgeId, action) {
  const res = await fetch(`${API_BASE}/match-edges`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ edge_id: edgeId, action })
  })
  return res.json()
}

export async function searchProducts(query, limit = 10) {
  const res = await fetch(`${API_BASE}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit })
  })
  return res.json()
}

export async function runDedupe() {
  const res = await fetch(`${API_BASE}/dedupe`, { method: 'POST' })
  return res.json()
}

export async function importProducts(file, supplierId) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('supplier_id', supplierId)

  const res = await fetch(`${API_BASE}/import`, {
    method: 'POST',
    body: formData
  })
  return res.json()
}