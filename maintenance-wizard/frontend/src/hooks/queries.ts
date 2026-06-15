import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import { qk } from '@/lib/queryKeys';

export function useMe() {
  return useQuery({ queryKey: qk.me, queryFn: () => api.me() });
}

export function useUsers() {
  return useQuery({ queryKey: qk.users, queryFn: api.users });
}

export function useEquipment() {
  return useQuery({ queryKey: qk.equipment, queryFn: api.equipment });
}

export function usePriority() {
  return useQuery({ queryKey: qk.priority, queryFn: api.priority });
}

export function useSensors(id: string, series = false) {
  return useQuery({
    queryKey: qk.sensors(id, series),
    queryFn: () => api.sensors(id, { series }),
    enabled: !!id,
  });
}

export function useEquipmentDetail(id: string) {
  return useQuery({
    queryKey: qk.equipmentDetail(id),
    queryFn: () => api.equipmentDetail(id),
    enabled: !!id,
  });
}

export function useAlerts(
  opts?: { unacknowledged?: boolean; equipment_id?: string },
  refetchInterval?: number,
) {
  return useQuery({
    queryKey: qk.alerts(opts),
    queryFn: () => api.alerts(opts),
    refetchInterval,
  });
}

export function useTickets(opts?: { status?: string; equipment_id?: string }) {
  return useQuery({ queryKey: qk.tickets(opts), queryFn: () => api.tickets(opts) });
}

export function useTicket(id: string) {
  return useQuery({ queryKey: qk.ticket(id), queryFn: () => api.ticket(id), enabled: !!id });
}

export function useLogbook(opts?: { equipment_id?: string; limit?: number }) {
  return useQuery({ queryKey: qk.logbook(opts), queryFn: () => api.logbook(opts) });
}

export function useProactiveState() {
  return useQuery({ queryKey: qk.proactiveState, queryFn: api.proactiveState });
}
