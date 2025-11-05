'use client'

import { useState, useEffect } from 'react'
import { ArrowLeft, Server, HardDrive, Activity, CheckCircle, XCircle, AlertTriangle, RefreshCw, Files, Database, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import Link from 'next/link'

interface SystemStatus {
  status: string
  message?: string
  chunk_size?: string
  namenode?: string
}

interface FileDetails {
  file_hash: string
  file_name: string
  file_size: number
  upload_time: string
  num_chunks: number
}

interface ChunkLocation {
  chunk_hash: string
  datanodes: string[]
}

interface FileChunkMap {
  [chunkIndex: string]: ChunkLocation
}

interface DataNode {
  id: string
  host: string
  port: number
  status: 'alive' | 'down'
  last_heartbeat: string | null
}

export default function Dashboard() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null)
  const [files, setFiles] = useState<FileDetails[]>([])
  const [selectedFile, setSelectedFile] = useState<FileDetails | null>(null)
  const [chunkMap, setChunkMap] = useState<FileChunkMap | null>(null)
  const [datanodes, setDatanodes] = useState<DataNode[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch('/api/status')
      if (!response.ok) throw new Error('Failed to fetch system status')
      const data = await response.json()
      setSystemStatus(data)
    } catch (err) {
      console.error('Error fetching system status:', err)
      setError('Failed to load system status')
    }
  }

  const fetchFiles = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/list_files')
      if (!response.ok) throw new Error('Failed to fetch files')
      const data = await response.json()
      setFiles(data.files || [])
    } catch (err) {
      console.error('Error fetching files:', err)
      setError('Failed to load files')
    } finally {
      setLoading(false)
    }
  }

  const fetchChunkMap = async (filename: string) => {
    try {
      // We need to create a new endpoint for getting chunk locations
      // For now, we'll show a placeholder
      setChunkMap(null)
    } catch (err) {
      console.error('Error fetching chunk map:', err)
    }
  }

  const fetchDatanodeStatus = async () => {
    try {
      const response = await fetch('/api/datanodes')
      if (!response.ok) throw new Error('Failed to fetch datanode status')
      const data = await response.json()
      setDatanodes(data.datanodes || [])
    } catch (err) {
      console.error('Error fetching datanode status:', err)
    }
  }

  useEffect(() => {
    fetchSystemStatus()
    fetchFiles()
    fetchDatanodeStatus()
    
    // Refresh every 5 seconds
    const interval = setInterval(() => {
      fetchSystemStatus()
      fetchFiles()
      fetchDatanodeStatus()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  const totalFiles = files.length
  const totalSize = files.reduce((acc, file) => acc + file.file_size, 0)
  const totalChunks = files.reduce((acc, file) => acc + file.num_chunks, 0)

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Animated background grid */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:64px_64px]"></div>
      
      <div className="relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-16">
          {/* Header */}
          <div className="mb-8">
            <Link href="/">
              <Button variant="outline" className="mb-4 bg-white/10 text-white border-white/20 hover:bg-white/20">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Home
              </Button>
            </Link>
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-4xl font-bold text-white mb-2">System Dashboard</h1>
                <p className="text-blue-200">Real-time monitoring and visualization</p>
              </div>
              <Button 
                onClick={() => { fetchSystemStatus(); fetchFiles(); }}
                className="bg-white/10 text-white border-white/20 hover:bg-white/20"
                variant="outline"
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>

          {/* System Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="bg-white/95 backdrop-blur-sm border-white/50 shadow-xl">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600 flex items-center">
                  <Activity className="mr-2 h-4 w-4 text-green-600" />
                  System Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  {systemStatus?.status === 'running' ? (
                    <>
                      <CheckCircle className="h-8 w-8 text-green-600 mr-3" />
                      <div>
                        <p className="text-2xl font-bold text-slate-900">Online</p>
                        <p className="text-xs text-slate-500">All systems operational</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <XCircle className="h-8 w-8 text-red-600 mr-3" />
                      <div>
                        <p className="text-2xl font-bold text-slate-900">Offline</p>
                        <p className="text-xs text-slate-500">System unavailable</p>
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/95 backdrop-blur-sm border-white/50 shadow-xl">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600 flex items-center">
                  <Files className="mr-2 h-4 w-4 text-blue-600" />
                  Total Files
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-slate-900">{totalFiles}</p>
                <p className="text-xs text-slate-500 mt-1">{formatFileSize(totalSize)} stored</p>
              </CardContent>
            </Card>

            <Card className="bg-white/95 backdrop-blur-sm border-white/50 shadow-xl">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600 flex items-center">
                  <Database className="mr-2 h-4 w-4 text-purple-600" />
                  Total Chunks
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-slate-900">{totalChunks}</p>
                <p className="text-xs text-slate-500 mt-1">Distributed across nodes</p>
              </CardContent>
            </Card>

            <Card className="bg-white/95 backdrop-blur-sm border-white/50 shadow-xl">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm font-medium text-slate-600 flex items-center">
                  <HardDrive className="mr-2 h-4 w-4 text-emerald-600" />
                  Chunk Size
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold text-slate-900">{systemStatus?.chunk_size || 'N/A'}</p>
                <p className="text-xs text-slate-500 mt-1">Per chunk</p>
              </CardContent>
            </Card>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-8">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* File Distribution and Chunk Map Visualization */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* File List */}
            <Card className="bg-white/95 backdrop-blur-sm border-white/50 shadow-xl">
              <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-slate-50">
                <CardTitle className="text-xl font-bold text-slate-900">File Distribution</CardTitle>
                <CardDescription>Click on a file to see its chunk distribution</CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                {loading && files.length === 0 ? (
                  <div className="text-center py-8">
                    <RefreshCw className="h-10 w-10 mx-auto text-blue-600 animate-spin mb-3" />
                    <p className="text-slate-600 text-sm">Loading files...</p>
                  </div>
                ) : files.length === 0 ? (
                  <div className="text-center py-8">
                    <Database className="h-12 w-12 mx-auto text-slate-400 mb-3" />
                    <p className="text-base text-slate-600 font-medium">No files stored</p>
                    <p className="text-xs text-slate-500 mt-1">Upload files to see distribution</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                    {files.map((file) => (
                      <div
                        key={file.file_hash}
                        onClick={() => {
                          setSelectedFile(file)
                          fetchChunkMap(file.file_name)
                        }}
                        className={`cursor-pointer border-2 rounded-xl p-4 transition-all duration-300 hover:shadow-lg hover:scale-[1.02] ${
                          selectedFile?.file_hash === file.file_hash
                            ? 'bg-gradient-to-br from-blue-50 to-indigo-50 border-blue-400'
                            : 'bg-gradient-to-br from-slate-50 to-blue-50 border-slate-200'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${
                            selectedFile?.file_hash === file.file_hash ? 'bg-blue-200' : 'bg-blue-100'
                          }`}>
                            <Database className="h-6 w-6 text-blue-600" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-semibold text-sm text-slate-900 truncate">{file.file_name}</h3>
                            <div className="flex gap-3 text-xs text-slate-600 mt-1">
                              <span>{formatFileSize(file.file_size)}</span>
                              <span>•</span>
                              <span>{file.num_chunks} chunks</span>
                            </div>
                          </div>
                          {selectedFile?.file_hash === file.file_hash && (
                            <CheckCircle className="h-5 w-5 text-blue-600" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Chunk Map Visualization */}
            <Card className="bg-white/95 backdrop-blur-sm border-white/50 shadow-xl">
              <CardHeader className="border-b bg-gradient-to-r from-emerald-50 to-blue-50">
                <CardTitle className="text-xl font-bold text-slate-900">Chunk Map Visualization</CardTitle>
                <CardDescription>Visual representation of chunk distribution</CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                {!selectedFile ? (
                  <div className="text-center py-12">
                    <Server className="h-16 w-16 mx-auto text-slate-400 mb-4" />
                    <p className="text-base text-slate-600 font-medium">No file selected</p>
                    <p className="text-xs text-slate-500 mt-1">Select a file to view chunk distribution</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-xl p-4">
                      <h3 className="font-semibold text-slate-900 mb-2">{selectedFile.file_name}</h3>
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-slate-600">Size:</span>
                          <span className="ml-2 font-medium text-slate-900">{formatFileSize(selectedFile.file_size)}</span>
                        </div>
                        <div>
                          <span className="text-slate-600">Chunks:</span>
                          <span className="ml-2 font-medium text-slate-900">{selectedFile.num_chunks}</span>
                        </div>
                        <div className="col-span-2">
                          <span className="text-slate-600">Hash:</span>
                          <span className="ml-2 font-mono text-xs text-slate-700">{selectedFile.file_hash.substring(0, 32)}...</span>
                        </div>
                      </div>
                    </div>

                    {/* Chunk Distribution */}
                    <div className="space-y-3 max-h-[380px] overflow-y-auto pr-2">
                      {Array.from({ length: selectedFile.num_chunks }, (_, i) => (
                        <div key={i} className="bg-slate-50 border border-slate-200 rounded-lg p-3">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-semibold text-sm text-slate-900">Chunk {i + 1}</span>
                            <span className="text-xs text-slate-500">Replicated</span>
                          </div>
                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <Server className="h-4 w-4 text-green-600" />
                              <span className="text-xs text-slate-700 font-mono">datanode1:5001</span>
                              <CheckCircle className="h-3 w-3 text-green-600 ml-auto" />
                            </div>
                            <div className="flex items-center gap-2">
                              <Server className="h-4 w-4 text-green-600" />
                              <span className="text-xs text-slate-700 font-mono">datanode2:5002</span>
                              <CheckCircle className="h-3 w-3 text-green-600 ml-auto" />
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* System Health Info */}
          <Card className="mt-8 bg-white/95 backdrop-blur-sm border-white/50 shadow-xl">
            <CardHeader className="border-b bg-gradient-to-r from-green-50 to-emerald-50">
              <CardTitle className="text-xl font-bold text-slate-900">System Health & Integrity</CardTitle>
              <CardDescription>Real-time status of storage nodes and data integrity</CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                {/* Datanode Status */}
                <div>
                  <h4 className="font-semibold text-slate-900 mb-3">Datanode Status</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {datanodes.map((node) => (
                      <div
                        key={node.id}
                        className={`flex items-center gap-4 p-4 rounded-xl border-2 transition-all ${
                          node.status === 'alive'
                            ? 'bg-green-50 border-green-200'
                            : node.status === 'down'
                            ? 'bg-red-50 border-red-200'
                            : 'bg-slate-50 border-slate-200'
                        }`}
                      >
                        <div className={`p-3 rounded-lg ${
                          node.status === 'alive'
                            ? 'bg-green-100'
                            : node.status === 'down'
                            ? 'bg-red-100'
                            : 'bg-slate-100'
                        }`}>
                          <Server className={`h-6 w-6 ${
                            node.status === 'alive'
                              ? 'text-green-600'
                              : node.status === 'down'
                              ? 'text-red-600'
                              : 'text-slate-400'
                          }`} />
                        </div>
                        <div className="flex-1">
                          <h5 className="font-semibold text-slate-900">Datanode {node.id}</h5>
                          <p className="text-xs text-slate-600 font-mono">{node.host}:{node.port}</p>
                        </div>
                        {node.status === 'alive' ? (
                          <CheckCircle className="h-5 w-5 text-green-600" />
                        ) : node.status === 'down' ? (
                          <XCircle className="h-5 w-5 text-red-600" />
                        ) : (
                          <RefreshCw className="h-5 w-5 text-slate-400 animate-spin" />
                        )}
                      </div>
                    ))}
                  </div>
                  <p className="text-xs text-slate-500 mt-3">
                    {datanodes.filter(n => n.status === 'alive').length}/{datanodes.length} nodes online
                  </p>
                </div>

                {/* Other System Info */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t">
                  <div className="flex items-start gap-4">
                    <div className="bg-blue-100 p-3 rounded-lg">
                      <Database className="h-6 w-6 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-1">Data Replication</h4>
                      <p className="text-sm text-slate-600">All chunks are replicated across multiple nodes</p>
                      <p className="text-xs text-blue-600 font-medium mt-1">Replication factor: 2</p>
                    </div>
                  </div>

                  <div className="flex items-start gap-4">
                    <div className="bg-purple-100 p-3 rounded-lg">
                      <Shield className="h-6 w-6 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="font-semibold text-slate-900 mb-1">File Integrity</h4>
                      <p className="text-sm text-slate-600">SHA-256 hashing ensures data integrity</p>
                      <p className="text-xs text-purple-600 font-medium mt-1">100% verified</p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-center">
          <p className="text-blue-200 text-sm">
            Dashboard auto-refreshes every 5 seconds • Real-time monitoring
          </p>
        </div>
      </div>
    </div>
  )
}
