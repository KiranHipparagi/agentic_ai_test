export default function Header() {
  return (
    <header style={{
      backgroundColor: "#ffffff",
      borderBottom: "1px solid #E5E7EB",
      padding: "1rem 1.5rem",
      boxShadow: "0 1px 2px 0 rgba(0, 0, 0, 0.05)"
    }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <div style={{
            width: "2.5rem",
            height: "2.5rem",
            backgroundColor: "#D04A02",
            borderRadius: "0.5rem",
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}>
            <span style={{ color: "#ffffff", fontWeight: "bold", fontSize: "1.25rem" }}>P</span>
          </div>
          <div>
            <h1 style={{ fontSize: "1.25rem", fontWeight: "bold", color: "#1F2937" }}>
              Plan IQ
            </h1>
            <p style={{ fontSize: "0.75rem", color: "#6B7280" }}>
              Supply Chain Intelligence Platform
            </p>
          </div>
        </div>
        
        <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
          <span style={{
            display: "inline-flex",
            alignItems: "center",
            padding: "0.25rem 0.75rem",
            borderRadius: "9999px",
            fontSize: "0.75rem",
            fontWeight: "500",
            backgroundColor: "#D1FAE5",
            color: "#065F46"
          }}>
            ● Live
          </span>
        </div>
      </div>
    </header>
  );
}
