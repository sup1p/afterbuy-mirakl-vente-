"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BookOpen, Users, Package, ImageIcon, Upload, Settings } from "lucide-react"

export function DashboardOverview() {
  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-gray-600">Welcome to the Omar s Admin Panel</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              User Management
            </CardTitle>
            <CardDescription>Manage system users and permissions</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Available Actions:</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• View all registered users</li>
                <li>• Create new user accounts</li>
                <li>• Edit user permissions</li>
                <li>• Delete user accounts</li>
              </ul>
            </div>
            <Badge variant="outline" className="text-xs">
              Admin Only
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Package className="h-5 w-5" />
              Fabrics Management
            </CardTitle>
            <CardDescription>Import and manage fabric data</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Available Actions:</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Upload fabric data files</li>
                <li>• View fabric processing status</li>
                <li>• Monitor import progress</li>
                <li>• Delete fabric records</li>
              </ul>
            </div>
            <Badge variant="secondary" className="text-xs">
              All Users
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ImageIcon className="h-5 w-5" />
              Image Verification
            </CardTitle>
            <CardDescription>Verify product images for accuracy</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Available Actions:</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Select fabric to verify</li>
                <li>• Review product images</li>
                <li>• Mark images as correct/incorrect</li>
                <li>• View verification history</li>
              </ul>
            </div>
            <Badge variant="secondary" className="text-xs">
              All Users
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Product Import
            </CardTitle>
            <CardDescription>Import products to different destinations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <h4 className="font-medium text-sm">Available Actions:</h4>
              <ul className="text-sm text-gray-600 space-y-1">
                <li>• Select import destination</li>
                <li>• Upload product data</li>
                <li>• Configure import settings</li>
                <li>• Monitor import status</li>
              </ul>
            </div>
            <Badge variant="secondary" className="text-xs">
              All Users
            </Badge>
          </CardContent>
        </Card>

        <Card className="md:col-span-2 lg:col-span-3">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              Getting Started
            </CardTitle>
            <CardDescription>Quick guide to using the admin panel</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <h4 className="font-medium text-sm mb-2">For New Users:</h4>
                <ol className="text-sm text-gray-600 space-y-1 list-decimal list-inside">
                  <li>Start with Fabrics Management to upload your data</li>
                  <li>Use Image Verification to check product images</li>
                  <li>Import products to your desired destination</li>
                  <li>Monitor progress in each section</li>
                </ol>
              </div>
              <div>
                <h4 className="font-medium text-sm mb-2">Navigation Tips:</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  <li>• Use the sidebar to navigate between sections</li>
                  <li>• Check badges for item counts</li>
                  <li>• Look for loading indicators during operations</li>
                  <li>• Error messages appear at the top of pages</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}