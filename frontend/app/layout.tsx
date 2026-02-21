import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'LatSpace Excel Parser',
  description: 'Intelligent Excel header mapping and data parsing for power plant operations',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-industrial-900 text-industrial-50">{children}</body>
    </html>
  )
}
