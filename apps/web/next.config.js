/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'crests.football-data.org',
      },
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
      {
        protocol: 'https',
        hostname: 'media.api-sports.io',
      },
    ],
  },
}

module.exports = nextConfig
