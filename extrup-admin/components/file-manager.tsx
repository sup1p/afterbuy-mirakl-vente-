"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import { 
  Upload, 
  FileText, 
  Loader2, 
  Eye, 
  Download,
  Trash2,
  RefreshCw,
  FileJson,
  File
} from "lucide-react"
import { apiClient } from "@/lib/api-client"

interface FileInfo {
  filename: string
  path: string
  size: number
  created: number
  modified: number
  error?: string
}

interface FileListResponse {
  files: FileInfo[]
  total: number
  offset: number
  limit: number
  has_more: boolean
  message?: string
}

export function FileManager() {
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  
  // File lists for each category
  const [jsonJvFiles, setJsonJvFiles] = useState<FileInfo[]>([])
  const [jsonXlFiles, setJsonXlFiles] = useState<FileInfo[]>([])
  const [htmlJvFiles, setHtmlJvFiles] = useState<FileInfo[]>([])
  const [htmlXlFiles, setHtmlXlFiles] = useState<FileInfo[]>([])
  
  // Pagination
  const [pagination, setPagination] = useState({
    jsonJv: { offset: 0, limit: 10, total: 0, hasMore: false },
    jsonXl: { offset: 0, limit: 10, total: 0, hasMore: false },
    htmlJv: { offset: 0, limit: 10, total: 0, hasMore: false },
    htmlXl: { offset: 0, limit: 10, total: 0, hasMore: false },
  })

  const [selectedFiles, setSelectedFiles] = useState<{
    jsonJv?: File
    jsonXl?: File
    htmlJv?: File
    htmlXl?: File
  }>({})

  // Load file lists
  const loadFiles = async (category: 'jsonJv' | 'jsonXl' | 'htmlJv' | 'htmlXl', offset = 0) => {
    try {
      setLoading(true)
      
      const endpoints = {
        jsonJv: '/api/list-json-fabric-jv',
        jsonXl: '/api/list-json-fabric-xl',
        htmlJv: '/api/list-html-jv',
        htmlXl: '/api/list-html-xl'
      }
      
      const url = `${endpoints[category]}?offset=${offset}&limit=10`
      const response: FileListResponse = await apiClient.request(url)
      
      switch (category) {
        case 'jsonJv':
          setJsonJvFiles(response.files)
          setPagination(prev => ({ 
            ...prev, 
            jsonJv: { 
              offset: response.offset, 
              limit: response.limit, 
              total: response.total, 
              hasMore: response.has_more 
            } 
          }))
          break
        case 'jsonXl':
          setJsonXlFiles(response.files)
          setPagination(prev => ({ 
            ...prev, 
            jsonXl: { 
              offset: response.offset, 
              limit: response.limit, 
              total: response.total, 
              hasMore: response.has_more 
            } 
          }))
          break
        case 'htmlJv':
          setHtmlJvFiles(response.files)
          setPagination(prev => ({ 
            ...prev, 
            htmlJv: { 
              offset: response.offset, 
              limit: response.limit, 
              total: response.total, 
              hasMore: response.has_more 
            } 
          }))
          break
        case 'htmlXl':
          setHtmlXlFiles(response.files)
          setPagination(prev => ({ 
            ...prev, 
            htmlXl: { 
              offset: response.offset, 
              limit: response.limit, 
              total: response.total, 
              hasMore: response.has_more 
            } 
          }))
          break
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to load files"
      setError(`Failed to load ${category} files: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  // Upload file
  const uploadFile = async (category: 'jsonJv' | 'jsonXl' | 'htmlJv' | 'htmlXl') => {
    const file = selectedFiles[category]
    if (!file) {
      setError("Please select a file first")
      return
    }

    try {
      setUploading(true)
      setError("")
      setSuccess("")

      const endpoints = {
        jsonJv: '/api/upload-json-fabric-jv',
        jsonXl: '/api/upload-json-fabric-xl',
        htmlJv: '/api/upload-html-jv',
        htmlXl: '/api/upload-html-xl'
      }

      const formData = new FormData()
      formData.append('file', file)

      console.log('Uploading file:', file.name, 'Size:', file.size, 'Type:', file.type)
      console.log('FormData entries:', Array.from(formData.entries()))

      const response = await apiClient.request(endpoints[category], {
        method: 'POST',
        body: formData
      })

      setSuccess(`File ${file.name} uploaded successfully to ${category}`)
      setSelectedFiles(prev => ({ ...prev, [category]: undefined }))
      
      // Reload files for this category
      await loadFiles(category)
      
      setTimeout(() => setSuccess(""), 5000)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Failed to upload file"
      setError(`Upload failed: ${errorMessage}`)
    } finally {
      setUploading(false)
    }
  }

  // Load all files on component mount
  useEffect(() => {
    loadFiles('jsonJv')
    loadFiles('jsonXl')
    loadFiles('htmlJv')
    loadFiles('htmlXl')
  }, [])

  // Format file size
  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  // Format date
  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString()
  }

  // File upload section
  const FileUploadSection = ({ 
    category, 
    title, 
    description, 
    acceptedTypes 
  }: { 
    category: 'jsonJv' | 'jsonXl' | 'htmlJv' | 'htmlXl'
    title: string
    description: string
    acceptedTypes: string
  }) => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {category.includes('json') ? <FileJson className="h-5 w-5" /> : <File className="h-5 w-5" />}
          {title}
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label htmlFor={`file-${category}`}>Select File ({acceptedTypes})</Label>
          <Input
            id={`file-${category}`}
            type="file"
            accept={acceptedTypes}
            onChange={(e) => {
              const file = e.target.files?.[0]
              setSelectedFiles(prev => ({ ...prev, [category]: file }))
            }}
          />
        </div>
        
        {selectedFiles[category] && (
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
            <span className="text-sm">
              {selectedFiles[category]?.name} ({formatFileSize(selectedFiles[category]?.size || 0)})
            </span>
            <Button
              onClick={() => uploadFile(category)}
              disabled={uploading}
              size="sm"
            >
              {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              Upload
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )

  // File list section
  const FileListSection = ({ 
    category, 
    files, 
    title 
  }: { 
    category: 'jsonJv' | 'jsonXl' | 'htmlJv' | 'htmlXl'
    files: FileInfo[]
    title: string
  }) => {
    const paginationData = pagination[category]
    
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{title}</CardTitle>
              <CardDescription>
                Total: {paginationData.total} files
              </CardDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadFiles(category)}
              disabled={loading}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {files.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No files found
            </div>
          ) : (
            <div className="space-y-2">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 border rounded-md hover:bg-gray-50"
                >
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{file.filename}</span>
                      {file.error && <Badge variant="destructive">Error</Badge>}
                    </div>
                    <div className="text-sm text-gray-500">
                      Size: {formatFileSize(file.size)} | Modified: {formatDate(file.modified)}
                    </div>
                    {file.error && (
                      <div className="text-sm text-red-500 mt-1">{file.error}</div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
              
              {/* Pagination */}
              <div className="flex items-center justify-between mt-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => loadFiles(category, Math.max(0, paginationData.offset - paginationData.limit))}
                  disabled={paginationData.offset === 0 || loading}
                >
                  Previous
                </Button>
                <span className="text-sm text-gray-500">
                  Showing {paginationData.offset + 1} - {Math.min(paginationData.offset + paginationData.limit, paginationData.total)} of {paginationData.total}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => loadFiles(category, paginationData.offset + paginationData.limit)}
                  disabled={!paginationData.hasMore || loading}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">File Manager</h1>
        <p className="text-gray-600">Upload and manage JSON and HTML files for product import</p>
      </div>

      {/* Success/Error Messages */}
      {success && (
        <Alert className="bg-green-50 text-green-800 border-green-200">
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="upload" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="upload">Upload Files</TabsTrigger>
          <TabsTrigger value="manage">Manage Files</TabsTrigger>
        </TabsList>
        
        <TabsContent value="upload" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <FileUploadSection
              category="jsonJv"
              title="JSON Fabrics JV"
              description="Upload JSON files for JV fabrics"
              acceptedTypes=".json"
            />
            <FileUploadSection
              category="jsonXl"
              title="JSON Fabrics XL"
              description="Upload JSON files for XL fabrics"
              acceptedTypes=".json"
            />
            <FileUploadSection
              category="htmlJv"
              title="HTML JV"
              description="Upload HTML files for JV"
              acceptedTypes=".html"
            />
            <FileUploadSection
              category="htmlXl"
              title="HTML XL"
              description="Upload HTML files for XL"
              acceptedTypes=".html"
            />
          </div>
        </TabsContent>
        
        <TabsContent value="manage" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <FileListSection
              category="jsonJv"
              files={jsonJvFiles}
              title="JSON Fabrics JV Files"
            />
            <FileListSection
              category="jsonXl"
              files={jsonXlFiles}
              title="JSON Fabrics XL Files"
            />
            <FileListSection
              category="htmlJv"
              files={htmlJvFiles}
              title="HTML JV Files"
            />
            <FileListSection
              category="htmlXl"
              files={htmlXlFiles}
              title="HTML XL Files"
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}