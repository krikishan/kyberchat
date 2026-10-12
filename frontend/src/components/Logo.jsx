export default function Logo({ size = 28, showText = true, subtitle = null, className = '' }) {
  return (
    <div className={`kyber-logo-brand ${className}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 10, userSelect: 'none' }}>
      {/* Precision Geometric Kyber K Emblem */}
      <svg
        width={size}
        height={size}
        viewBox="0 0 64 64"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ flexShrink: 0, display: 'block' }}
      >
        <defs>
          <linearGradient id="kc-logo-bg" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#4F46E5" />
            <stop offset="100%" stopColor="#3730A3" />
          </linearGradient>
        </defs>

        {/* High-contrast container visible on both dark and light surfaces */}
        <rect x="2" y="2" width="60" height="60" rx="14" fill="url(#kc-logo-bg)" stroke="#818CF8" strokeWidth="2.5" />

        {/* Bold, sharp, unmistakable Kyber 'K' */}
        <rect x="15" y="14" width="8" height="36" rx="3.5" fill="#FFFFFF" />
        <path d="M21 33 L41 15" stroke="#FFFFFF" strokeWidth="8" strokeLinecap="round" />
        <path d="M21 31 L41 49" stroke="#38BDF8" strokeWidth="8" strokeLinecap="round" />
        <circle cx="21" cy="32" r="4.5" fill="#FFFFFF" />
      </svg>

      {showText && (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{
            fontSize: size >= 32 ? 16 : 14,
            fontWeight: 700,
            letterSpacing: '-0.02em',
            lineHeight: 1.2,
            color: 'var(--text-primary)',
            display: 'flex',
            alignItems: 'center',
            gap: 2
          }}>
            <span>Kyber</span><span style={{ color: 'var(--accent)', fontWeight: 600 }}>Chat</span>
          </div>
          {subtitle && (
            <div style={{
              fontSize: 10,
              color: 'var(--text-tertiary)',
              fontWeight: 500,
              letterSpacing: '0.03em',
              lineHeight: 1.2,
              marginTop: 1
            }}>
              {subtitle}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
