import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Mini-HDFS Upload',
  description: 'Upload files to distributed file system',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
