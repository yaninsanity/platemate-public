// Navigation related types
export interface NavItem {
  to: string
  icon: string
  label: string
  color: string
  notification?: number
}

export interface Item {
  name: string
  icon: string
  path?: string
  action?: () => void
}
