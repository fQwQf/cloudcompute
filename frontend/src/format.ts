export function money(value: number): string {
  return `¥${value.toLocaleString('zh-CN', { maximumFractionDigits: 2 })}`;
}

export function percent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function shortTime(value?: string): string {
  if (!value) return '-';
  return new Intl.DateTimeFormat('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(new Date(value));
}
