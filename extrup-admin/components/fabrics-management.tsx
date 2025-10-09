"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Search,
  MoreHorizontal,
  Eye,
  Trash2,
  Package,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  Edit,
} from "lucide-react"
import { apiClient } from "@/lib/api-client"
import type { UploadedFabric, UploadedEAN } from "@/lib/types"
import { useAuth } from "@/contexts/auth-context"
import Image from "next/image"

type FabricStatus = "pending" | "processed" | "error" | "all"
type EANStatus = "pending" | "processed" | "error" | "all"

export function FabricsManagement() {
  const [fabrics, setFabrics] = useState<UploadedFabric[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [statusFilter, setStatusFilter] = useState<FabricStatus>("all")
  const { user, isAdmin } = useAuth()

  // Dialog states
  const [viewDialogOpen, setViewDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [editEANDialogOpen, setEditEANDialogOpen] = useState(false)
  const [selectedFabric, setSelectedFabric] = useState<UploadedFabric | null>(null)
  const [selectedEAN, setSelectedEAN] = useState<UploadedEAN | null>(null)
  const [fabricEANs, setFabricEANs] = useState<UploadedEAN[]>([])
  const [loadingEANs, setLoadingEANs] = useState(false)
  const [eanStatusFilter, setEanStatusFilter] = useState<EANStatus>("all")

  const [eanStatusUpdate, setEanStatusUpdate] = useState<{
    status: "pending" | "processed" | "error"
    is_correct: boolean | null
  }>({
    status: "pending",
    is_correct: null,
  })

  useEffect(() => {
    loadFabrics()
  }, [statusFilter])

  const loadFabrics = async () => {
    try {
      setLoading(true)
      setError("")
      let data: UploadedFabric[]

      if (statusFilter === "all") {
        data = await apiClient.request<UploadedFabric[]>("/uploaded-fabrics")
      } else {
        data = await apiClient.request<UploadedFabric[]>(`/uploaded-fabrics/fabrics-by-status?status=${statusFilter}`)
      }

      setFabrics(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load fabrics")
    } finally {
      setLoading(false)
    }
  }

  const loadFabricEANs = async (fabricId: string, shop: string) => {
    try {
      setLoadingEANs(true)
      const data = await apiClient.request<UploadedEAN[]>(`/uploaded-fabrics/${shop}/${fabricId}/eans?limit=100&offset=0`)
      setFabricEANs(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load EANs")
    } finally {
      setLoadingEANs(false)
    }
  }

  const handleDeleteFabric = async () => {
    if (!selectedFabric) return
    try {
      setError("")
      await apiClient.request(`/uploaded-fabrics/${selectedFabric.shop}/delete-fabric?afterbuy_fabric_id=${selectedFabric.afterbuy_fabric_id}`, {
        method: "DELETE",
      })
      setSuccess("Fabric deleted successfully")
      setDeleteDialogOpen(false)
      setSelectedFabric(null)
      loadFabrics()
      setTimeout(() => setSuccess(""), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete fabric")
    }
  }

  const handleUpdateEANStatus = async () => {
    if (!selectedEAN) return
    try {
      setError("")
      await apiClient.request("/uploaded-fabrics/update-ean-status", {
        method: "PATCH",
        body: JSON.stringify({
          id: selectedEAN.id,
          new_status: eanStatusUpdate.status,
        }),
      })
      setSuccess("EAN status updated successfully")
      setEditEANDialogOpen(false)
      setSelectedEAN(null)
      if (selectedFabric) {
        await loadFabricEANs(selectedFabric.afterbuy_fabric_id, selectedFabric.shop)
      }
      setTimeout(() => setSuccess(""), 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update EAN status")
    }
  }

  const openViewDialog = async (fabric: UploadedFabric) => {
    setSelectedFabric(fabric)
    setViewDialogOpen(true)
    await loadFabricEANs(fabric.afterbuy_fabric_id, fabric.shop)
  }

  const openDeleteDialog = (fabric: UploadedFabric) => {
    setSelectedFabric(fabric)
    setDeleteDialogOpen(true)
  }

  const openEditEANDialog = (ean: UploadedEAN) => {
    setSelectedEAN(ean)
    setEanStatusUpdate({
      status: ean.status,
      is_correct: ean.is_correct ?? null,
    })
    setEditEANDialogOpen(true)
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "processed":
        return (
          <Badge className="bg-green-100 text-green-800">
            <CheckCircle className="mr-1 h-3 w-3" />
            Processed
          </Badge>
        )
      case "pending":
        return (
          <Badge className="bg-yellow-100 text-yellow-800">
            <Clock className="mr-1 h-3 w-3" />
            Pending
          </Badge>
        )
      case "error":
        return (
          <Badge className="bg-red-100 text-red-800">
            <XCircle className="mr-1 h-3 w-3" />
            Error
          </Badge>
        )
      default:
        return <Badge variant="secondary">{status}</Badge>
    }
  }

  const filteredFabrics = fabrics.filter((fabric) =>
    String(fabric.afterbuy_fabric_id).toLowerCase().includes(searchTerm.toLowerCase()) ||
    String(fabric.shop).toLowerCase().includes(searchTerm.toLowerCase()),
  )

  const filteredEANs = fabricEANs.filter((ean) =>
    eanStatusFilter === "all" || ean.status === eanStatusFilter
  )

  const stats = {
    total: fabrics.length,
    pending: fabrics.filter((f) => f.status === "pending").length,
    processed: fabrics.filter((f) => f.status === "processed").length,
    error: fabrics.filter((f) => f.status === "error").length,
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Fabrics Management</h1>
        <p className="text-gray-600">Manage uploaded fabrics and their products</p>
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

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Fabrics</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
              <Package className="h-8 w-8 text-blue-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Pending</p>
                <p className="text-2xl font-bold text-gray-900">{stats.pending}</p>
              </div>
              <Clock className="h-8 w-8 text-yellow-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Processed</p>
                <p className="text-2xl font-bold text-gray-900">{stats.processed}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Errors</p>
                <p className="text-2xl font-bold text-gray-900">{stats.error}</p>
              </div>
              <AlertCircle className="h-8 w-8 text-red-600" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Fabrics Table */}
      <Card>
        <CardHeader>
          <CardTitle>Fabrics</CardTitle>
          <CardDescription>View and manage uploaded fabrics</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={statusFilter} onValueChange={(value) => setStatusFilter(value as FabricStatus)}>
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
              <TabsList>
                <TabsTrigger value="all">All</TabsTrigger>
                <TabsTrigger value="pending">Pending</TabsTrigger>
                <TabsTrigger value="processed">Processed</TabsTrigger>
                <TabsTrigger value="error">Error</TabsTrigger>
              </TabsList>
              <div className="relative w-full sm:w-64">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  placeholder="Search by fabric ID or shop..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <TabsContent value={statusFilter} className="mt-0">
              {loading ? (
                <div className="text-center py-8 text-gray-500">Loading fabrics...</div>
              ) : filteredFabrics.length === 0 ? (
                <div className="text-center py-8 text-gray-500">No fabrics found</div>
              ) : (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Fabric ID</TableHead>
                        <TableHead>Shop</TableHead>
                        <TableHead>Market</TableHead>
                        <TableHead>User ID</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Created</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {filteredFabrics.map((fabric) => (
                        <TableRow key={fabric.id}>
                          <TableCell className="font-medium">{fabric.afterbuy_fabric_id}</TableCell>
                          <TableCell>{fabric.shop}</TableCell>
                          <TableCell>jv</TableCell>
                          <TableCell>{fabric.user_id}</TableCell>
                          <TableCell>{getStatusBadge(fabric.status)}</TableCell>
                          <TableCell className="text-sm text-gray-500">
                            {fabric.date_time ? new Date(fabric.date_time + (fabric.date_time.includes('Z') ? '' : 'Z')).toLocaleDateString() : 'N/A'}
                          </TableCell>
                          <TableCell className="text-right">
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button variant="ghost" className="h-8 w-8 p-0">
                                  <span className="sr-only">Open menu</span>
                                  <MoreHorizontal className="h-4 w-4" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuLabel>Actions</DropdownMenuLabel>
                                <DropdownMenuItem onClick={() => openViewDialog(fabric)}>
                                  <Eye className="mr-2 h-4 w-4" />
                                  View EANs
                                </DropdownMenuItem>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem onClick={() => openDeleteDialog(fabric)} className="text-red-600">
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete Fabric
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* View Fabric EANs Dialog */}
      <Dialog open={viewDialogOpen} onOpenChange={setViewDialogOpen}>
        <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Fabric Details</DialogTitle>
            <DialogDescription>
              Viewing products (EANs) for fabric: {selectedFabric?.afterbuy_fabric_id}
            </DialogDescription>
          </DialogHeader>
          {selectedFabric && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm font-medium text-gray-600">Fabric ID</p>
                  <p className="text-sm">{selectedFabric.afterbuy_fabric_id}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Shop</p>
                  <p className="text-sm">{selectedFabric.shop}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Status</p>
                  <div className="mt-1">{getStatusBadge(selectedFabric.status)}</div>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">User ID</p>
                  <p className="text-sm">{selectedFabric.user_id}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Created</p>
                  <p className="text-sm">{new Date(selectedFabric.date_time).toLocaleString()}</p>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold mb-3">Products (EANs)</h3>
                <Tabs value={eanStatusFilter} onValueChange={(value) => setEanStatusFilter(value as EANStatus)}>
                  <TabsList className="mb-4">
                    <TabsTrigger value="all">All</TabsTrigger>
                    <TabsTrigger value="pending">Pending</TabsTrigger>
                    <TabsTrigger value="processed">Processed</TabsTrigger>
                    <TabsTrigger value="error">Error</TabsTrigger>
                  </TabsList>

                  <TabsContent value={eanStatusFilter} className="mt-0">
                    {loadingEANs ? (
                      <div className="text-center py-4 text-gray-500">Loading products...</div>
                    ) : filteredEANs.length === 0 ? (
                      <div className="text-center py-4 text-gray-500">No products found</div>
                    ) : (
                      <div className="rounded-md border">
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead>EAN</TableHead>
                              <TableHead>Name</TableHead>
                              <TableHead>Status</TableHead>
                              <TableHead className="text-right">Actions</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {filteredEANs.map((ean) => (
                              <TableRow key={ean.id}>
                                <TableCell className="font-mono text-sm">{ean.ean}</TableCell>
                                <TableCell>{ean.title || "-"}</TableCell>
                                <TableCell>{getStatusBadge(ean.status)}</TableCell>
                                <TableCell className="text-right">
                                  <Button variant="ghost" size="sm" onClick={() => openEditEANDialog(ean)}>
                                    <Edit className="h-4 w-4" />
                                  </Button>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    )}
                  </TabsContent>
                </Tabs>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setViewDialogOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={editEANDialogOpen} onOpenChange={setEditEANDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Update EAN Status</DialogTitle>
            <DialogDescription>Update the status and verification for EAN: {selectedEAN?.ean}</DialogDescription>
          </DialogHeader>
          {selectedEAN && (
            <div className="space-y-4">
              {/* Product Info */}
              <div className="p-4 bg-gray-50 rounded-lg space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm font-medium text-gray-600">Product Name:</span>
                  <span className="text-sm">{selectedEAN.title || "N/A"}</span>
                </div>
              </div>

              {/* Images Preview */}
              {(selectedEAN.image_1 || selectedEAN.image_2 || selectedEAN.image_3) && (
                <div>
                  <Label className="mb-2 block">Product Images</Label>
                  <div className="grid grid-cols-3 gap-2">
                    {[selectedEAN.image_1, selectedEAN.image_2, selectedEAN.image_3].map((image, idx) => (
                      <div key={idx} className="relative aspect-square bg-gray-100 rounded border overflow-hidden">
                        {image ? (
                          <Image
                            src={image || "/placeholder.svg"}
                            alt={`Image ${idx + 1}`}
                            fill
                            className="object-cover"
                            unoptimized
                          />
                        ) : (
                          <div className="absolute inset-0 flex items-center justify-center text-gray-400 text-xs">
                            No image
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Status Selection */}
              <div className="space-y-2">
                <Label htmlFor="ean-status">Processing Status</Label>
                <Select
                  value={eanStatusUpdate.status}
                  onValueChange={(value) =>
                    setEanStatusUpdate({ ...eanStatusUpdate, status: value as "pending" | "processed" | "error" })
                  }
                >
                  <SelectTrigger id="ean-status">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="pending">Pending</SelectItem>
                    <SelectItem value="processed">Processed</SelectItem>
                    <SelectItem value="error">Error</SelectItem>
                  </SelectContent>
                </Select>
              </div>

            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditEANDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateEANStatus}>Update Status</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Fabric</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete fabric {selectedFabric?.afterbuy_fabric_id}? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteFabric}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
