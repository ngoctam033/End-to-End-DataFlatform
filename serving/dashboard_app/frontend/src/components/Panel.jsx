export function Panel({ title, meta, wide = false, children }) {
  return (
    <article className={wide ? "panel panel-wide" : "panel"}>
      <div className="panel-title">
        <h2>{title}</h2>
        <span>{meta}</span>
      </div>
      {children}
    </article>
  );
}
