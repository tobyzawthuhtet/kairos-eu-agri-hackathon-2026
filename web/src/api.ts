export type Alert = {
  farm_id: string; hazard: string; severity: string; title: string; action: string; created_at: string;
};

export async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`);
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}
