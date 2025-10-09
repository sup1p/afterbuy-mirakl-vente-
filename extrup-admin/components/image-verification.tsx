"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { CheckCircle, XCircle, ChevronLeft, ChevronRight, ImageIcon, Package, AlertCircle, Loader2, Search } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import type { UploadedEAN, UploadedFabric } from "@/lib/types"
import Image from "next/image"

export function ImageVerification() {
  const [fabrics, setFabrics] = useState<UploadedFabric[]>([])
  const [searchFabricId, setSearchFabricId] = useState("")
  const [foundFabrics, setFoundFabrics] = useState<UploadedFabric[]>([])
  const [searchingFabric, setSearchingFabric] = useState(false)
  const [selectedFabricId, setSelectedFabricId] = useState("")
  const [selectedFabric, setSelectedFabric] = useState<UploadedFabric | null>(null)
  const [products, setProducts] = useState<UploadedEAN[]>([])
  const [currentIndex, setCurrentIndex] = useState(0)
  const [loading, setLoading] = useState(true)
  const [loadingFabrics, setLoadingFabrics] = useState(true)
  const [loadingProducts, setLoadingProducts] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [verifying, setVerifying] = useState(false)
  const [loadingNext, setLoadingNext] = useState(false)
  const [pendingProducts, setPendingProducts] = useState<UploadedEAN[]>([])
  const [errorProducts, setErrorProducts] = useState<UploadedEAN[]>([])
  const [processedProducts, setProcessedProducts] = useState<UploadedEAN[]>([])
  const [activeTab, setActiveTab] = useState<"pending" | "error" | "processed">("pending")
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [currentFabricPage, setCurrentFabricPage] = useState(1)
  const [totalFabricPages, setTotalFabricPages] = useState(1)
  const [allFabrics, setAllFabrics] = useState<UploadedFabric[]>([])
  const [loadingAllFabrics, setLoadingAllFabrics] = useState(false)

  // Image modal state
  const [imageModalOpen, setImageModalOpen] = useState(false)
  const [selectedImageUrl, setSelectedImageUrl] = useState<string>("")

  useEffect(() => {
    loadAllFabrics()
  }, [])

  useEffect(() => {
    if (selectedFabricId) {
      loadAllProducts()
      setCurrentIndex(0) // Reset to first product when fabric changes
    }
  }, [selectedFabricId])

  const loadAllFabrics = async (page: number = 1) => {
    try {
      setLoadingAllFabrics(true)
      setError("")
      const limit = 20 // Show 20 fabrics per page
      const offset = (page - 1) * limit
      
      // For now, load all fabrics and implement client-side pagination
      // In future, this could be server-side pagination
      const allFabricsData = await apiClient.request<UploadedFabric[]>("/uploaded-fabrics")
      
      // Calculate pagination
      const totalFabrics = allFabricsData.length
      const totalPages = Math.ceil(totalFabrics / limit)
      const startIndex = (page - 1) * limit
      const endIndex = startIndex + limit
      const paginatedFabrics = allFabricsData.slice(startIndex, endIndex)
      
      setAllFabrics(paginatedFabrics)
      setTotalFabricPages(totalPages)
      setCurrentFabricPage(page)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load fabrics")
    } finally {
      setLoadingAllFabrics(false)
    }
  }

  const searchFabric = async () => {
    if (!searchFabricId.trim()) {
      setError("Please enter a fabric ID")
      return
    }

    try {
      setSearchingFabric(true)
      setError("")
      setFoundFabrics([])
      
      // Search for fabric by ID using the main endpoint with potential query parameters
      // Since we don't know the exact API, we'll try the main endpoint first
      const allFabrics = await apiClient.request<UploadedFabric[]>("/uploaded-fabrics")
      const foundFabrics = allFabrics.filter(fabric => 
        fabric.afterbuy_fabric_id && 
        String(fabric.afterbuy_fabric_id).toLowerCase().includes(searchFabricId.trim().toLowerCase())
      )
      
      if (foundFabrics.length > 0) {
        setFoundFabrics(foundFabrics)
        setSuccess(`Found ${foundFabrics.length} fabric${foundFabrics.length > 1 ? 's' : ''} matching "${searchFabricId}"`)
      } else {
        setFoundFabrics([])
        setError("No fabrics found")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to search fabric")
    } finally {
      setSearchingFabric(false)
    }
  }

  const selectFabric = (fabric: UploadedFabric) => {
    setSelectedFabricId(fabric.afterbuy_fabric_id)
    setSelectedFabric(fabric)
    setFoundFabrics([])
    setSearchFabricId("")
    setSuccess("")
  }

  const loadAllProducts = async (page: number = 1) => {
    if (!selectedFabricId || !selectedFabric) return

    try {
      setLoadingProducts(true)
      setError("")
      const limit = 50 // Load more products per page for better UX
      const offset = (page - 1) * limit
      const data = await apiClient.request<UploadedEAN[]>(`/uploaded-fabrics/${selectedFabric.shop}/${selectedFabricId}/eans?limit=${limit}&offset=${offset}`)
      
      const pending = data.filter((p) => p.status === "pending")
      const error = data.filter((p) => p.status === "error")
      const processed = data.filter((p) => p.status === "processed")
      
      setProducts(pending)
      setPendingProducts(pending)
      setErrorProducts(error)
      setProcessedProducts(processed)
      setCurrentIndex(0)
      setCurrentPage(page)
      // For now, assume we load all at once. In future, we could implement proper pagination
      setTotalPages(1)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load products")
    } finally {
      setLoadingProducts(false)
    }
  }

  const handleVerification = async (isCorrect: boolean) => {
    const currentProduct = products[currentIndex]
    if (!currentProduct) return

    try {
      setVerifying(true)
      setError("")

      await apiClient.request("/uploaded-fabrics/update-ean-status", {
        method: "PATCH",
        body: JSON.stringify({
          id: currentProduct.id,
          new_status: isCorrect ? "processed" : "error",
        }),
      })

      // Immediately update local state
      const newStatus = isCorrect ? "processed" as const : "error" as const
      const updatedProduct = { ...currentProduct, status: newStatus }
      
      // Show loading before switching to next product
      setLoadingNext(true)
      
      // Remove from pending products and update arrays
      setProducts(prev => {
        const newProducts = prev.filter(p => p.id !== currentProduct.id)
        return newProducts
      })
      
      // Adjust currentIndex after product removal
      setTimeout(() => {
        setProducts(currentProducts => {
          setCurrentIndex(currentIdx => {
            // If we removed the last product in the array, move to previous
            if (currentIdx >= currentProducts.length && currentProducts.length > 0) {
              return currentProducts.length - 1
            }
            // Otherwise stay at the same index (which now shows the next product)
            // or 0 if no products left
            return currentProducts.length > 0 ? Math.min(currentIdx, currentProducts.length - 1) : 0
          })
          setLoadingNext(false)
          return currentProducts
        })
      }, 100) // Small delay to show loading state
      setPendingProducts(prev => prev.filter(p => p.id !== currentProduct.id))
      
      // Add to appropriate array
      if (isCorrect) {
        setProcessedProducts(prev => [...prev, updatedProduct])
      } else {
        setErrorProducts(prev => [...prev, updatedProduct])
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update verification status")
    } finally {
      setVerifying(false)
    }
  }

  const handleStatusChange = async (product: UploadedEAN, newStatus: "processed" | "error" | "pending") => {
    try {
      setError("")
      
      await apiClient.request("/uploaded-fabrics/update-ean-status", {
        method: "PATCH",
        body: JSON.stringify({
          id: product.id,
          new_status: newStatus,
        }),
      })

      const updatedProduct = { ...product, status: newStatus }

      // Remove from current arrays
      setErrorProducts(prev => prev.filter(p => p.id !== product.id))
      setProcessedProducts(prev => prev.filter(p => p.id !== product.id))
      setPendingProducts(prev => prev.filter(p => p.id !== product.id))

      // Add to appropriate array
      if (newStatus === "processed") {
        setProcessedProducts(prev => [...prev, updatedProduct])
      } else if (newStatus === "error") {
        setErrorProducts(prev => [...prev, updatedProduct])
      } else if (newStatus === "pending") {
        setPendingProducts(prev => [...prev, updatedProduct])
        setProducts(prev => [...prev, updatedProduct])
      }

      setSuccess(`Product status changed to ${newStatus}`)
      setTimeout(() => setSuccess(""), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update product status")
    }
  }

  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
    }
  }

  const handleNext = () => {
    if (currentIndex < products.length - 1) {
      setCurrentIndex(currentIndex + 1)
    }
  }

  const handleImageClick = (imageUrl: string) => {
    setSelectedImageUrl(imageUrl)
    setImageModalOpen(true)
  }

  const currentProduct = products[currentIndex]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Image Verification</h1>
        <p className="text-gray-600">Verify product images for accuracy</p>
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

      {/* Fabric Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Search Fabric</CardTitle>
          <CardDescription>Enter a fabric ID to verify its product images</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              placeholder="Enter fabric ID..."
              value={searchFabricId}
              onChange={(e) => setSearchFabricId(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && searchFabric()}
              className="flex-1"
            />
            <Button 
              onClick={searchFabric} 
              disabled={searchingFabric || !searchFabricId.trim()}
              variant="outline"
            >
              {searchingFabric ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Search className="h-4 w-4" />
              )}
            </Button>
          </div>
          
          {foundFabrics.length > 0 && (
            <div className="bg-green-50 border border-green-200 rounded-lg">
              <div className="p-3 border-b border-green-200">
                <p className="font-medium text-green-800">
                  Found {foundFabrics.length} fabric{foundFabrics.length > 1 ? 's' : ''}:
                </p>
              </div>
              <div className="max-h-64 overflow-y-auto">
                {foundFabrics.map((fabric, index) => (
                  <div 
                    key={fabric.id}
                    className={`p-4 flex items-center justify-between hover:bg-green-100 ${
                      index !== foundFabrics.length - 1 ? 'border-b border-green-200' : ''
                    }`}
                  >
                    <div>
                      <p className="font-medium text-green-800">{fabric.afterbuy_fabric_id}</p>
                      <p className="text-sm text-green-600">Shop: {fabric.shop}</p>
                      <p className="text-sm text-green-600">Status: {fabric.status}</p>
                    </div>
                    <Button 
                      onClick={() => selectFabric(fabric)}
                      size="sm"
                      className="bg-green-600 hover:bg-green-700"
                    >
                      Select
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* All Fabrics List */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg">
            <div className="p-3 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <p className="font-medium text-gray-800">All Fabrics</p>
                <div className="flex items-center gap-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => loadAllFabrics(currentFabricPage - 1)}
                    disabled={currentFabricPage === 1 || loadingAllFabrics}
                  >
                    Previous
                  </Button>
                  <span className="text-sm text-gray-600">
                    {currentFabricPage} of {totalFabricPages}
                  </span>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => loadAllFabrics(currentFabricPage + 1)}
                    disabled={currentFabricPage === totalFabricPages || loadingAllFabrics}
                  >
                    Next
                  </Button>
                </div>
              </div>
            </div>
            <div className="max-h-96 overflow-y-auto">
              {loadingAllFabrics ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  Loading fabrics...
                </div>
              ) : allFabrics.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No fabrics found</div>
              ) : (
                <div className="divide-y divide-gray-200">
                  {allFabrics.map((fabric) => (
                    <div 
                      key={fabric.id}
                      className="p-4 flex items-center justify-between hover:bg-gray-100 transition-colors"
                    >
                      <div>
                        <p className="font-medium text-gray-800">{fabric.afterbuy_fabric_id}</p>
                        <p className="text-sm text-gray-600">Shop: {fabric.shop}</p>
                        <p className="text-sm text-gray-600">Status: {fabric.status}</p>
                        <p className="text-xs text-gray-500">
                          Created: {new Date(fabric.date_time).toLocaleDateString()}
                        </p>
                      </div>
                      <Button 
                        onClick={() => selectFabric(fabric)}
                        size="sm"
                        variant="outline"
                        disabled={selectedFabricId === fabric.afterbuy_fabric_id}
                      >
                        {selectedFabricId === fabric.afterbuy_fabric_id ? 'Selected' : 'Select'}
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          
          {selectedFabricId && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                <strong>Selected Fabric:</strong> {selectedFabricId}
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={() => {
                    setSelectedFabricId("")
                    setSelectedFabric(null)
                    setFoundFabrics([])
                    setProducts([])
                    setPendingProducts([])
                    setErrorProducts([])
                    setProcessedProducts([])
                  }}
                  className="ml-2 h-6 px-2 text-blue-600 hover:text-blue-800"
                >
                  Change
                </Button>
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Show tabs only when fabric is selected */}
      {selectedFabricId && (
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "pending" | "error" | "processed")}>
          <TabsList>
            <TabsTrigger value="pending">
              Pending
              {pendingProducts.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {pendingProducts.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="error">
              Error
              {errorProducts.length > 0 && (
                <Badge variant="destructive" className="ml-2">
                  {errorProducts.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="processed">
              Processed
              {processedProducts.length > 0 && (
                <Badge variant="default" className="ml-2">
                  {processedProducts.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

        {/* Pending Tab */}
        <TabsContent value="pending" className="space-y-6">
          {loadingProducts ? (
            <Card>
              <CardContent className="p-12">
                <div className="text-center text-gray-500">Loading products...</div>
              </CardContent>
            </Card>
          ) : products.length === 0 ? (
            <Card>
              <CardContent className="p-12">
                <div className="text-center space-y-4">
                  <CheckCircle className="h-16 w-16 text-green-600 mx-auto" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">All products verified!</h3>
                    <p className="text-gray-600">There are no more products to verify at this time.</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* Progress */}
              <Card>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-gray-600">
                      Left {products.length} products
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm" onClick={handlePrevious} disabled={currentIndex === 0}>
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleNext}
                        disabled={currentIndex === products.length - 1}
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                  <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${((currentIndex + 1) / products.length) * 100}%` }}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Product Card */}
              {loadingNext ? (
                <Card>
                  <CardContent className="p-12">
                    <div className="flex flex-col items-center justify-center space-y-4">
                      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
                      <p className="text-muted-foreground">Loading next product...</p>
                    </div>
                  </CardContent>
                </Card>
              ) : currentProduct ? (
                <Card>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <CardTitle className="text-xl">{currentProduct.title || "Unnamed Product"}</CardTitle>
                        <p className="text-sm text-gray-600">EAN: {currentProduct.ean}</p>
                      </div>
                      <Badge variant="outline" className="text-blue-600 border-blue-200">
                        <Package className="mr-1 h-3 w-3" />
                        Fabric #{currentProduct.fabric_id}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Images Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {[currentProduct.image_1, currentProduct.image_2, currentProduct.image_3].map((image, idx) => (
                        <div key={idx} className="space-y-2">
                          <div className="text-sm font-medium text-gray-700">Image {idx + 1}</div>
                          <div className="relative aspect-square bg-gray-100 rounded-lg overflow-hidden border-2 border-gray-200 cursor-pointer hover:border-blue-400 transition-colors">
                            {image ? (
                              <Image
                                src={image || "/placeholder.svg"}
                                alt={`${currentProduct.title || "Product"} - Image ${idx + 1}`}
                                fill
                                className="object-cover"
                                unoptimized
                                onClick={() => handleImageClick(image)}
                              />
                            ) : (
                              <div className="absolute inset-0 flex items-center justify-center">
                                <div className="text-center text-gray-400">
                                  <ImageIcon className="h-12 w-12 mx-auto mb-2" />
                                  <p className="text-sm">No image</p>
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* Verification Buttons */}
                    <div className="flex flex-col sm:flex-row gap-4 pt-4">
                      <Button
                        onClick={() => handleVerification(false)}
                        disabled={verifying}
                        variant="destructive"
                        size="lg"
                        className="flex-1 h-16 text-lg"
                      >
                        <XCircle className="mr-2 h-6 w-6" />
                        Incorrect
                      </Button>
                      <Button
                        onClick={() => handleVerification(true)}
                        disabled={verifying}
                        size="lg"
                        className="flex-1 h-16 text-lg bg-green-600 hover:bg-green-700"
                      >
                        <CheckCircle className="mr-2 h-6 w-6" />
                        Correct
                      </Button>
                    </div>

                    <div className="text-center text-sm text-gray-500">
                      Review the images and mark whether they correctly represent the product
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent className="p-12">
                    <div className="text-center space-y-4">
                      <CheckCircle className="h-16 w-16 text-green-600 mx-auto" />
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">All products verified!</h3>
                        <p className="text-gray-600">There are no more products to verify at this time.</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        {/* Error Products Tab */}
        <TabsContent value="error" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Error Products</CardTitle>
              <CardDescription>Products marked as having incorrect images</CardDescription>
            </CardHeader>
            <CardContent>
              {errorProducts.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No error products found</div>
              ) : (
                <div className="space-y-4">
                  {errorProducts.map((product) => (
                    <Card key={product.id} className="border-red-200">
                      <CardContent className="p-4">
                        <div className="flex flex-col md:flex-row gap-4">
                          {/* Product Info */}
                          <div className="flex-1 space-y-2">
                            <div className="flex items-start justify-between">
                              <div>
                                <h3 className="font-semibold text-lg">{product.title || "Unnamed Product"}</h3>
                                <p className="text-sm text-gray-600">EAN: {product.ean}</p>
                              </div>
                              <Badge variant="destructive">
                                <AlertCircle className="mr-1 h-3 w-3" />
                                Error
                              </Badge>
                            </div>
                            {/* Action Buttons */}
                            <div className="flex gap-2 mt-3">
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-green-600 border-green-200 hover:bg-green-50"
                                onClick={() => handleStatusChange(product, "processed")}
                              >
                                <CheckCircle className="mr-1 h-3 w-3" />
                                Mark as Correct
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-blue-600 border-blue-200 hover:bg-blue-50"
                                onClick={() => handleStatusChange(product, "pending")}
                              >
                                Return to Pending
                              </Button>
                            </div>
                          </div>

                          {/* Image Thumbnails */}
                          <div className="flex gap-2">
                            {[product.image_1, product.image_2, product.image_3].map((image, idx) => (
                              <div
                                key={idx}
                                className="relative w-20 h-20 bg-gray-100 rounded border overflow-hidden flex-shrink-0 cursor-pointer hover:border-blue-400 transition-colors"
                              >
                                {image ? (
                                  <Image
                                    src={image || "/placeholder.svg"}
                                    alt={`Image ${idx + 1}`}
                                    fill
                                    className="object-cover"
                                    unoptimized
                                    onClick={() => handleImageClick(image)}
                                  />
                                ) : (
                                  <div className="absolute inset-0 flex items-center justify-center">
                                    <ImageIcon className="h-6 w-6 text-gray-400" />
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Processed Products Tab */}
        <TabsContent value="processed" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Processed Products</CardTitle>
              <CardDescription>Products marked as having correct images</CardDescription>
            </CardHeader>
            <CardContent>
              {processedProducts.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No processed products found</div>
              ) : (
                <div className="space-y-4">
                  {processedProducts.map((product) => (
                    <Card key={product.id} className="border-green-200">
                      <CardContent className="p-4">
                        <div className="flex flex-col md:flex-row gap-4">
                          {/* Product Info */}
                          <div className="flex-1 space-y-2">
                            <div className="flex items-start justify-between">
                              <div>
                                <h3 className="font-semibold text-lg">{product.title || "Unnamed Product"}</h3>
                                <p className="text-sm text-gray-600">EAN: {product.ean}</p>
                              </div>
                              <Badge className="bg-green-100 text-green-800">
                                <CheckCircle className="mr-1 h-3 w-3" />
                                Processed
                              </Badge>
                            </div>
                            {/* Action Buttons */}
                            <div className="flex gap-2 mt-3">
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-red-600 border-red-200 hover:bg-red-50"
                                onClick={() => handleStatusChange(product, "error")}
                              >
                                <XCircle className="mr-1 h-3 w-3" />
                                Mark as Error
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="text-blue-600 border-blue-200 hover:bg-blue-50"
                                onClick={() => handleStatusChange(product, "pending")}
                              >
                                Return to Pending
                              </Button>
                            </div>
                          </div>

                          {/* Image Thumbnails */}
                          <div className="flex gap-2">
                            {[product.image_1, product.image_2, product.image_3].map((image, idx) => (
                              <div
                                key={idx}
                                className="relative w-20 h-20 bg-gray-100 rounded border overflow-hidden flex-shrink-0 cursor-pointer hover:border-blue-400 transition-colors"
                              >
                                {image ? (
                                  <Image
                                    src={image || "/placeholder.svg"}
                                    alt={`Image ${idx + 1}`}
                                    fill
                                    className="object-cover"
                                    unoptimized
                                    onClick={() => handleImageClick(image)}
                                  />
                                ) : (
                                  <div className="absolute inset-0 flex items-center justify-center">
                                    <ImageIcon className="h-6 w-6 text-gray-400" />
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        </Tabs>
      )}

      {/* Image Modal */}
      <Dialog open={imageModalOpen} onOpenChange={setImageModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] p-0">
          <DialogHeader className="p-6 pb-0">
            <DialogTitle>Product Image</DialogTitle>
          </DialogHeader>
          <div className="p-6 pt-0">
            {selectedImageUrl && (
              <div className="relative w-full h-[70vh] bg-gray-100 rounded-lg overflow-hidden">
                <Image
                  src={selectedImageUrl}
                  alt="Product image"
                  fill
                  className="object-contain"
                  unoptimized
                />
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}