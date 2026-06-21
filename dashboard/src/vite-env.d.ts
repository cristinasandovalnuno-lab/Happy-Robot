/// <reference types="vite/client" />

declare module 'react-simple-maps' {
  import { ComponentType, ReactNode } from 'react'
  export const ComposableMap: ComponentType<any>
  export const Geographies: ComponentType<{ geography: string; children: (data: { geographies: any[] }) => ReactNode }>
  export const Geography: ComponentType<any>
  export const Line: ComponentType<any>
  export const Marker: ComponentType<any>
}