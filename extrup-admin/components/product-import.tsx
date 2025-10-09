"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Upload, Package, FileText, Loader2 } from "lucide-react"
import { apiClient } from "@/lib/api-client"
import type { UploadedFabric } from "@/lib/types"
import { IMPORT_DESTINATIONS } from "@/lib/types"

export function ProductImport() {
  const [destination, setDestination] = useState<"vente" | "xxxlutz">("vente")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  // Fabric import
  const [afterbuyFabricId, setAfterbuyFabricId] = useState("")
  const [deliveryDaysFile, setDeliveryDaysFile] = useState("20")
  const [market, setMarket] = useState("jv")



  const handleFabricImport = async () => {
    if (!afterbuyFabricId.trim()) {
      setError("Please enter Afterbuy Fabric ID")
      return
    }

    try {
      setLoading(true)
      setError("")
      setSuccess("")

      const url = `/import-products-by-fabric-from-file/${destination}`

      const body = JSON.stringify({
        afterbuy_fabric_id: afterbuyFabricId,
        delivery_days: parseInt(deliveryDaysFile),
        market: market
      })

      const response = await apiClient.request(url, {
        method: "POST",
        body: body,
      })

      // If we get here, request was successful
      setSuccess(`Products from fabric ${afterbuyFabricId} imported successfully to ${destination}`)
      setAfterbuyFabricId("")
      setTimeout(() => setSuccess(""), 5000)
    } catch (err) {
      // Handle errors - show them as error messages with details
      const errorMessage = err instanceof Error ? err.message : "Failed to import fabric products"
      setError(`Import failed for fabric ${afterbuyFabricId}. Details: ${errorMessage}`)
      setAfterbuyFabricId("")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Product Import</h1>
        <p className="text-gray-600">Import products to Vente or XXXLutz</p>
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

      {/* Destination Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Select Destination</CardTitle>
          <CardDescription>Choose where to import the products</CardDescription>
        </CardHeader>
        <CardContent>
          <RadioGroup value={destination} onValueChange={(value) => setDestination(value as "vente" | "xxxlutz")}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {IMPORT_DESTINATIONS.map((dest) => (
                <div key={dest.value} className="flex items-center space-x-2">
                  <RadioGroupItem value={dest.value} id={dest.value} />
                  <Label
                    htmlFor={dest.value}
                    className="flex-1 cursor-pointer p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-center space-x-3">
                      <Package className="h-5 w-5 text-blue-600" />
                      <span className="font-medium">{dest.label}</span>
                    </div>
                  </Label>
                </div>
              ))}
            </div>
          </RadioGroup>
        </CardContent>
      </Card>

      {/* Import Options */}
      <Card>
        <CardHeader>
          <CardTitle>Import Options</CardTitle>
          <CardDescription>Choose how you want to import products</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="fabric" className="w-full">
            <TabsList className="grid w-full grid-cols-1">
              {destination === "vente" ? (
                <TabsTrigger value="fabric">Import from File</TabsTrigger>
              ) : (
                <TabsTrigger value="fabric">By Fabric</TabsTrigger>
              )}
            </TabsList>





            {/* Fabric Import */}
            <TabsContent value="fabric" className="space-y-4">
              <div className="space-y-4">
                {destination === "vente" ? (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="afterbuy-fabric-id">Afterbuy Fabric ID</Label>
                      <Input
                        id="afterbuy-fabric-id"
                        placeholder="Enter Afterbuy Fabric ID"
                        value={afterbuyFabricId}
                        onChange={(e) => setAfterbuyFabricId(e.target.value)}
                        disabled={loading}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="delivery-days-file">Delivery Days</Label>
                        <Input
                          id="delivery-days-file"
                          type="number"
                          placeholder="20"
                          value={deliveryDaysFile}
                          onChange={(e) => setDeliveryDaysFile(e.target.value)}
                          disabled={loading}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="market">Market</Label>
                        <Select value={market} onValueChange={setMarket} disabled={loading}>
                          <SelectTrigger id="market">
                            <SelectValue placeholder="Select market" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="jv">JV</SelectItem>
                            <SelectItem value="xl">XL</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="space-y-2">
                      <Label htmlFor="afterbuy-fabric-id-xxxlutz">Afterbuy Fabric ID</Label>
                      <Input
                        id="afterbuy-fabric-id-xxxlutz"
                        placeholder="Enter Afterbuy Fabric ID"
                        value={afterbuyFabricId}
                        onChange={(e) => setAfterbuyFabricId(e.target.value)}
                        disabled={loading}
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label htmlFor="delivery-days-xxxlutz">Delivery Days</Label>
                        <Input
                          id="delivery-days-xxxlutz"
                          type="number"
                          placeholder="20"
                          value={deliveryDaysFile}
                          onChange={(e) => setDeliveryDaysFile(e.target.value)}
                          disabled={loading}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="market-xxxlutz">Market</Label>
                        <Select value={market} onValueChange={setMarket} disabled={loading}>
                          <SelectTrigger id="market-xxxlutz">
                            <SelectValue placeholder="Select market" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="jv">JV</SelectItem>
                            <SelectItem value="xl">XL</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </>
                )}

                <div className="space-y-2">
                  <Button onClick={handleFabricImport} disabled={loading} className="w-full">
                    {loading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Importing...
                      </>
                    ) : (
                      <>
                        <Package className="mr-2 h-4 w-4" />
                        {destination === "vente" ? "Import Products from File" : "Import All Products from Fabric"}
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle>Import Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-gray-600">
          {destination === "vente" ? (
            <p>
              <strong>Import from File:</strong> Import all products from a fabric file with automatic settings (20 delivery days, JV market)
            </p>
          ) : (
            <p>
              <strong>By Fabric:</strong> Import all products from a fabric file by entering the Afterbuy Fabric ID and delivery days
            </p>
          )}
          <p className="text-blue-600 font-medium">
            Current destination: <strong>{destination === "vente" ? "Vente" : "XXXLutz"}</strong>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
