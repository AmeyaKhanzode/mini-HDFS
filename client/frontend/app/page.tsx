'use client'

import { useState, useCallback, useEffect } from 'react'
import { Upload, File, CheckCircle2, XCircle, HardDrive, Database, Zap, Shield, Download, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'

interface UploadResult {
  filename: string
  file_id: string
  file_size: number
  num_chunks: number
}

interface StoredFile {
  file_hash: string
  file_name: string
  file_size: number
  upload_time: string
  num_chunks: number
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [files, setFiles] = useState<StoredFile[]>([])
  const [loadingFiles, setLoadingFiles] = useState(false)
  const [filesError, setFilesError] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      setFile(selectedFile)
      setError(null)
    }
  }

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFile = e.dataTransfer.files?.[0]
    if (droppedFile) {
      setFile(droppedFile)
      setError(null)
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setProgress(0)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    const xhr = new XMLHttpRequest()

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const percentComplete = Math.round((e.loaded / e.total) * 100)
        setProgress(percentComplete)
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        const response = JSON.parse(xhr.responseText)
        setResult(response)
        setFile(null)
      } else {
        setError(`Upload failed: ${xhr.statusText}`)
      }
      setUploading(false)
    })

    xhr.addEventListener('error', () => {
      setError('Upload failed due to network error')
      setUploading(false)
    })

    xhr.open('POST', '/api/upload')
    xhr.send(formData)
  }

  const reset = () => {
    setFile(null)
    setResult(null)
    setError(null)
    setProgress(0)
  }

  const fetchFiles = async () => {
    setLoadingFiles(true)
    setFilesError(null)
    try {
      const response = await fetch('/api/list_files')
      if (!response.ok) {
        throw new Error('Failed to fetch files')
      }
      const data = await response.json()
      setFiles(data.files || [])
    } catch (err) {
      setFilesError(err instanceof Error ? err.message : 'Failed to load files')
    } finally {
      setLoadingFiles(false)
    }
  }

  const handleDownload = async (fileHash: string, fileName: string) => {
    // TODO: Implement download functionality
    console.log('Download:', fileHash, fileName)
    alert('Download functionality coming soon!')
  }

  useEffect(() => {
    fetchFiles()
  }, [])

  useEffect(() => {
    if (result) {
      // Refresh file list after successful upload
      fetchFiles()
    }
  }, [result])

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Animated background grid */}
      <div className="fixed inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:64px_64px]"></div>
      
      {/* Hero Section */}
      <div className="relative">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <div className="text-center mb-16">
            <h1 className="text-6xl font-bold text-white mb-4 tracking-tight">
              Distributed File System
            </h1>
            <p className="text-xl text-blue-200 max-w-2xl mx-auto">
              Store, replicate, and manage your files across a distributed network with automatic deduplication
            </p>
          </div>

          {/* Feature Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-16">
            <Card className="bg-white/10 backdrop-blur-lg border-white/20 text-white hover:bg-white/15 transition-all duration-300 hover:scale-105">
              <CardContent className="p-6 text-center">
                <HardDrive className="h-12 w-12 mx-auto mb-4 text-blue-400" />
                <h3 className="font-semibold text-lg mb-2">Distributed Storage</h3>
                <p className="text-sm text-blue-200">Files split across multiple nodes</p>
              </CardContent>
            </Card>
            
            <Card className="bg-white/10 backdrop-blur-lg border-white/20 text-white hover:bg-white/15 transition-all duration-300 hover:scale-105">
              <CardContent className="p-6 text-center">
                <Database className="h-12 w-12 mx-auto mb-4 text-emerald-400" />
                <h3 className="font-semibold text-lg mb-2">Auto Replication</h3>
                <p className="text-sm text-blue-200">Fault tolerance built-in</p>
              </CardContent>
            </Card>
            
            <Card className="bg-white/10 backdrop-blur-lg border-white/20 text-white hover:bg-white/15 transition-all duration-300 hover:scale-105">
              <CardContent className="p-6 text-center">
                <Zap className="h-12 w-12 mx-auto mb-4 text-yellow-400" />
                <h3 className="font-semibold text-lg mb-2">Deduplication</h3>
                <p className="text-sm text-blue-200">Save space with smart hashing</p>
              </CardContent>
            </Card>
            
            <Card className="bg-white/10 backdrop-blur-lg border-white/20 text-white hover:bg-white/15 transition-all duration-300 hover:scale-105">
              <CardContent className="p-6 text-center">
                <Shield className="h-12 w-12 mx-auto mb-4 text-purple-400" />
                <h3 className="font-semibold text-lg mb-2">Reliable</h3>
                <p className="text-sm text-blue-200">Metadata persistence layer</p>
              </CardContent>
            </Card>
          </div>

          {/* Upload Card */}
          <Card className="max-w-4xl mx-auto shadow-2xl bg-white/95 backdrop-blur-sm border-white/50">
            <CardHeader className="border-b bg-gradient-to-r from-blue-50 to-slate-50">
              <CardTitle className="text-3xl font-bold text-slate-900">Upload Files</CardTitle>
              <CardDescription className="text-slate-600">Drag and drop or click to select files for upload</CardDescription>
            </CardHeader>
            <CardContent className="p-8 space-y-6">
              {!file && !result && (
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={() => document.getElementById('file-input')?.click()}
                  className={`border-2 border-dashed rounded-xl p-16 text-center cursor-pointer transition-all duration-300 ${
                    isDragging
                      ? 'border-blue-500 bg-gradient-to-br from-blue-50 to-indigo-50 scale-105 shadow-xl'
                      : 'border-slate-300 hover:border-blue-400 hover:bg-gradient-to-br hover:from-slate-50 hover:to-blue-50 hover:shadow-lg'
                  }`}
                >
                  <div className={`transition-transform duration-300 ${isDragging ? 'scale-110' : ''}`}>
                    <Upload className="mx-auto h-20 w-20 text-blue-600 mb-6" />
                    <p className="text-2xl font-semibold text-slate-900 mb-3">
                      Drop your file here or click to browse
                    </p>
                    <p className="text-base text-slate-500">
                      Supports all file types • Automatic chunking and replication
                    </p>
                  </div>
                  <input
                    id="file-input"
                    type="file"
                    className="hidden"
                    onChange={handleFileChange}
                  />
                </div>
              )}

              {file && !result && (
                <>
                  {!uploading && (
                    <div className="bg-gradient-to-br from-slate-50 to-blue-50 border-2 border-blue-200 rounded-xl p-8 space-y-6 shadow-lg">
                      <div className="flex items-center gap-6">
                        <div className="bg-blue-100 p-4 rounded-xl">
                          <File className="h-16 w-16 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-xl text-slate-900 truncate mb-1">{file.name}</p>
                          <p className="text-base text-slate-600">{formatFileSize(file.size)}</p>
                        </div>
                      </div>

                      <div className="flex gap-4">
                        <Button onClick={handleUpload} size="lg" className="flex-1 shadow-lg text-lg py-6 hover:scale-105 transition-transform">
                          <Upload className="mr-2 h-5 w-5" />
                          Upload to HDFS
                        </Button>
                        <Button variant="outline" size="lg" onClick={reset} className="shadow-lg py-6 hover:scale-105 transition-transform">
                          Cancel
                        </Button>
                      </div>
                    </div>
                  )}

                  {uploading && (
                    <div className="space-y-4 bg-gradient-to-br from-slate-50 to-blue-50 border-2 border-blue-200 rounded-xl p-8 shadow-lg">
                      <div className="flex items-center gap-6 mb-6">
                        <div className="bg-blue-100 p-4 rounded-xl">
                          <File className="h-16 w-16 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-xl text-slate-900 truncate mb-1">{file.name}</p>
                          <p className="text-base text-slate-600">{formatFileSize(file.size)}</p>
                        </div>
                      </div>

                      <div className="space-y-4 bg-white/80 p-6 rounded-lg">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-slate-700">Upload Progress</span>
                          <span className="text-2xl font-bold text-blue-600">{progress}%</span>
                        </div>
                        <Progress value={progress} className="h-3" />
                        <p className="text-sm text-center text-slate-600">
                          Uploading to distributed nodes...
                        </p>
                      </div>
                    </div>
                  )}
                </>
              )}

              {result && (
                <div className="space-y-6">
                  <Alert className="border-2 border-emerald-500 bg-gradient-to-br from-emerald-50 to-green-50 shadow-xl">
                    <CheckCircle2 className="h-6 w-6 text-emerald-600" />
                    <AlertTitle className="text-emerald-900 font-bold text-xl">Upload Successful!</AlertTitle>
                    <AlertDescription className="text-emerald-800 space-y-4 mt-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-white/70 p-4 rounded-lg border border-emerald-200 hover:shadow-md transition-shadow">
                          <span className="text-xs font-semibold text-emerald-900 uppercase tracking-wide">Filename</span> 
                          <p className="text-lg text-emerald-700 truncate font-medium mt-1">{result.filename}</p>
                        </div>
                        <div className="bg-white/70 p-4 rounded-lg border border-emerald-200 hover:shadow-md transition-shadow">
                          <span className="text-xs font-semibold text-emerald-900 uppercase tracking-wide">Size</span> 
                          <p className="text-lg text-emerald-700 font-medium mt-1">{formatFileSize(result.file_size)}</p>
                        </div>
                        <div className="bg-white/70 p-4 rounded-lg border border-emerald-200 hover:shadow-md transition-shadow">
                          <span className="text-xs font-semibold text-emerald-900 uppercase tracking-wide">Chunks Created</span> 
                          <p className="text-lg text-emerald-700 font-medium mt-1">{result.num_chunks}</p>
                        </div>
                        <div className="bg-white/70 p-4 rounded-lg border border-emerald-200 hover:shadow-md transition-shadow">
                          <span className="text-xs font-semibold text-emerald-900 uppercase tracking-wide">File ID</span> 
                          <p className="text-sm text-emerald-700 truncate font-mono mt-1">{result.file_id.substring(0, 24)}...</p>
                        </div>
                      </div>
                      <Button onClick={reset} size="lg" className="w-full mt-6 shadow-lg text-lg py-6 hover:scale-105 transition-transform" variant="outline">
                        Upload Another File
                      </Button>
                    </AlertDescription>
                  </Alert>
                </div>
              )}

              {error && (
                <Alert variant="destructive" className="shadow-xl border-2">
                  <XCircle className="h-6 w-6" />
                  <AlertTitle className="font-bold text-xl">Upload Failed</AlertTitle>
                  <AlertDescription className="text-base mt-2">{error}</AlertDescription>
                </Alert>
              )}
            </CardContent>
          </Card>

          {/* Files List Section */}
          <Card className="max-w-4xl mx-auto mt-12 shadow-2xl bg-white/95 backdrop-blur-sm border-white/50">
            <CardHeader className="border-b bg-gradient-to-r from-emerald-50 to-blue-50">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-3xl font-bold text-slate-900">Stored Files</CardTitle>
                  <CardDescription className="text-slate-600">Browse and download your distributed files</CardDescription>
                </div>
                <Button 
                  onClick={fetchFiles} 
                  disabled={loadingFiles}
                  size="lg"
                  variant="outline"
                  className="shadow-lg"
                >
                  <RefreshCw className={`h-5 w-5 mr-2 ${loadingFiles ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-8">
              {filesError && (
                <Alert variant="destructive" className="mb-6">
                  <XCircle className="h-5 w-5" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{filesError}</AlertDescription>
                </Alert>
              )}

              {loadingFiles && (
                <div className="text-center py-12">
                  <RefreshCw className="h-12 w-12 mx-auto text-blue-600 animate-spin mb-4" />
                  <p className="text-slate-600">Loading files...</p>
                </div>
              )}

              {!loadingFiles && files.length === 0 && (
                <div className="text-center py-12">
                  <File className="h-16 w-16 mx-auto text-slate-400 mb-4" />
                  <p className="text-lg text-slate-600 font-medium">No files stored yet</p>
                  <p className="text-sm text-slate-500 mt-2">Upload your first file to get started</p>
                </div>
              )}

              {!loadingFiles && files.length > 0 && (
                <div className="space-y-4">
                  {files.map((file) => (
                    <div
                      key={file.file_hash}
                      className="bg-gradient-to-br from-slate-50 to-blue-50 border-2 border-slate-200 rounded-xl p-6 hover:shadow-lg transition-all duration-300 hover:scale-[1.02]"
                    >
                      <div className="flex items-center gap-6">
                        <div className="bg-blue-100 p-4 rounded-xl">
                          <File className="h-12 w-12 text-blue-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-xl text-slate-900 truncate mb-2">{file.file_name}</h3>
                          <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                            <div>
                              <span className="font-medium">Size:</span> {formatFileSize(file.file_size)}
                            </div>
                            <div>
                              <span className="font-medium">Chunks:</span> {file.num_chunks}
                            </div>
                            <div>
                              <span className="font-medium">Uploaded:</span> {new Date(file.upload_time).toLocaleString()}
                            </div>
                          </div>
                          <div className="mt-2">
                            <span className="text-xs text-slate-500 font-mono">Hash: {file.file_hash.substring(0, 32)}...</span>
                          </div>
                        </div>
                        <Button
                          onClick={() => handleDownload(file.file_hash, file.file_name)}
                          size="lg"
                          className="shadow-lg hover:scale-105 transition-transform"
                        >
                          <Download className="h-5 w-5 mr-2" />
                          Download
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 text-center">
          <p className="text-blue-200 text-sm">
            Built with FastAPI, Next.js, and Docker • Distributed Storage System
          </p>
        </div>
      </div>
    </div>
  )
}
