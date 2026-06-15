// UI-level role personas. This is NOT a security boundary -- auth is
// stubbed (X-User-Id), the backend does not hard-gate, and these checks only shape
// what the UI offers. Engineer/supervisor get the operational write actions;
// analyst and plant_manager are read-broad (with report/feedback as noted).
export type ActionKey =
  | 'ack_alert'
  | 'ticket_write'
  | 'submit_feedback'
  | 'generate_report'
  | 'run_proactive';

const ACTIONS: Record<string, ActionKey[]> = {
  engineer: ['ack_alert', 'ticket_write', 'submit_feedback', 'generate_report', 'run_proactive'],
  supervisor: ['ack_alert', 'ticket_write', 'submit_feedback', 'generate_report', 'run_proactive'],
  analyst: ['submit_feedback', 'generate_report'],
  plant_manager: ['generate_report'],
  system: [],
};

export function canDo(role: string | undefined, action: ActionKey): boolean {
  if (!role) return false;
  return (ACTIONS[role] ?? ACTIONS.engineer).includes(action);
}
