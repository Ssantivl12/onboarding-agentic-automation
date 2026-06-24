export default {
  server: {
    proxy: {
      '/chat': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
}
