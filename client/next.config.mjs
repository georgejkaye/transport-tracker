/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.API_PROTOCOL}://${process.env.API_HOST}/:path*`,
      },
    ]
  },
  output: "standalone",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "www.georgejkaye.com",
      },
    ],
  },
}

export default nextConfig
