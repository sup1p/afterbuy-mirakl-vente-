export interface User {
  id: number
  username: string
  is_admin: boolean
  created_at: string
}

export interface UserCreate {
  username: string
  password: string
  is_admin?: boolean
}

export interface UploadedFabric {
  id: number
  afterbuy_fabric_id: string
  user_id: number
  status: "pending" | "processed" | "error"
  date_time: string
  shop: string
}

export interface UploadedEAN {
  id: number
  ean: string
  fabric_id: number
  status: "pending" | "processed" | "error"
  title: string
  image_1?: string
  image_2?: string
  image_3?: string
  is_correct?: boolean
  created_at: string
  updated_at: string
}

export interface ImportDestination {
  value: "vente" | "xxxlutz"
  label: string
}

export const IMPORT_DESTINATIONS: ImportDestination[] = [
  { value: "vente", label: "Vente" },
  { value: "xxxlutz", label: "XXXLutz" },
]
