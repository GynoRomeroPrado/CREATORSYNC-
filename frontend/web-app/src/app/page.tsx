'use client'

import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-gray-900 mb-4">
            CreatorSync
          </h1>
          <p className="text-2xl text-gray-700 mb-8">
            Sistema Operativo Financiero para Creadores
          </p>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Gestión financiera all-in-one: atribución de ingresos multi-plataforma,
            optimización fiscal, CRM de marcas, factorización de facturas.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8 mb-16">
          <FeatureCard
            title="Atribución de Ingresos"
            description="Tracking multi-plataforma con correlación views → ingresos y análisis predictivo"
            icon="📊"
            link="/dashboard"
          />
          <FeatureCard
            title="Optimización Fiscal"
            description="Categorización automática de gastos y cálculo de impuestos trimestrales"
            icon="💰"
            link="/tax"
          />
          <FeatureCard
            title="CRM de Marcas"
            description="Pipeline management, media kits automáticos y contract tracking"
            icon="🤝"
            link="/crm"
          />
          <FeatureCard
            title="Factorización"
            description="Adelanto de 80-95% del valor de facturas en 24-48h"
            icon="⚡"
            link="/factoring"
          />
        </div>

        <div className="bg-white rounded-lg shadow-xl p-8 max-w-4xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 mb-6">Mercado Objetivo</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <StatCard label="Economía creadora" value="$104-500B" />
            <StatCard label="Creadores en YouTube" value="64M+" />
            <StatCard label="Creadores totales" value="165M+" />
            <StatCard label="Gen Z creadores" value="28%" />
          </div>
        </div>

        <div className="text-center mt-16">
          <Link
            href="/dashboard"
            className="inline-block bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
          >
            Ir al Dashboard
          </Link>
        </div>
      </div>
    </main>
  )
}

function FeatureCard({
  title,
  description,
  icon,
  link
}: {
  title: string
  description: string
  icon: string
  link: string
}) {
  return (
    <Link href={link}>
      <div className="bg-white rounded-lg shadow-lg p-6 hover:shadow-xl transition-shadow cursor-pointer h-full">
        <div className="text-4xl mb-4">{icon}</div>
        <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-600">{description}</p>
      </div>
    </Link>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-blue-50 rounded-lg p-4">
      <div className="text-3xl font-bold text-blue-600 mb-1">{value}</div>
      <div className="text-gray-700">{label}</div>
    </div>
  )
}
