// Address of a file of the public bucket, from the key the API returned. The browser loads it straight from
// the bucket; files are sent through the API, never from the frontend.
export function useFileUrl(key: string): string {
  const base = useRuntimeConfig().public.s3PublicUrl
  return base ? `${base.replace(/\/$/, '')}/${key}` : ''
}
