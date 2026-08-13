export function StockTag({ value }) {
  return <span className={`tag ${value || ""}`}>{value}</span>;
}
