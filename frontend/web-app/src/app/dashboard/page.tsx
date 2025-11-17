'use client'

import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export default function Dashboard() {
  // This would fetch actual data from the API
  const { data: healthCheck } = useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await axios.get(`${API_URL}/health`)
      return response.data
    },
  })

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">CreatorSync Dashboard</h1>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-8">
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          <MetricCard
            title="Total Income (30d)"
            value="$12,450"
            change="+23%"
            positive={true}
          />
          <MetricCard
            title="Content Published"
            value="24"
            change="+8%"
            positive={true}
          />
          <MetricCard
            title="Avg Engagement"
            value="5.2%"
            change="-2%"
            positive={false}
          />
        </div>

        <div className="grid lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Income by Platform</h2>
            <div className="space-y-4">
              <PlatformBar platform="YouTube" amount={8500} percentage={68} color="bg-red-500" />
              <PlatformBar platform="TikTok" amount={2100} percentage={17} color="bg-black" />
              <PlatformBar platform="Twitch" amount={1200} percentage={10} color="bg-purple-500" />
              <PlatformBar platform="Patreon" amount={650} percentage={5} color="bg-orange-500" />
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Income Forecast</h2>
            <div className="h-64 flex items-center justify-center text-gray-500">
              Chart placeholder - Recharts will be integrated here
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Top Performing Content</h2>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Content
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Platform
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Views
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Attributed Income
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                <ContentRow
                  title="How I Made $10k in 30 Days"
                  platform="YouTube"
                  views="125,400"
                  income="$3,200"
                />
                <ContentRow
                  title="Day in the Life Vlog"
                  platform="YouTube"
                  views="98,200"
                  income="$2,450"
                />
                <ContentRow
                  title="Viral Dance Challenge"
                  platform="TikTok"
                  views="2.1M"
                  income="$1,800"
                />
              </tbody>
            </table>
          </div>
        </div>

        {healthCheck && (
          <div className="mt-8 text-center text-sm text-gray-500">
            API Status: {healthCheck.status} - Connected to backend
          </div>
        )}
      </main>
    </div>
  )
}

function MetricCard({
  title,
  value,
  change,
  positive
}: {
  title: string
  value: string
  change: string
  positive: boolean
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="text-sm text-gray-600 mb-1">{title}</div>
      <div className="text-3xl font-bold text-gray-900 mb-2">{value}</div>
      <div className={`text-sm ${positive ? 'text-green-600' : 'text-red-600'}`}>
        {change} vs last month
      </div>
    </div>
  )
}

function PlatformBar({
  platform,
  amount,
  percentage,
  color
}: {
  platform: string
  amount: number
  percentage: number
  color: string
}) {
  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-gray-700">{platform}</span>
        <span className="text-sm text-gray-600">${amount.toLocaleString()}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`${color} h-2 rounded-full`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  )
}

function ContentRow({
  title,
  platform,
  views,
  income
}: {
  title: string
  platform: string
  views: string
  income: string
}) {
  return (
    <tr>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
        {title}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {platform}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
        {views}
      </td>
      <td className="px-6 py-4 whitespace-nowrap text-sm font-semibold text-green-600">
        {income}
      </td>
    </tr>
  )
}
