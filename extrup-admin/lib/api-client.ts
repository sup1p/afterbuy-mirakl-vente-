const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8180"

interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

interface RefreshTokenRequest {
  refresh_token: string
}

class ApiClient {
  private accessToken: string | null = null
  private refreshToken: string | null = null

  constructor() {
    if (typeof window !== "undefined") {
      this.accessToken = localStorage.getItem("access_token")
      this.refreshToken = localStorage.getItem("refresh_token")
    }
  }

  private async refreshAccessToken(): Promise<boolean> {
    if (!this.refreshToken) return false

    try {
      const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: this.refreshToken } as RefreshTokenRequest),
      })

      if (!response.ok) {
        this.clearTokens()
        return false
      }

      const data: TokenResponse = await response.json()
      this.setTokens(data.access_token, data.refresh_token)
      return true
    } catch (error) {
      console.error("Token refresh failed:", error)
      this.clearTokens()
      return false
    }
  }

  private setTokens(accessToken: string, refreshToken: string) {
    this.accessToken = accessToken
    this.refreshToken = refreshToken
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", accessToken)
      localStorage.setItem("refresh_token", refreshToken)
    }
  }

  private clearTokens() {
    this.accessToken = null
    this.refreshToken = null
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
    }
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string>),
    }

    // Не устанавливаем Content-Type для FormData, браузер сделает это автоматически с boundary
    if (!(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json"
    } else {
      console.log('Detected FormData, not setting Content-Type header')
    }

    if (this.accessToken && this.accessToken.trim()) {
      headers["Authorization"] = `Bearer ${this.accessToken}`
    }

    console.log('Request headers:', headers)
    console.log('Request body type:', options.body?.constructor.name)

    let response = await fetch(url, {
      ...options,
      headers,
    })

    // If unauthorized, try to refresh token
    if (response.status === 401 && this.refreshToken) {
      const refreshed = await this.refreshAccessToken()
      if (refreshed) {
        // Retry the request with new token
        if (this.accessToken && this.accessToken.trim()) {
          headers["Authorization"] = `Bearer ${this.accessToken}`
        }
        response = await fetch(url, {
          ...options,
          headers,
        })
      }
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Request failed" }))
      throw new Error(error.detail || `HTTP ${response.status}`)
    }

    // Handle responses without content (like 204 No Content)
    if (response.status === 204) {
      return null as T
    }

    return response.json()
  }

  async login(username: string, password: string): Promise<TokenResponse> {
    const formData = new URLSearchParams()
    formData.append("username", username)
    formData.append("password", password)

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Login failed" }))
      throw new Error(error.detail || "Invalid credentials")
    }

    const data: TokenResponse = await response.json()
    this.setTokens(data.access_token, data.refresh_token)
    return data
  }

  logout() {
    this.clearTokens()
  }

  isAuthenticated(): boolean {
    return !!this.accessToken
  }

  getAccessToken(): string | null {
    return this.accessToken
  }
}

export const apiClient = new ApiClient()
