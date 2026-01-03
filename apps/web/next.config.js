/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'sofascore.com',
      },
      {
        protocol: 'https',
        hostname: 'flashscore.com',
      },
      {
        protocol: 'https',
        hostname: 'tmssl.akamaized.net',
      },
    ],
  },
}

module.exports = nextConfig
