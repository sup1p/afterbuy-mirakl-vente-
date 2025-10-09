"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Search, MoreHorizontal, Eye, Trash2, Flag, Briefcase, Clock, CheckCircle, Users } from "lucide-react"

const jobs = [
  {
    id: 1,
    title: "E-commerce Website Development",
    client: "TechCorp Ltd",
    clientAvatar: "/placeholder.svg?height=32&width=32",
    budget: "$2,500 - $5,000",
    status: "Open",
    applications: 12,
    postedDate: "2024-01-15",
    deadline: "2024-02-15",
    category: "Web Development",
  },
  {
    id: 2,
    title: "Mobile App UI Design",
    client: "StartupXYZ",
    clientAvatar: "/placeholder.svg?height=32&width=32",
    budget: "$1,000 - $2,000",
    status: "In Progress",
    applications: 8,
    postedDate: "2024-01-20",
    deadline: "2024-02-20",
    category: "Design",
  },
  {
    id: 3,
    title: "Content Writing for Blog",
    client: "Digital Agency",
    clientAvatar: "/placeholder.svg?height=32&width=32",
    budget: "$500 - $800",
    status: "Completed",
    applications: 15,
    postedDate: "2024-01-10",
    deadline: "2024-01-25",
    category: "Writing",
  },
  {
    id: 4,
    title: "Social Media Marketing Campaign",
    client: "Fashion Brand",
    clientAvatar: "/placeholder.svg?height=32&width=32",
    budget: "$1,500 - $3,000",
    status: "Open",
    applications: 6,
    postedDate: "2024-01-25",
    deadline: "2024-03-01",
    category: "Marketing",
  },
  {
    id: 5,
    title: "Data Analysis Project",
    client: "Research Institute",
    clientAvatar: "/placeholder.svg?height=32&width=32",
    budget: "$800 - $1,200",
    status: "Hired",
    applications: 9,
    postedDate: "2024-01-18",
    deadline: "2024-02-28",
    category: "Data Science",
  },
]

const jobStats = [
  {
    title: "Total Jobs",
    value: "1,234",
    icon: Briefcase,
    color: "text-blue-600",
  },
  {
    title: "Open Jobs",
    value: "567",
    icon: Clock,
    color: "text-green-600",
  },
  {
    title: "In Progress",
    value: "345",
    icon: Users,
    color: "text-yellow-600",
  },
  {
    title: "Completed",
    value: "322",
    icon: CheckCircle,
    color: "text-purple-600",
  },
]

export function JobManagement() {
  const [searchTerm, setSearchTerm] = useState("")
  const [statusFilter, setStatusFilter] = useState("all")
  const [categoryFilter, setCategoryFilter] = useState("all")

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "Open":
        return <Badge className="bg-green-100 text-green-800">Open</Badge>
      case "In Progress":
        return <Badge className="bg-blue-100 text-blue-800">In Progress</Badge>
      case "Hired":
        return <Badge className="bg-yellow-100 text-yellow-800">Hired</Badge>
      case "Completed":
        return <Badge className="bg-purple-100 text-purple-800">Completed</Badge>
      default:
        return <Badge variant="secondary">{status}</Badge>
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Job Management</h1>
        <p className="text-gray-600">Manage all job postings and applications on the platform</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {jobStats.map((stat) => (
          <Card key={stat.title}>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                  <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
                </div>
                <stat.icon className={`h-8 w-8 ${stat.color}`} />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Jobs Table */}
      <Card>
        <CardHeader>
          <CardTitle>Job Listings</CardTitle>
          <CardDescription>All job postings on the platform</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                placeholder="Search jobs..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="in-progress">In Progress</SelectItem>
                <SelectItem value="hired">Hired</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
              </SelectContent>
            </Select>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
                <SelectValue placeholder="Filter by category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="web-development">Web Development</SelectItem>
                <SelectItem value="design">Design</SelectItem>
                <SelectItem value="writing">Writing</SelectItem>
                <SelectItem value="marketing">Marketing</SelectItem>
                <SelectItem value="data-science">Data Science</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Job Title</TableHead>
                  <TableHead>Client</TableHead>
                  <TableHead>Budget</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Applications</TableHead>
                  <TableHead>Posted Date</TableHead>
                  <TableHead>Deadline</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>
                      <div>
                        <div className="font-medium text-gray-900">{job.title}</div>
                        <div className="text-sm text-gray-500">{job.category}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <Avatar className="h-6 w-6">
                          <AvatarImage src={job.clientAvatar || "/placeholder.svg"} alt={job.client} />
                          <AvatarFallback>
                            {job.client
                              .split(" ")
                              .map((n) => n[0])
                              .join("")}
                          </AvatarFallback>
                        </Avatar>
                        <span className="text-sm">{job.client}</span>
                      </div>
                    </TableCell>
                    <TableCell className="font-medium">{job.budget}</TableCell>
                    <TableCell>{getStatusBadge(job.status)}</TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-1">
                        <Users className="h-4 w-4 text-gray-400" />
                        <span>{job.applications}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-sm text-gray-500">{job.postedDate}</TableCell>
                    <TableCell className="text-sm text-gray-500">{job.deadline}</TableCell>
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
                          <DropdownMenuItem>
                            <Eye className="mr-2 h-4 w-4" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem>
                            <Users className="mr-2 h-4 w-4" />
                            View Applications
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-orange-600">
                            <Flag className="mr-2 h-4 w-4" />
                            Mark as Spam
                          </DropdownMenuItem>
                          <DropdownMenuItem className="text-red-600">
                            <Trash2 className="mr-2 h-4 w-4" />
                            Delete Job
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between space-x-2 py-4">
            <div className="text-sm text-gray-500">Showing 1 to 5 of 1,234 jobs</div>
            <div className="flex space-x-2">
              <Button variant="outline" size="sm" disabled>
                Previous
              </Button>
              <Button variant="outline" size="sm">
                Next
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
