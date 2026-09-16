import { isAxiosError } from 'axios'

export function getErrorMessage(err: unknown, fallback: string): string {
  if (isAxiosError<{ detail?: string }>(err)) {
    return err.response?.data?.detail ?? fallback
  }
  return fallback
}
