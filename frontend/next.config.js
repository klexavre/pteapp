/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
      {
        source: '/audio/:path*',
        destination: 'http://127.0.0.1:8000/audio/:path*',
      },
      {
        source: '/word_audio/:path*',
        destination: 'http://127.0.0.1:8000/word_audio/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
