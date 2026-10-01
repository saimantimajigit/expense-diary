const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1").replace(/\/$/, "");

export interface Category {
  id: number;
  name: string;
  slug: string;
  is_active: boolean;
}

export interface Transaction {
  id: number;
  amount: string;
  currency: string;
  transaction_type: "expense" | "income" | "refund";
  merchant: string | null;
  description: string | null;
  category_id: number | null;
  category: Pick<Category, "id" | "name" | "slug"> | null;
  source: "notification" | "manual" | "statement_import";
  payment_app: "gpay" | "phonepe" | "paytm" | "other";
  transaction_reference: string | null;
  transaction_time: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionPage {
  items: Transaction[];
  total: number;
  limit: number;
  offset: number;
}

export interface CategoryBreakdown {
  category: string;
  amount: string;
  percentage: string;
}

export interface DashboardSummary {
  start_date: string;
  end_date: string;
  total_expense: string;
  total_income: string;
  total_refund: string;
  transaction_count: number;
  average_daily_spend: string;
  category_breakdown: CategoryBreakdown[];
  recent_transactions: Transaction[];
}

export interface MonthlyDashboard {
  month: string;
  total_spent: string;
  categories: CategoryBreakdown[];
}

export interface TransactionFilters {
  start_date?: string;
  end_date?: string;
  category?: string;
  payment_app?: string;
  merchant?: string;
  transaction_type?: string;
  limit?: number;
  offset?: number;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
      cache: "no-store",
    });
  } catch {
    throw new Error("Can’t reach the API. Check that the backend is running and NEXT_PUBLIC_API_URL is correct.");
  }
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // Keep the HTTP status message when the server response is not JSON.
    }
    throw new Error(detail);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function getCategories() {
  return request<Category[]>("/categories");
}

export function getSummary(month: string) {
  return request<DashboardSummary>(`/dashboard/summary?month=${encodeURIComponent(month)}`);
}

export function getTodaySummary(start: Date, end: Date) {
  const query = new URLSearchParams({ start_date: start.toISOString(), end_date: end.toISOString() });
  return request<DashboardSummary>(`/dashboard/summary?${query.toString()}`);
}

export function getMonthly(month: string) {
  return request<MonthlyDashboard>(`/dashboard/monthly?month=${encodeURIComponent(month)}`);
}

export function getTransactions(filters: TransactionFilters) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== "") query.set(key, String(value));
  }
  return request<TransactionPage>(`/transactions?${query.toString()}`);
}

export function updateTransaction(id: number, values: Pick<Transaction, "merchant" | "description" | "category_id">) {
  return request<Transaction>(`/transactions/${id}`, { method: "PATCH", body: JSON.stringify(values) });
}

export function saveMerchantRule(merchant_pattern: string, category_id: number) {
  return request<{ id: number }>("/merchant-rules", {
    method: "POST",
    body: JSON.stringify({ merchant_pattern, category_id, priority: 10, is_active: true }),
  });
}
