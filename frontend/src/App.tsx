import { useState, useEffect, useRef } from 'react'
import Dashboard from './pages/Dashboard'
import Vulnerabilities from './pages/Vulnerabilities'
import Reports from './pages/Reports'
import Analysis from './pages/Analysis'
import Analytics from './pages/Analytics'
import Patches from './pages/Patches'
import Settings from './pages/Settings'

function UserAccountSection() {
  const email = localStorage.getItem('user_email') || 'Not logged in'
  const initials = email
    .split('@')[0]
    .split('.')
    .map(p => p[0]?.toUpperCase())
    .join('')
    .slice(0, 2) || 'XX'

  return (
    <div style={{ padding: '18px 22px', borderTop: '1px solid rgba(232,0,29,.12)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', borderRadius: 3, border: '1px solid rgba(232,0,29,.15)', background: 'rgba(232,0,29,.04)', cursor: 'pointer' }}>
        <div style={{ width: 36, height: 36, borderRadius: 3, background: '#e8001d', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'Bebas Neue',sans-serif", fontSize: 14, color: '#fff', fontWeight: 700 }}>{initials}</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#f0f0f0' }}>{email.split('@')[0]}</div>
          <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 9, color: '#888', letterSpacing: 1, textTransform: 'lowercase' }}>{email}</div>
        </div>
      </div>
    </div>
  )
}

type Tab = 'dashboard' | 'vulnerabilities' | 'reports' | 'analysis' | 'analytics' | 'patches' | 'settings'

const NAV = [
  { key: 'dashboard',       label: 'Dashboard',      icon: '\u{1F4CA}' },
  { key: 'vulnerabilities', label: 'Verifications',   icon: '\u{1F6E1}', badge: 12 },
  { key: 'reports',         label: 'Reports',         icon: '\u{1F4C4}' },
  { key: 'analysis',        label: 'Analysis',        icon: '\u{1F50D}' },
  { key: 'analytics',       label: 'Analytics',       icon: '\u{1F4C8}' },
  { key: 'patches',         label: 'Patches',         icon: '\u{1F529}' },
  { key: 'settings',        label: 'Settings',        icon: '\u{2699}' },
]

export default function App() {
  const [tab, setTab] = useState<Tab>('dashboard')
  const curRef  = useRef<HTMLDivElement>(null)
  const curRRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    let rx = 0, ry = 0, mx = 0, my = 0
    const move = (e: MouseEvent) => {
      mx = e.clientX; my = e.clientY
      if (curRef.current) { curRef.current.style.left = mx + 'px'; curRef.current.style.top = my + 'px' }
    }
    const animate = () => {
      rx += (mx - rx) * 0.15; ry += (my - ry) * 0.15
      if (curRRef.current) { curRRef.current.style.left = rx + 'px'; curRRef.current.style.top = ry + 'px' }
      requestAnimationFrame(animate)
    }
    document.addEventListener('mousemove', move)
    const id = requestAnimationFrame(animate)
    return () => { document.removeEventListener('mousemove', move); cancelAnimationFrame(id) }
  }, [])

  return (
    <div style={{ display:'flex', minHeight:'100vh', position:'relative', zIndex:1 }}>
      {/* BG Effects */}
      <div className="radial-bg" style={{ position:'fixed', inset:0, zIndex:0, overflow:'hidden' }} />
      <div className="grid-bg" />
      <div className="scan-line" />
      <div id="cur" ref={curRef} />
      <div id="curR" ref={curRRef} />

      {/* SIDEBAR */}
      <aside style={{ width:220, minHeight:'100vh', flexShrink:0, background:'rgba(6,6,6,.97)', borderRight:'1px solid rgba(232,0,29,.18)', display:'flex', flexDirection:'column', position:'sticky', top:0, height:'100vh', zIndex:10 }}>
        <div style={{ padding:'30px 22px 26px', borderBottom:'1px solid rgba(232,0,29,.1)' }}>
          <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:40, letterSpacing:8, color:'#fff', lineHeight:1, textShadow:'0 0 10px rgba(232,0,29,.8),0 0 30px rgba(232,0,29,.5)' }}>
            ZOR<span style={{ color:'#e8001d' }}>IX</span>
          </div>
          <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:9, color:'#e8001d', letterSpacing:2, textTransform:'uppercase', marginTop:5, opacity:.7 }}>// AI Security Validation</div>
        </div>

        <nav style={{ padding:'18px 0', flex:1 }}>
          <div style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:9, letterSpacing:3, color:'#555', textTransform:'uppercase', padding:'14px 22px 6px' }}>// Core</div>
          {NAV.map((item) => (
            <div key={item.key} onClick={() => setTab(item.key as Tab)} style={{ display:'flex', alignItems:'center', gap:11, padding:'12px 22px', cursor:'pointer', borderLeft: tab===item.key ? '3px solid #e8001d' : '3px solid transparent', fontSize:15, fontWeight:600, letterSpacing:.5, textTransform:'uppercase', color: tab===item.key ? '#fff' : '#888', background: tab===item.key ? 'rgba(232,0,29,.1)' : 'transparent', transition:'all .22s' }}>
              <span style={{ fontSize:17, width:20, textAlign:'center' }}>{item.icon}</span>
              {item.label}
              {item.badge && <span style={{ marginLeft:'auto', background:'#e8001d', color:'#fff', fontFamily:"'Share Tech Mono',monospace", fontSize:10, padding:'2px 8px', borderRadius:2 }}>{item.badge}</span>}
            </div>
          ))}
        </nav>

        <UserAccountSection />
      </aside>

      {/* MAIN */}
      <div style={{ flex:1, display:'flex', flexDirection:'column', overflow:'hidden' }}>
        {/* HEADER */}
        <div style={{ height:64, background:'rgba(6,6,6,.92)', backdropFilter:'blur(20px)', borderBottom:'1px solid rgba(232,0,29,.18)', display:'flex', alignItems:'center', justifyContent:'space-between', padding:'0 34px', position:'sticky', top:0, zIndex:100 }}>
          <div style={{ display:'flex', alignItems:'center', gap:18 }}>
            <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:22, letterSpacing:4, color:'#fff', textTransform:'uppercase' }}>
              {NAV.find(n => n.key === tab)?.label || 'Dashboard'}
            </div>
            <div style={{ display:'flex', alignItems:'center', gap:6, padding:'5px 14px', border:'1px solid rgba(0,255,100,.22)', background:'rgba(0,255,100,.04)', borderRadius:2 }}>
              <div style={{ width:7, height:7, borderRadius:'50%', background:'#00ff64', boxShadow:'0 0 8px #00ff64', animation:'livePulse 1.2s infinite' }} />
              <span style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:10, color:'#00ff64', letterSpacing:2 }}>LIVE</span>
            </div>
          </div>

          <div style={{ display:'flex', gap:2, background:'rgba(12,12,12,.8)', border:'1px solid rgba(232,0,29,.15)', borderRadius:3, padding:3 }}>
            {(['dashboard','vulnerabilities','reports','analysis'] as Tab[]).map((t) => (
              <button key={t} onClick={() => setTab(t)} style={{ fontFamily:"'Share Tech Mono',monospace", fontSize:11, letterSpacing:2, padding:'7px 18px', cursor:'pointer', border:'none', borderRadius:2, textTransform:'uppercase', background: tab===t ? '#e8001d' : 'transparent', color: tab===t ? '#fff' : '#888', transition:'all .2s' }}>
                {t === 'dashboard' ? 'Dashboard' : t === 'vulnerabilities' ? 'Verifications' : t === 'reports' ? 'Reports' : 'Analysis'}
              </button>
            ))}
          </div>

          <div style={{ display:'flex', gap:8 }}>
            {['\u{1F514}','\u{1F50D}'].map((icon, i) => (
              <div key={i} style={{ width:40, height:40, display:'flex', alignItems:'center', justifyContent:'center', border:'1px solid rgba(232,0,29,.18)', borderRadius:3, background:'rgba(232,0,29,.04)', cursor:'pointer', fontSize:18, position:'relative' }}>
                {icon}
                {i===1 && <div style={{ position:'absolute', top:6, right:6, width:7, height:7, background:'#e8001d', borderRadius:'50%', border:'1.5px solid #000' }} />}
              </div>
            ))}
          </div>
        </div>

        {/* CONTENT */}
        <main style={{ flex:1, overflowY:'auto', padding:'30px 34px 60px', position:'relative', zIndex:1 }}>
          {tab === 'dashboard'       && <Dashboard />}
          {tab === 'vulnerabilities' && <Vulnerabilities />}
          {tab === 'reports'         && <Reports />}
          {tab === 'analysis'        && <Analysis />}
          {tab === 'analytics'       && <Analytics />}
          {tab === 'patches'         && <Patches />}
          {tab === 'settings'        && <Settings />}
        </main>
      </div>
      <style>{`@keyframes livePulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(.75)}}`}</style>
    </div>
  )
}
