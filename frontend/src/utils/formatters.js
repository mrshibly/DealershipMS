/**
 * Format BDT amounts in Bangladesh format.
 * bd-BD locale uses Indian numbering: 1,23,456.00
 * Prefixed with Bangladeshi Taka symbol ৳
 */

/**
 * Format a number as BDT currency.
 * @param {number|string} amount
 * @param {string} locale - 'bn-BD' or 'en-BD'
 */
export function formatBDT(amount, locale = 'bn-BD') {
  const num = typeof amount === 'string' ? parseFloat(amount) : amount;
  if (isNaN(num)) return '৳0.00';

  return '৳' + num.toLocaleString(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

/**
 * Format a date as dd/mm/yyyy (BD standard).
 * @param {string|Date} date
 */
export function formatDate(date) {
  if (!date) return '';
  const d = typeof date === 'string' ? new Date(date) : date;
  const day = String(d.getDate()).padStart(2, '0');
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
}

/**
 * Convert a Date to YYYY-MM-DD string (for API date params).
 * @param {Date} date
 */
export function toApiDate(date) {
  return date.toISOString().split('T')[0];
}

/**
 * Format BD phone numbers: +8801XXXXXXXXX
 */
export function formatPhone(phone) {
  if (!phone) return '';
  if (phone.startsWith('+880')) return phone;
  if (phone.startsWith('0')) return '+880' + phone.slice(1);
  return phone;
}
