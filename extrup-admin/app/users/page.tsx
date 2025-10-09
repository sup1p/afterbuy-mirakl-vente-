import { AdminLayout } from "@/components/admin-layout"
import { UserManagement } from "@/components/user-management"

export default function UsersPage() {
  return (
    <AdminLayout>
      <UserManagement />
    </AdminLayout>
  )
}
