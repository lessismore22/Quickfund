/// <reference types="vite/client" />
interface ImportMetaEnv {
  VITE_USE_MOCK_API: string
  readonly VITE_API_BASE_URL: string
  // add more env variables here if needed
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}