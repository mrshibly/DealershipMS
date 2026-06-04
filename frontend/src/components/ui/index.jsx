/** Loading spinner */
export default function Spinner({ size = 'md' }) {
  const sz = size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-10 h-10' : 'w-6 h-6';
  return (
    <div className={`${sz} border-2 border-primary border-t-transparent rounded-full animate-spin`} />
  );
}

/** Status badge */
export function Badge({ variant = 'info', children }) {
  const variants = {
    success: 'badge-success',
    warning: 'badge-warning',
    danger:  'badge-danger',
    info:    'badge-info',
    muted:   'bg-border text-text-muted',
  };
  return <span className={`badge ${variants[variant] || variants.info}`}>{children}</span>;
}

/** Page header with title and action button slot */
export function PageHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h1 className="text-xl font-bold text-text">{title}</h1>
        {subtitle && <p className="text-text-muted text-sm mt-0.5">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}

/** Search input */
export function SearchInput({ value, onChange, placeholder }) {
  return (
    <input
      type="search"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      className="input max-w-xs"
    />
  );
}
