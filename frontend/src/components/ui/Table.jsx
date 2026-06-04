/**
 * Reusable data table with striped rows and blue header.
 * Props:
 *   columns: [{ key, label, render? }]
 *   data: array of row objects
 *   loading: bool
 *   emptyMessage: string
 */
import { useTranslation } from 'react-i18next';
import Spinner from './index.jsx';

export default function Table({ columns, data, loading, emptyMessage }) {
  const { t } = useTranslation();

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table className="table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key}>{col.label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="text-center py-10 text-text-muted">
                {emptyMessage || t('common.no_data')}
              </td>
            </tr>
          ) : (
            data.map((row, i) => (
              <tr key={row.id ?? i}>
                {columns.map((col) => (
                  <td key={col.key}>
                    {col.render ? col.render(row[col.key], row) : (row[col.key] ?? '—')}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
