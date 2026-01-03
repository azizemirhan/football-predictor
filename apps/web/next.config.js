/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  experimental: {
    serverActions: true,
  },
  images: {
    domains: ['sofascore.com', 'flashscore.com', 'tmssl.akamaized.net'],
  },
}

module.exports = nextConfig
