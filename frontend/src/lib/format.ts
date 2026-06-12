export function formatCurrency(value: string | number): string {
  const num = typeof value === 'string' ? Number(value) : value
  return num.toLocaleString('de-DE', { style: 'currency', currency: 'EUR' })
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '–'
  return new Date(value).toLocaleDateString('de-DE')
}

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '–'
  return new Date(value).toLocaleString('de-DE')
}
