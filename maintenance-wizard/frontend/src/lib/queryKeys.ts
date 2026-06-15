// Centralised React Query keys so invalidation stays consistent.
export const qk = {
  me: ['me'] as const,
  users: ['users'] as const,
  equipment: ['equipment'] as const,
  priority: ['priority'] as const,
  sensors: (id: string, series: boolean) => ['sensors', id, series] as const,
  equipmentDetail: (id: string) => ['equipment-detail', id] as const,
  alerts: (opts?: { unacknowledged?: boolean; equipment_id?: string }) =>
    ['alerts', opts ?? {}] as const,
  tickets: (opts?: { status?: string; equipment_id?: string }) => ['tickets', opts ?? {}] as const,
  ticket: (id: string) => ['ticket', id] as const,
  logbook: (opts?: { equipment_id?: string; limit?: number }) => ['logbook', opts ?? {}] as const,
  proactiveState: ['proactive', 'state'] as const,
};
