"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import {
  Category,
  DashboardSummary,
  MonthlyDashboard,
  Transaction,
  TransactionFilters,
  TransactionPage,
  getCategories,
  getMonthly,
  getSummary,
  getTodaySummary,
  getTransactions,
  saveMerchantRule,
  updateTransaction,
} from "@/lib/api";

const PALETTE = ["#2f6e57", "#9dbd8f", "#e6b85c", "#638a9b", "#d18c75", "#796c9c", "#b5a176", "#77a69a"];
const PAGE_SIZE = 12;

function currentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function monthRange(month: string) {
  const [year, monthIndex] = month.split("-").map(Number);
  const end = new Date(year, monthIndex, 0).getDate();
  return { from: `${month}-01`, to: `${month}-${String(end).padStart(2, "0")}` };
}

function apiMonthRange(month: string) {
  const range = monthRange(month);
  return {
    start_date: filterDate(range.from),
    end_date: filterDate(range.to, true),
  };
}

function dayBounds() {
  const now = new Date();
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const end = new Date(start);
  end.setDate(end.getDate() + 1);
  return { start, end };
}

function filterDate(value: string, endOfDay = false) {
  const date = new Date(`${value}T00:00:00`);
  if (endOfDay) date.setHours(23, 59, 59, 999);
  return date.toISOString();
}

function money(value: string | number, currency = "INR") {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency,
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function displayDate(value: string) {
  return new Intl.DateTimeFormat("en-IN", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
}

function appLabel(app: Transaction["payment_app"]) {
  return ({ gpay: "Google Pay", phonepe: "PhonePe", paytm: "Paytm", other: "Other" })[app];
}

export default function ExpenseDashboard() {
  const initialMonth = currentMonth();
  const [month, setMonth] = useState(initialMonth);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [today, setToday] = useState<DashboardSummary | null>(null);
  const [monthly, setMonthly] = useState<MonthlyDashboard | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [transactions, setTransactions] = useState<TransactionPage | null>(null);
  const [filters, setFilters] = useState<TransactionFilters>({ ...apiMonthRange(initialMonth), limit: PAGE_SIZE, offset: 0 });
  const [draft, setDraft] = useState({ ...monthRange(initialMonth), category: "", payment_app: "", transaction_type: "", merchant: "" });
  const [loading, setLoading] = useState(true);
  const [listLoading, setListLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [listError, setListError] = useState<string | null>(null);
  const [editing, setEditing] = useState<Transaction | null>(null);

  const loadOverview = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const bounds = dayBounds();
      const [summaryResult, monthResult, todayResult, categoryResult] = await Promise.all([
        getSummary(month),
        getMonthly(month),
        getTodaySummary(bounds.start, bounds.end),
        getCategories(),
      ]);
      setSummary(summaryResult);
      setMonthly(monthResult);
      setToday(todayResult);
      setCategories(categoryResult);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "The dashboard could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [month]);

  const loadTransactions = useCallback(async () => {
    setListLoading(true);
    setListError(null);
    try {
      setTransactions(await getTransactions(filters));
    } catch (cause) {
      setListError(cause instanceof Error ? cause.message : "Transactions could not be loaded.");
    } finally {
      setListLoading(false);
    }
  }, [filters]);

  useEffect(() => { void loadOverview(); }, [loadOverview]);
  useEffect(() => { void loadTransactions(); }, [loadTransactions]);

  const chartData = useMemo(
    () => (monthly?.categories ?? []).map((item) => ({ ...item, chartAmount: Number(item.amount) })),
    [monthly],
  );

  function changeMonth(value: string) {
    if (!value) return;
    setMonth(value);
    const range = monthRange(value);
    setDraft((current) => ({ ...current, ...range }));
    setFilters((current) => ({ ...current, ...apiMonthRange(value), offset: 0 }));
  }

  function applyFilters(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFilters({
      start_date: draft.from ? filterDate(draft.from) : undefined,
      end_date: draft.to ? filterDate(draft.to, true) : undefined,
      category: draft.category || undefined,
      payment_app: draft.payment_app || undefined,
      transaction_type: draft.transaction_type || undefined,
      merchant: draft.merchant || undefined,
      limit: PAGE_SIZE,
      offset: 0,
    });
  }

  async function saveTransaction(values: Pick<Transaction, "merchant" | "description" | "category_id">, rememberMerchant: boolean) {
    if (!editing) return;
    await updateTransaction(editing.id, values);
    if (rememberMerchant && values.merchant && values.category_id !== null) {
      try {
        await saveMerchantRule(values.merchant, values.category_id);
      } catch (cause) {
        await Promise.all([loadOverview(), loadTransactions()]);
        throw new Error(`Transaction saved, but the merchant rule could not be saved: ${cause instanceof Error ? cause.message : "please try again"}`);
      }
    }
    setEditing(null);
    await Promise.all([loadOverview(), loadTransactions()]);
  }

  const canGoBack = (transactions?.offset ?? 0) > 0;
  const canGoForward = (transactions?.offset ?? 0) + PAGE_SIZE < (transactions?.total ?? 0);

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#overview" aria-label="Expense Diary overview">
          <span className="brand-mark">e</span>
          <span>expense diary<small>PERSONAL FINANCE</small></span>
        </a>
        <div className="side-label">WORKSPACE</div>
        <nav className="side-nav" aria-label="Main navigation">
          <a className="nav-item active" href="#overview"><span>⌂</span> Overview</a>
          <a className="nav-item" href="#transactions"><span>▤</span> Transactions</a>
          <a className="nav-item" href="#categories"><span>◌</span> Categories</a>
        </nav>
        <div className="privacy-card">
          <span className="privacy-icon">✳</span>
          <strong>Your money, your data.</strong>
          <p>This diary runs on your own backend. No bank login is connected.</p>
        </div>
        <div className="sidebar-footer"><span className="status-dot" /> Local workspace</div>
      </aside>

      <section className="main-area" id="overview">
        <header className="topbar">
          <div className="breadcrumb">Personal <span>/</span> Overview</div>
          <div className="topbar-right"><span className="today-label">{new Intl.DateTimeFormat("en-IN", { dateStyle: "full" }).format(new Date())}</span><span className="avatar">S</span></div>
        </header>

        <div className="page-content">
          <section className="page-heading">
            <div><p className="eyebrow">YOUR MONEY AT A GLANCE</p><h1>Good day<span className="heading-period">.</span></h1><p className="heading-copy">A clear view of where this month is going.</p></div>
            <label className="month-picker"><span>MONTH</span><input type="month" value={month} onChange={(event) => changeMonth(event.target.value)} /></label>
          </section>

          {error && <div className="error-banner" role="alert"><span>Couldn’t load your dashboard</span><p>{error}</p><button onClick={() => void loadOverview()}>Try again</button></div>}

          <section className="summary-grid" aria-label="Spending summary">
            <article className="summary-card primary-card">
              <div className="card-label light-label">MONTHLY SPENDING <span className="card-symbol">↗</span></div>
              <div className="primary-value">{loading ? <span className="skeleton skeleton-value" /> : money(monthly?.total_spent ?? "0")}</div>
              <div className="primary-foot"><span className="primary-foot-dot" /> For {new Intl.DateTimeFormat("en", { month: "long", year: "numeric" }).format(new Date(`${month}-01T12:00:00`))}</div>
              <div className="primary-decoration" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /><i /></div>
            </article>
            <article className="summary-card">
              <div className="card-label">SPENT TODAY <span className="metric-icon">◷</span></div>
              <div className="metric-value">{loading ? <span className="skeleton skeleton-value" /> : money(today?.total_expense ?? "0")}</div>
              <div className="metric-hint">Across today’s transactions</div>
            </article>
            <article className="summary-card">
              <div className="card-label">TRANSACTIONS <span className="metric-icon">▤</span></div>
              <div className="metric-value">{loading ? <span className="skeleton skeleton-value" /> : summary?.transaction_count ?? 0}</div>
              <div className="metric-hint">In the selected month</div>
            </article>
            <article className="summary-card">
              <div className="card-label">DAILY AVERAGE <span className="metric-icon">⌁</span></div>
              <div className="metric-value">{loading ? <span className="skeleton skeleton-value" /> : money(summary?.average_daily_spend ?? "0")}</div>
              <div className="metric-hint">Average spend per day</div>
            </article>
          </section>

          <section className="insights-grid">
            <article className="panel category-panel" id="categories">
              <div className="panel-heading"><div><h2>Spending by category</h2><p>Where your money went this month</p></div><span className="panel-menu" aria-hidden="true">···</span></div>
              {loading ? <div className="chart-loading"><span className="skeleton skeleton-chart" /></div> : chartData.length === 0 ? (
                <div className="empty-chart"><span className="empty-orbit">◌</span><strong>No spending yet</strong><p>Transactions will appear here after they’re recorded.</p></div>
              ) : (
                <div className="category-chart-wrap">
                  <div className="donut-wrap">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={chartData} dataKey="chartAmount" nameKey="category" innerRadius="68%" outerRadius="92%" paddingAngle={3} stroke="none">
                          {chartData.map((entry, index) => <Cell key={entry.category} fill={PALETTE[index % PALETTE.length]} />)}
                        </Pie>
                        <Tooltip formatter={(value) => money(Number(value))} />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="donut-total"><span>TOTAL SPENT</span><strong>{money(monthly?.total_spent ?? "0")}</strong></div>
                  </div>
                  <div className="category-legend">
                    {monthly?.categories.map((item, index) => (
                      <div className="legend-row" key={item.category}>
                        <span className="legend-name"><i style={{ background: PALETTE[index % PALETTE.length] }} />{item.category}</span>
                        <span className="legend-value">{money(item.amount)} <small>{Number(item.percentage).toFixed(0)}%</small></span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </article>

            <article className="panel recent-panel">
              <div className="panel-heading"><div><h2>Recent activity</h2><p>Your latest transactions</p></div><a className="text-link" href="#transactions">View all <span>↗</span></a></div>
              {loading ? <div className="recent-loading"><span className="skeleton skeleton-row" /><span className="skeleton skeleton-row" /><span className="skeleton skeleton-row" /></div> : (summary?.recent_transactions.length ?? 0) === 0 ? (
                <div className="empty-recent"><span className="empty-icon">＋</span><strong>Your diary starts here</strong><p>Once a transaction is captured, it will show up in this list.</p></div>
              ) : (
                <div className="recent-list">
                  {summary?.recent_transactions.slice(0, 6).map((transaction) => <TransactionRow key={transaction.id} transaction={transaction} onEdit={setEditing} compact />)}
                </div>
              )}
            </article>
          </section>

          <section className="panel transactions-panel" id="transactions">
            <div className="panel-heading transaction-heading"><div><h2>Transactions</h2><p>Search and review your expense diary</p></div><span className="transaction-count">{transactions?.total ?? 0} records</span></div>
            <form className="filters" onSubmit={applyFilters}>
              <label className="filter-search"><span aria-hidden="true">⌕</span><input placeholder="Find a merchant" value={draft.merchant} onChange={(event) => setDraft({ ...draft, merchant: event.target.value })} /></label>
              <label className="filter-control"><span className="sr-only">From date</span><input type="date" value={draft.from} onChange={(event) => setDraft({ ...draft, from: event.target.value })} /></label>
              <label className="filter-control"><span className="sr-only">To date</span><input type="date" value={draft.to} onChange={(event) => setDraft({ ...draft, to: event.target.value })} /></label>
              <label className="filter-control"><span className="sr-only">Category</span><select value={draft.category} onChange={(event) => setDraft({ ...draft, category: event.target.value })}><option value="">All categories</option>{categories.map((category) => <option key={category.id} value={category.slug}>{category.name}</option>)}</select></label>
              <label className="filter-control"><span className="sr-only">Payment app</span><select value={draft.payment_app} onChange={(event) => setDraft({ ...draft, payment_app: event.target.value })}><option value="">All apps</option><option value="gpay">Google Pay</option><option value="phonepe">PhonePe</option><option value="paytm">Paytm</option><option value="other">Other</option></select></label>
              <label className="filter-control"><span className="sr-only">Transaction type</span><select value={draft.transaction_type} onChange={(event) => setDraft({ ...draft, transaction_type: event.target.value })}><option value="">All types</option><option value="expense">Expense</option><option value="income">Income</option><option value="refund">Refund</option></select></label>
              <button className="filter-button" type="submit">Apply</button>
            </form>
            {listError && <div className="inline-error" role="alert">{listError} <button onClick={() => void loadTransactions()}>Retry</button></div>}
            <div className="transaction-table-wrap">
              <table className="transaction-table">
                <thead><tr><th>MERCHANT</th><th>CATEGORY</th><th>PAYMENT APP</th><th>DATE &amp; TIME</th><th className="amount-col">AMOUNT</th><th><span className="sr-only">Actions</span></th></tr></thead>
                <tbody>
                  {transactions?.items.map((transaction) => <TransactionTableRow key={transaction.id} transaction={transaction} onEdit={setEditing} />)}
                </tbody>
              </table>
              {listLoading && <div className="table-state"><span className="loader" />Loading transactions…</div>}
              {!listLoading && !listError && (transactions?.items.length ?? 0) === 0 && <div className="table-state empty-state"><span>⌕</span><strong>No transactions found</strong><p>Try changing the date range or filters.</p><button onClick={() => { setDraft({ ...monthRange(month), category: "", payment_app: "", transaction_type: "", merchant: "" }); setFilters({ ...apiMonthRange(month), limit: PAGE_SIZE, offset: 0 }); }}>Clear filters</button></div>}
            </div>
            <div className="pagination"><span>{transactions?.total ? `${(transactions.offset ?? 0) + 1}–${Math.min((transactions.offset ?? 0) + PAGE_SIZE, transactions.total)} of ${transactions.total}` : "0 records"}</span><div><button disabled={!canGoBack || listLoading} onClick={() => setFilters({ ...filters, offset: Math.max(0, (filters.offset ?? 0) - PAGE_SIZE) })}>← Previous</button><button disabled={!canGoForward || listLoading} onClick={() => setFilters({ ...filters, offset: (filters.offset ?? 0) + PAGE_SIZE })}>Next →</button></div></div>
          </section>
          <footer className="page-footer">Expense Diary <span>·</span> Private by design</footer>
        </div>
      </section>
      {editing && <EditTransactionDialog transaction={editing} categories={categories} onClose={() => setEditing(null)} onSave={saveTransaction} />}
    </main>
  );
}

function TransactionRow({ transaction, onEdit, compact = false }: { transaction: Transaction; onEdit: (value: Transaction) => void; compact?: boolean }) {
  return (
    <div className={`transaction-row${compact ? " compact" : ""}`}>
      <div className="merchant-avatar">{(transaction.merchant ?? "?").trim().charAt(0).toUpperCase()}</div>
      <div className="transaction-main"><strong>{transaction.merchant || transaction.description || "Unknown merchant"}</strong><small>{transaction.description || appLabel(transaction.payment_app)}</small></div>
      <div className="transaction-trailing"><strong className={transaction.transaction_type === "income" ? "income-amount" : ""}>{transaction.transaction_type === "income" ? "+" : transaction.transaction_type === "refund" ? "↩ " : "−"}{money(transaction.amount, transaction.currency)}</strong><small>{displayDate(transaction.transaction_time)}</small></div>
      {!compact && <button className="edit-icon-button" onClick={() => onEdit(transaction)} aria-label={`Edit ${transaction.merchant ?? "transaction"}`}>···</button>}
    </div>
  );
}

function TransactionTableRow({ transaction, onEdit }: { transaction: Transaction; onEdit: (value: Transaction) => void }) {
  return (
    <tr>
      <td><div className="table-merchant"><span className="merchant-avatar small-avatar">{(transaction.merchant ?? "?").trim().charAt(0).toUpperCase()}</span><span><strong>{transaction.merchant || "Unknown merchant"}</strong><small>{transaction.description || "No description"}</small></span></div></td>
      <td><span className="category-pill">{transaction.category?.name ?? "Uncategorized"}</span></td>
      <td><span className="app-name"><i className={`app-dot ${transaction.payment_app}`} />{appLabel(transaction.payment_app)}</span></td>
      <td className="date-cell">{displayDate(transaction.transaction_time)}</td>
      <td className={`amount-cell ${transaction.transaction_type === "income" ? "income-amount" : ""}`}>{transaction.transaction_type === "income" ? "+" : transaction.transaction_type === "refund" ? "↩ " : "−"}{money(transaction.amount, transaction.currency)}</td>
      <td><button className="edit-icon-button" onClick={() => onEdit(transaction)} aria-label={`Edit ${transaction.merchant ?? "transaction"}`}>···</button></td>
    </tr>
  );
}

function EditTransactionDialog({
  transaction,
  categories,
  onClose,
  onSave,
}: {
  transaction: Transaction;
  categories: Category[];
  onClose: () => void;
  onSave: (values: Pick<Transaction, "merchant" | "description" | "category_id">, rememberMerchant: boolean) => Promise<void>;
}) {
  const [merchant, setMerchant] = useState(transaction.merchant ?? "");
  const [description, setDescription] = useState(transaction.description ?? "");
  const [categoryId, setCategoryId] = useState(transaction.category_id?.toString() ?? "");
  const [rememberMerchant, setRememberMerchant] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await onSave(
        { merchant: merchant.trim() || null, description: description.trim() || null, category_id: categoryId ? Number(categoryId) : null },
        rememberMerchant,
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Could not save your changes.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section className="edit-dialog" role="dialog" aria-modal="true" aria-labelledby="edit-title">
        <div className="dialog-heading"><div><p className="eyebrow">TRANSACTION DETAILS</p><h2 id="edit-title">Edit transaction</h2></div><button className="close-button" onClick={onClose} aria-label="Close">×</button></div>
        <p className="dialog-amount">{money(transaction.amount, transaction.currency)} <span>· {displayDate(transaction.transaction_time)}</span></p>
        <form onSubmit={submit} className="edit-form">
          <label>Merchant<input value={merchant} onChange={(event) => setMerchant(event.target.value)} maxLength={200} /></label>
          <label>Description<input value={description} onChange={(event) => setDescription(event.target.value)} maxLength={500} /></label>
          <label>Category<select value={categoryId} onChange={(event) => setCategoryId(event.target.value)}><option value="">No category</option>{categories.map((category) => <option value={category.id} key={category.id}>{category.name}</option>)}</select></label>
          <label className="remember-rule"><input type="checkbox" checked={rememberMerchant} disabled={!merchant.trim() || !categoryId} onChange={(event) => setRememberMerchant(event.target.checked)} /><span><strong>Use this category for future transactions from this merchant</strong><small>Saves a merchant rule for “{merchant.trim() || "this merchant"}”.</small></span></label>
          {error && <p className="dialog-error" role="alert">{error}</p>}
          <div className="dialog-actions"><button className="secondary-button" type="button" onClick={onClose}>Cancel</button><button className="primary-button" type="submit" disabled={saving}>{saving ? "Saving…" : "Save changes"}</button></div>
        </form>
      </section>
    </div>
  );
}
