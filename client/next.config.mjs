/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.SERVER_PROTOCOL}://${process.env.SERVER_HOST}/:path*`,
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
