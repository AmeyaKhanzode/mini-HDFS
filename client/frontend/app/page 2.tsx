'use client'

import { useState, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Upload, FileIcon, CheckCircle2, XCircle, Cloud } from 'lucide-react'

'use client'

import { useState, useCallback } from 'react'
import { Upload, File, CheckCircle2, XCircle, HardDrive, Database, Zap, Shield } from 'lucide-react'
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

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [result, setResult] = useState<UploadResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
  }

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = (selectedFile: File) => {
    setFile(selectedFile)
    setResult(null)
    setError(null)
    setProgress(0)
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)
    setResult(null)
    setProgress(0)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('file_size', file.size.toString())

    const xhr = new XMLHttpRequest()

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable) {
        const percentComplete = Math.round((e.loaded / e.total) * 100)
        setProgress(percentComplete)
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status === 200) {
        const response: UploadResult = JSON.parse(xhr.responseText)
        setResult(response)
        setFile(null)
      } else {
        setError(`Upload failed: ${xhr.statusText}`)
      }
      setUploading(false)
    })

    xhr.addEventListener('error', () => {
      setError('Network error occurred')
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
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
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
          {!result && (
            <>
              <div
                className={`border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${
                  dragActive
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-slate-300 hover:border-blue-400 hover:bg-slate-50'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                />
                <Upload className="mx-auto h-12 w-12 text-slate-400 mb-4" />
                <p className="text-base font-medium text-slate-700">
                  Click to upload or drag and drop
                </p>
                <p className="text-sm text-slate-500 mt-2">Any file type supported</p>
              </div>

              {file && (
                <div className="bg-slate-50 rounded-xl p-4 space-y-3 border border-slate-200">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-white rounded-lg border border-slate-200">
                      <FileIcon className="h-5 w-5 text-blue-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-900 truncate">{file.name}</p>
                      <p className="text-sm text-slate-500">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                  
                  {uploading && (
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
                  )}
                  
                  {!uploading && (
                    <div className="flex gap-4">
                      <Button onClick={handleUpload} size="lg" className="flex-1 shadow-lg text-lg py-6 hover:scale-105 transition-transform">
                        <Upload className="mr-2 h-5 w-5" />
                        Upload to HDFS
                      </Button>
                      <Button variant="outline" size="lg" onClick={reset} className="shadow-lg py-6 hover:scale-105 transition-transform">
                        Cancel
                      </Button>
                    </div>
                  )}
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
