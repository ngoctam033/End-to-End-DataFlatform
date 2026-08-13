export function compactCurrency(value) {
  const amount = Number(value || 0);
  return `${new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(amount)} VND`;
}

export function fullNumber(value) {
  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(Number(value || 0));
}

export function percent(value) {
  return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

export function chartCurrency(value) {
  return compactCurrency(value).replace(" VND", "");
}
