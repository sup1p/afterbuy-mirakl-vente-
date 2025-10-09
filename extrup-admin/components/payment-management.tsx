"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { DollarSign, TrendingUp, CreditCard, Wallet, MoreHorizontal, CheckCircle, XCircle } from "lucide-react"

const paymentStats = [
  {
    title: "Total Revenue",
    value: "$234,567",
    change: "+18%",
    icon: DollarSign,
    color: "text-green-600",
  },
  {
    title: "Platform Commission",
    value: "$45,678",
    change: "+15%",
    icon: TrendingUp,
    color: "text-blue-600",
  },
  {
    title: "Pending Payouts",
    value: "$12,345",
    change: "-5%",
    icon: Wallet,
    color: "text-yellow-600",
  },
  {
    title: "Active Transactions",
    value: "1,234",
    change: "+12%",
    icon: CreditCard,
    color: "text-purple-600",
  },
]

const transactions = [
  {
    id: 1,
    user: "Sarah Ahmed",
    type: "Withdraw",
    amount: "$1,250",
    gateway: "Bkash",
    status: "Completed",
    date: "2024-01-15",
    transactionId: "TXN001234",
  },
  {
    id: 2,
    user: "Rahul Sharma",
    type: "Deposit",
    amount: "$2,500",
    gateway: "Nagad",
    status: "Pending",
    date: "2024-01-14",
    transactionId: "TXN001235",
  },
  {
    id: 3,
    user: "Ahmed Hassan",
    type: "Commission",
    amount: "$125",
    gateway: "Platform",
    status: "Completed",
    date: "2024-01-13",
    transactionId: "TXN001236",
  },
  {
    id: 4,
    user: "Priya Patel",
    type: "Withdraw",
    amount: "$800",
    gateway: "Bank Transfer",
    status: "Failed",
    date: "2024-01-12",
    transactionId: "TXN001237",
  },
  {
    id: 5,
    user: "Fatima Khan",
    type: "Deposit",
    amount: "$1,500",
    gateway: "Rocket",
    status: "Completed",
    date: "2024-01-11",
    transactionId: "TXN001238",
  },
]

const payoutRequests = [
  {
    id: 1,
    user: "Sarah Ahmed",
    amount: "$1,250",
    method: "Bkash",
    requestDate: "2024-01-15",
    status: "Pending",
  },
  {
    id: 2,
    user: "Ahmed Hassan",
    amount: "$2,100",
    method: "Bank Transfer",
    requestDate: "2024-01-14",
    status: "Pending",
  },
  {
    id: 3,
    user: "Priya Sharma",
    amount: "$950",
    method: "Nagad",
    requestDate: "2024-01-13",
    status: "Pending",
  },
]

export function PaymentManagement() {
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Completed":
        return <Badge className="bg-green-100 text-green-800">Completed</Badge>
      case "Pending":
        return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>
      case "Failed":
        return <Badge className="bg-red-100 text-red-800">Failed</Badge>
      default:
        return <Badge variant="secondary">{status}</Badge>
    }
  }

  const getTypeColor = (type: string) => {
    switch (type) {
      case "Deposit":
        return "text-green-600"
      case "Withdraw":
        return "text-red-600"
      case "Commission":
        return "text-blue-600"
      default:
        return "text-gray-600"
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Payment & Wallet Management</h1>
        <p className="text-gray-600">Monitor transactions, payouts, and platform earnings</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {paymentStats.map((stat) => (
          <Card key={stat.title}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                  <p className="text-xs text-green-600 font-medium mt-1">{stat.change} from last month</p>
                </div>
                <stat.icon className={`h-8 w-8 ${stat.color}`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Transactions Table */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Recent Transactions</CardTitle>
              <CardDescription>Latest payment transactions on the platform</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="rounded-md border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>User</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Gateway</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {transactions.map((transaction) => (
                      <TableRow key={transaction.id}>
                        <TableCell className="font-medium">{transaction.user}</TableCell>
                        <TableCell>
                          <span className={`font-medium ${getTypeColor(transaction.type)}`}>{transaction.type}</span>
                        </TableCell>
                        <TableCell className="font-medium">{transaction.amount}</TableCell>
                        <TableCell>{transaction.gateway}</TableCell>
                        <TableCell>{getStatusBadge(transaction.status)}</TableCell>
                        <TableCell className="text-sm text-gray-500">{transaction.date}</TableCell>
                        <TableCell className="text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" className="h-8 w-8 p-0">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuLabel>Actions</DropdownMenuLabel>
                              <DropdownMenuItem>View Details</DropdownMenuItem>
                              <DropdownMenuItem>Download Receipt</DropdownMenuItem>
                              {transaction.status === "Pending" && (
                                <>
                                  <DropdownMenuItem className="text-green-600">
                                    <CheckCircle className="mr-2 h-4 w-4" />
                                    Approve
                                  </DropdownMenuItem>
                                  <DropdownMenuItem className="text-red-600">
                                    <XCircle className="mr-2 h-4 w-4" />
                                    Reject
                                  </DropdownMenuItem>
                                </>
                              )}
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Payout Requests */}
        <Card>
          <CardHeader>
            <CardTitle>Payout Requests</CardTitle>
            <CardDescription>Pending withdrawal requests</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {payoutRequests.map((request) => (
              <div key={request.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{request.user}</p>
                  <p className="text-sm text-gray-500">{request.method}</p>
                  <p className="text-xs text-gray-400">{request.requestDate}</p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-gray-900">{request.amount}</p>
                  <div className="flex space-x-1 mt-2">
                    <Button size="sm" className="h-6 text-xs">
                      <CheckCircle className="h-3 w-3 mr-1" />
                      Approve
                    </Button>
                    <Button size="sm" variant="outline" className="h-6 text-xs">
                      <XCircle className="h-3 w-3 mr-1" />
                      Reject
                    </Button>
                  </div>
                </div>
              </div>
            ))}
            <Button variant="outline" className="w-full">
              View All Requests
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Commission Report */}
      <Card>
        <CardHeader>
          <CardTitle>Commission Report</CardTitle>
          <CardDescription>Platform earnings breakdown</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-6 bg-blue-50 rounded-lg">
              <DollarSign className="h-8 w-8 text-blue-600 mx-auto mb-2" />
              <p className="text-2xl font-bold text-gray-900">$45,678</p>
              <p className="text-sm text-gray-600">Total Commission</p>
              <p className="text-xs text-green-600 mt-1">+15% this month</p>
            </div>
            <div className="text-center p-6 bg-green-50 rounded-lg">
              <TrendingUp className="h-8 w-8 text-green-600 mx-auto mb-2" />
              <p className="text-2xl font-bold text-gray-900">8.5%</p>
              <p className="text-sm text-gray-600">Average Commission Rate</p>
              <p className="text-xs text-gray-500 mt-1">Standard rate</p>
            </div>
            <div className="text-center p-6 bg-purple-50 rounded-lg">
              <Wallet className="h-8 w-8 text-purple-600 mx-auto mb-2" />
              <p className="text-2xl font-bold text-gray-900">1,234</p>
              <p className="text-sm text-gray-600">Transactions</p>
              <p className="text-xs text-blue-600 mt-1">This month</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
