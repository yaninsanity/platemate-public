// Market and location related types
export interface Store {
  id: string | number
  name: string
  lat: number
  lon: number
  address?: string
  distance?: number
  tags?: Record<string, string>
}

export interface OverpassElement {
  id: number
  lat: number
  lon: number
  tags?: Record<string, string>
}
