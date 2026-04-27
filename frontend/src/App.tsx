import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  ShieldCheck, 
  Upload, 
  BarChart3, 
  FileText, 
  ChevronRight, 
  AlertTriangle, 
  Activity, 
  Globe,
  Settings,
  Download,
  Terminal,
  Moon,
  Sun
} from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  LineChart, 
  Line,
  ErrorBar,
  AreaChart,
  Area
} from 'recharts';

// --- Utils ---

const getCookie = (name: string) => {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop()?.split(';').shift();
  return null;
};

const setCookie = (name: string, value: string) => {
  document.cookie = `${name}=${value}; path=/; max-age=31536000; SameSite=Lax`;
};

// --- Types & Mock Data ---

type Page = 'home' | 'upload' | 'dashboard' | 'certificate';
type Theme = 'light' | 'dark';

const CAUSAL_RACE = [
  { name: 'Ctf-DE', value: 0.12, low: 0.08, high: 0.16 },
  { name: 'Ctf-IE', value: 0.04, low: 0.02, high: 0.06 },
  { name: 'Ctf-SE', value: -0.02, low: -0.05, high: 0.01 },
];

const CAUSAL_GENDER = [
  { name: 'Ctf-DE', value: 0.05, low: 0.03, high: 0.07 },
  { name: 'Ctf-IE', value: 0.01, low: 0.00, high: 0.02 },
  { name: 'Ctf-SE', value: 0.01, low: -0.01, high: 0.03 },
];

const CAUSAL_AGE = [
  { name: 'Ctf-DE', value: 0.18, low: 0.14, high: 0.22 },
  { name: 'Ctf-IE', value: 0.06, low: 0.04, high: 0.08 },
  { name: 'Ctf-SE', value: -0.03, low: -0.06, high: 0.00 },
];

const DRIFT_DATA = Array.from({ length: 30 }, (_, i) => {
  const base = 0.4 + Math.sin(i / 5) * 0.1;
  const drift = base + (i > 22 ? 0.25 : 0) + (Math.random() - 0.5) * 0.05;
  return {
    day: i + 1,
    drift,
    upper: drift + 0.1,
    lower: drift - 0.1,
    alert: i === 23 || i === 28
  };
});

// --- UI Components ---

const Button = ({ children, onClick, variant = 'primary', className = '' }: any) => {
  const base = "px-6 py-3 font-mono text-xs uppercase tracking-tighter transition-all flex items-center gap-2 border rounded-none group";
  const variants: any = {
    primary: "bg-foreground text-background hover:bg-foreground/90 border-foreground",
    outline: "bg-transparent text-foreground border-foreground/30 hover:border-foreground",
    ghost: "bg-transparent text-foreground border-none hover:bg-foreground/5",
  };
  return (
    <button onClick={onClick} className={`${base} ${variants[variant]} ${className}`}>
      {children}
    </button>
  );
};

const Card = ({ children, title, subtitle, className = "", delay = 0 }: any) => (
  <motion.div 
    initial={{ opacity: 0, y: 20 }}
    whileInView={{ opacity: 1, y: 0 }}
    viewport={{ once: true }}
    transition={{ delay, duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
    className={`glass p-8 h-[340px] flex flex-col group hover:shadow-2xl hover:shadow-foreground/5 transition-shadow relative overflow-hidden ${className}`}
  >
    <div className="absolute top-0 left-0 w-full h-0.5 bg-foreground/10 group-hover:bg-foreground transition-colors" />
    {title && (
      <div className="mb-6">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="font-mono text-[10px] uppercase opacity-40 tracking-widest mb-1">{subtitle}</h3>
            <h2 className="font-serif italic text-2xl leading-none">{title}</h2>
          </div>
          <Terminal size={14} className="opacity-10 group-hover:opacity-40" />
        </div>
      </div>
    )}
    <div className="flex-1 overflow-hidden min-h-0">
      {children}
    </div>
  </motion.div>
);

const Gauge = ({ value, label, max = 1, threshold = 0.8 }: { value: number; label: string; max?: number; threshold?: number }) => {
  const percentage = (value / max) * 100;
  const isAlert = value < threshold;
  return (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="relative w-40 h-40">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="1" className="opacity-5" />
          <motion.circle 
            cx="50" cy="50" r="42" fill="none" stroke={isAlert ? "#ef4444" : "currentColor"} strokeWidth="4" 
            initial={{ strokeDasharray: "0 264" }}
            animate={{ strokeDasharray: `${percentage * 2.64} 264` }}
            transition={{ duration: 1.5, ease: "circOut" }}
            className="opacity-80"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-serif italic">{value.toFixed(2)}</span>
          <span className="text-[9px] font-mono opacity-50 uppercase tracking-[0.2em] mt-1">{label}</span>
        </div>
      </div>
      {isAlert && <div className="mt-4 text-[10px] font-mono text-red-500 uppercase tracking-widest animate-pulse font-bold">Insecure Variance Detected</div>}
    </div>
  );
};

// --- Pages ---

const HomePage = ({ onNavigate }: { onNavigate: (p: Page) => void }) => (
  <motion.div 
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="max-w-6xl mx-auto py-32 px-10 relative"
  >
    <div className="absolute top-20 right-10 opacity-5 pointer-events-none tech-grid w-96 h-96 -z-10" />
    
    <div className="mb-24 flex flex-col items-start">
      <motion.div 
        initial={{ width: 0 }}
        animate={{ width: 120 }}
        className="h-1.5 bg-foreground mb-12"
      />
      <motion.h1 
        initial={{ y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, ease: [0.23, 1, 0.32, 1] }}
        className="text-9xl font-serif italic leading-tight mb-8 tracking-tighter"
      >
        FairGuard.
      </motion.h1>
      <motion.p 
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.2, duration: 0.8 }}
        className="text-4xl font-sans tracking-tight max-w-3xl opacity-80 leading-snug font-light"
      >
        Independent algorithmic verification for AI decision layers. Protect against causal bias with mathematical certainty.
      </motion.p>
    </div>

    <div className="grid md:grid-cols-2 gap-16 items-start">
      <div className="space-y-12">
        <div className="flex items-center gap-6 text-[11px] font-mono uppercase tracking-[0.4em] opacity-40">
          <ShieldCheck size={18} />
          <span>Audit Protocol: IEEE 7000-2021 Verfied</span>
        </div>
        <div className="flex gap-8">
          <Button onClick={() => onNavigate('upload')} className="px-10 py-5 text-sm">
            Launch New Audit <ChevronRight size={18} className="group-hover:translate-x-2 transition-transform" />
          </Button>
          <Button variant="outline" onClick={() => onNavigate('dashboard')} className="px-10 py-5 text-sm">
            Public Registries
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-6 pt-12">
        {[
          { icon: Terminal, label: 'CAUSAL DECOMP', desc: 'Direct/Indirect effect breakdown' },
          { icon: Activity, label: 'RESILIENCE', desc: 'Rhea-style stress testing' },
          { icon: Globe, label: 'REGULATORY', desc: 'Cross-jurisdiction mapping' },
          { icon: ShieldCheck, label: 'SIGNED CERT', desc: 'Non-repudiable audit trails' }
        ].map((feat, idx) => (
          <motion.div 
            key={feat.label}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.4 + idx * 0.1 }}
            className="p-8 glass hover:bg-foreground/5 transition-all group cursor-default"
          >
            <feat.icon size={24} className="opacity-20 group-hover:opacity-100 group-hover:scale-110 transition-all mb-4" />
            <span className="block font-mono text-[10px] font-bold tracking-[0.2em] mb-2">{feat.label}</span>
            <span className="text-[10px] opacity-40 leading-relaxed font-mono">{feat.desc}</span>
          </motion.div>
        ))}
      </div>
    </div>
  </motion.div>
);

const UploadPage = ({ onNavigate, selectedModel, setSelectedModel }: { onNavigate: (p: Page) => void, selectedModel: string, setSelectedModel: (m: string) => void }) => {
  const [dragActive, setDragActive] = useState(false);
  const models = [
    { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', type: 'Multimodal' },
    { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', type: 'Reasoning' },
    { id: 'gemma-2-27b', name: 'Gemma 2 (27B)', type: 'Open Weights' },
    { id: 'gemma-2-9b', name: 'Gemma 2 (9B)', type: 'Open Weights' },
  ];

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-6xl mx-auto py-24 px-10"
    >
      <div className="mb-20">
        <h2 className="font-serif italic text-6xl mb-6">Ingest Data</h2>
        <div className="h-1.5 w-32 bg-foreground mb-8" />
        <p className="font-mono text-[10px] opacity-40 uppercase tracking-[0.5em]">SPECIFY AUDITOR MODEL & PROTECTED FEATURES</p>
      </div>

      <div className="space-y-16">
        {/* Model Selection Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {models.map((model) => (
            <motion.div 
              key={model.id}
              whileHover={{ y: -4 }}
              onClick={() => setSelectedModel(model.id)}
              className={`p-6 border transition-all cursor-pointer relative overflow-hidden group ${selectedModel === model.id ? 'bg-foreground text-background border-foreground shadow-2xl' : 'glass hover:border-foreground/40'}`}
            >
              <div className={`font-mono text-[9px] uppercase opacity-60 mb-2 ${selectedModel === model.id ? 'text-background/60' : ''}`}>{model.type}</div>
              <div className="font-serif italic text-xl leading-tight mb-4">{model.name}</div>
              <div className={`h-1 w-full bg-current opacity-10 mt-auto ${selectedModel === model.id ? 'opacity-20' : 'group-hover:opacity-30 transition-opacity'}`} />
            </motion.div>
          ))}
        </div>

        <div 
          className={`glass border-dashed border-2 h-96 flex flex-col items-center justify-center transition-all cursor-pointer group ${dragActive ? 'bg-foreground text-background scale-[1.01] border-foreground' : 'hover:border-foreground/60 border-foreground/10'}`}
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => { e.preventDefault(); setDragActive(false); }}
        >
          <div className={`p-6 border rounded-full mb-8 transition-transform group-hover:scale-110 ${dragActive ? 'border-background/20' : 'border-foreground/10'}`}>
            <Upload size={48} className={dragActive ? 'text-background' : 'opacity-30'} />
          </div>
          <p className="font-mono text-xs uppercase tracking-[0.4em] font-bold">DRAG AUDIT SOURCE (CSV / JSONL)</p>
          <span className="text-[10px] opacity-40 mt-4 font-mono italic px-4 py-1 border border-foreground/5">Hiring ● Healthcare ● Finance Domains Supported</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-20">
          <div className="space-y-10 text-left">
            <h4 className="font-mono text-[11px] uppercase tracking-[0.4em] opacity-30 border-b border-foreground/5 pb-4 font-bold">I. Target Integration</h4>
            <div className="space-y-8">
              <div className="group">
                <label className="block font-mono text-[9px] opacity-30 uppercase tracking-widest mb-2 group-focus-within:opacity-100 transition-opacity">Endpoint Configuration</label>
                <input type="text" className="w-full bg-transparent border-b border-foreground/10 py-4 focus:outline-none focus:border-foreground font-mono text-sm placeholder:opacity-10 transition-all" placeholder="https://api.model-provider.com/v1" />
              </div>
              <div className="group">
                <label className="block font-mono text-[9px] opacity-30 uppercase tracking-widest mb-2 group-focus-within:opacity-100 transition-opacity">Access Token</label>
                <input type="password" className="w-full bg-transparent border-b border-foreground/10 py-4 focus:outline-none focus:border-foreground font-mono text-sm placeholder:opacity-10 transition-all font-password" placeholder="••••••••••••••••" />
              </div>
            </div>
          </div>
          <div className="space-y-10 text-left">
            <h4 className="font-mono text-[11px] uppercase tracking-[0.4em] opacity-30 border-b border-foreground/5 pb-4 font-bold">II. Sensitivity Filters</h4>
            <div className="space-y-8">
              <div className="group">
                <label className="block font-mono text-[9px] opacity-30 uppercase tracking-widest mb-2 group-focus-within:opacity-100 transition-opacity">Protected Attributes</label>
                <input type="text" className="w-full bg-transparent border-b border-foreground/10 py-4 focus:outline-none focus:border-foreground font-mono text-sm placeholder:opacity-10 transition-all" placeholder="race, gender, age, disability_status" />
              </div>
              <div className="group">
                <label className="block font-mono text-[9px] opacity-30 uppercase tracking-widest mb-2 group-focus-within:opacity-100 transition-opacity">Target Variable</label>
                <input type="text" className="w-full bg-transparent border-b border-foreground/10 py-4 focus:outline-none focus:border-foreground font-mono text-sm placeholder:opacity-10 transition-all" placeholder="approved_y_n" />
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-between items-center pt-12 border-t border-foreground/5">
          <div className="flex items-center gap-4 font-mono text-[10px] opacity-30">
            <ShieldCheck size={14} /> Encrypted local processing enabled
          </div>
          <Button onClick={() => onNavigate('dashboard')} className="px-16 py-6 text-sm font-bold tracking-widest group">
            BEGIN AUDIT BATTERY <ChevronRight size={18} className="ml-2 group-hover:translate-x-2 transition-transform" />
          </Button>
        </div>
      </div>
    </motion.div>
  );
};


const DashboardPage = ({ onNavigate, selectedModel }: { onNavigate: (p: Page) => void, selectedModel: string }) => {
  const verdict = 'CERTIFIED_FAIR';
  const severityColor = verdict === 'CERTIFIED_FAIR' ? '#10b981' : verdict === 'CERTIFIED_UNFAIR' ? '#ef4444' : '#f59e0b';

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-[1600px] mx-auto pt-10 pb-24 px-12"
    >
      {/* Header Row */}
      <header className="h-24 flex items-center justify-between border-b border-foreground/10 mb-12">
        <div className="flex items-center gap-6">
          <div className="p-3 bg-foreground text-background">
            <ShieldCheck size={32} />
          </div>
          <div>
            <h2 className="font-serif italic text-3xl leading-none">FairGuard Protocol</h2>
            <div className="flex items-center gap-3 mt-1 underline decoration-foreground/20 underline-offset-4">
               <span className="text-[10px] font-mono uppercase tracking-[0.2em] opacity-40">System Audit Registry</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-16 font-mono text-[11px] uppercase tracking-[0.3em]">
          <div className="flex flex-col">
            <span className="opacity-30 mb-1">AUDITOR ENGINE</span>
            <span className="text-foreground font-bold">{selectedModel.toUpperCase()}</span>
          </div>
          <div className="flex flex-col">
            <span className="opacity-30 mb-1">AUDIT_TOKEN</span>
            <span className="text-foreground font-bold">FG-X902-8871</span>
          </div>
          <div className="flex flex-col">
            <span className="opacity-30 mb-1">STATUS</span>
            <span className="text-accent font-bold">VERIFIED</span>
          </div>
        </div>
        <div className="flex gap-4">
          <Button variant="outline" className="px-8" onClick={() => onNavigate('certificate')}>
            <Download size={14} /> EXPORT CERTIFICATE
          </Button>
        </div>
      </header>

      {/* Severity Banner */}
      <motion.div 
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="glass h-32 flex items-center px-12 mb-12 border-l-[16px] shadow-lg shadow-foreground/5" 
        style={{ borderLeftColor: severityColor }}
      >
        <div className="flex-1">
          <div className="flex items-baseline gap-6">
            <h1 className="text-5xl font-serif italic tracking-tight" style={{ color: severityColor }}>{verdict.replace('_', ' ')}</h1>
            <span className="font-mono text-[11px] opacity-40 uppercase tracking-[0.3em]">Temporal Cluster Verification ● April 26, 2026 ● Black-Box (BB)</span>
          </div>
          <p className="text-[12px] font-mono opacity-50 max-w-4xl mt-2 leading-relaxed">
            Audit battery completed across 12,000 synthetic permutations. Causal variance within strict regulatory bounds (δ &lt; 0.05).
          </p>
        </div>
        <div className="flex items-center gap-4 px-8 py-4 bg-foreground/[0.03] font-mono text-[11px] uppercase tracking-[0.2em] font-bold border border-foreground/5 shadow-inner">
          <Activity size={18} className="text-accent" /> Resilience Grade: 87%
        </div>
      </motion.div>

      {/* Grid of 6 Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10 mb-12">
        <Card subtitle="STABILITY PROFILE" title="Cluster Resilience" delay={0.1}>
          <div className="flex items-center justify-center h-full gap-10">
            <div className="relative w-28 h-28 border-[12px] border-foreground/5 shadow-xl flex items-center justify-center font-serif italic text-5xl">
              B+
              <div className="absolute -bottom-2 -right-2 p-1 bg-foreground text-background">
                <ShieldCheck size={12} />
              </div>
            </div>
            <div className="flex-1 flex flex-col justify-center gap-3">
              {[0.92, 0.74, 0.88, 0.96, 0.82, 0.89].map((val, i) => (
                <div key={i} className="flex flex-col gap-1">
                  <div className="h-1.5 w-full bg-foreground/5 overflow-hidden">
                    <motion.div 
                      initial={{ width: 0 }}
                      animate={{ width: `${val * 100}%` }}
                      transition={{ delay: 0.8 + i * 0.1, duration: 1.2, ease: "circOut" }}
                      className="h-full bg-foreground/60 transition-colors hover:bg-accent"
                    />
                  </div>
                </div>
              ))}
              <span className="text-[9px] font-mono opacity-40 uppercase tracking-[0.2em] mt-2">Multivariate Stability Distribution</span>
            </div>
          </div>
        </Card>

        {['Race', 'Gender', 'Age'].map((dim, idx) => (
          <Card key={dim} subtitle={`CAUSAL — ${dim.toUpperCase()}`} title="Demographic Variance" delay={0.2 + idx * 0.1}>
            <div className="h-full pt-6 min-h-0">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={dim === 'Race' ? CAUSAL_RACE : dim === 'Gender' ? CAUSAL_GENDER : CAUSAL_AGE} layout="vertical" margin={{ left: -20, right: 30 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="currentColor" style={{ opacity: 0.05 }} />
                  <XAxis type="number" hide domain={[-0.1, 0.3]} />
                  <YAxis dataKey="name" type="category" tick={{ fontSize: 10, fontFamily: 'monospace', opacity: 0.3 }} width={60} axisLine={false} tickLine={false} />
                  <Tooltip cursor={{ fill: 'currentColor', opacity: 0.03 }} contentStyle={{ backgroundColor: 'var(--color-card)', border: '1px solid var(--color-border)', fontSize: '10px', fontFamily: 'monospace' }} />
                  <Bar dataKey="value" fill="currentColor" barSize={14} radius={[0, 4, 4, 0]}>
                    <ErrorBar dataKey="low" stroke="currentColor" strokeWidth={1} width={4} opacity={0.3} />
                    <ErrorBar dataKey="high" stroke="currentColor" strokeWidth={1} width={4} opacity={0.3} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        ))}

        <Card subtitle="NYC LOCAL LAW 144" title="Impact Ratio Variance" delay={0.5}>
          <Gauge value={0.8422} label="Variance Coefficient" threshold={0.8} />
        </Card>

        <Card subtitle="MECHANISTIC" title="Circuit Extraction" delay={0.6}>
          <div className="opacity-10 h-full flex flex-col justify-center items-center gap-6 grayscale">
            <Settings size={48} className="animate-spin-slow" />
            <div className="text-center">
              <p className="font-mono text-[10px] uppercase tracking-[0.5em] mb-2 font-bold">White-Box Layer Restricted</p>
              <p className="text-[8px] font-mono opacity-60">Upgrade to Guardian-Grade access for SAE weight interpretation</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Drift Chart */}
      <motion.div 
        initial={{ y: 20, opacity: 0 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ delay: 0.7 }}
        className="w-full bg-foreground/[0.02] border border-foreground/10 p-12 h-[450px] relative group"
      >
        <div className="absolute top-8 left-12">
          <h3 className="font-mono text-[11px] uppercase opacity-40 tracking-[0.4em] mb-2">Temporal Dynamics</h3>
          <h2 className="font-serif italic text-3xl">30-Day Decision Drift Profile</h2>
        </div>
        <div className="h-full pt-20 min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={DRIFT_DATA} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorDrift" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="currentColor" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="currentColor" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" style={{ opacity: 0.05 }} />
              <XAxis dataKey="day" tick={{ fontSize: 10, fontFamily: 'monospace', opacity: 0.3 }} axisLine={false} tickLine={false} />
              <YAxis domain={[0, 1]} tick={{ fontSize: 10, fontFamily: 'monospace', opacity: 0.3 }} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ stroke: 'currentColor', strokeWidth: 1, strokeDasharray: '4 4' }} contentStyle={{ backgroundColor: 'var(--color-card)', border: '1px solid var(--color-border)', fontSize: '10px', fontFamily: 'monospace' }} />
              <Area type="monotone" dataKey="drift" stroke="currentColor" fillOpacity={1} fill="url(#colorDrift)" strokeWidth={2} />
              <Line type="monotone" dataKey="drift" stroke="currentColor" strokeWidth={0} dot={(props: any) => {
                if (props.payload.alert) {
                  return <circle cx={props.cx} cy={props.cy} r={5} fill="#ef4444" stroke="var(--color-background)" strokeWidth={2} key={props.index} />;
                }
                return <></>;
              }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </motion.div>

      {/* Footer Badges */}
      <footer className="h-24 flex items-center justify-between mt-12 opacity-80 border-t border-foreground/5">
        <div className="flex gap-10">
          {[
            { label: 'EU AI ACT', status: 'PASS' },
            { label: 'NYC LL 144', status: 'PASS' },
            { label: 'COLORADO SB21-169', status: 'PENDING' }
          ].map(badge => (
            <div key={badge.label} className="flex items-center gap-4 font-mono text-[11px] uppercase tracking-[0.2em] px-6 py-3 border border-foreground/5 hover:border-foreground/20 transition-colors">
               <span className="opacity-30">{badge.label}:</span>
               <span className={`font-bold ${badge.status === 'PASS' ? 'text-accent' : 'text-amber-500'}`}>{badge.status}</span>
            </div>
          ))}
        </div>
        <div className="font-mono text-[9px] uppercase tracking-[0.3em] opacity-30 text-right">
          Cryptographic Attestation v4.1.2<br/>Distributed via FairGuard Protocol
        </div>
      </footer>
    </motion.div>
  );
};

const CertificatePage = ({ onNavigate, selectedModel }: { onNavigate: (p: Page) => void, selectedModel: string }) => (
  <motion.div 
    initial={{ opacity: 0, scale: 0.98 }}
    animate={{ opacity: 1, scale: 1 }}
    className="max-w-5xl mx-auto py-20 px-20 glass my-16 relative overflow-hidden shadow-2xl"
  >
    {/* Archival Decorative Elements */}
    <div className="absolute top-0 left-0 w-full h-3 bg-foreground/10" />
    <div className="absolute -top-20 -right-20 opacity-[0.03] pointer-events-none rotate-12">
      <ShieldCheck size={500} />
    </div>

    <div className="flex justify-between items-start mb-32 relative z-10">
      <div className="flex items-center gap-6">
        <div className="p-3 bg-foreground text-background">
          <ShieldCheck size={32} />
        </div>
        <div>
          <h2 className="font-serif italic text-3xl leading-none">FairGuard</h2>
          <p className="font-mono text-[11px] opacity-40 uppercase tracking-[0.4em] mt-1">Verification Registry</p>
        </div>
      </div>
      <div className="text-right">
        <div className="font-mono text-[10px] opacity-40 uppercase tracking-[0.3em] mb-2">VALIDATION TIMESTAMP</div>
        <div className="font-mono text-[13px] font-bold">2026-04-26 T13:11:18Z</div>
      </div>
    </div>

    <div className="text-center mb-24 relative z-10">
      <div className="font-mono text-[11px] uppercase tracking-[0.7em] mb-10 opacity-40">Certificate of Algorithmic Integrity</div>
      <h1 className="font-serif italic text-9xl mb-10 tracking-tighter">Fairness Verdict</h1>
      <div className="h-1 w-64 bg-foreground mx-auto mb-10 opacity-10" />
      <div className="inline-block px-12 py-5 border-[3px] border-accent text-accent font-mono text-sm uppercase tracking-[0.5em] font-bold bg-accent/5 shadow-2xl shadow-accent/20">
        Outcome: Certified Fair
      </div>
    </div>

    <div className="mb-24 flex justify-center relative z-10">
      <div className="grid grid-cols-2 gap-20 w-full border-y border-foreground/5 py-12">
        <div className="flex flex-col items-center">
          <span className="font-mono text-[10px] opacity-30 uppercase tracking-[0.4em] mb-3">AUDITOR_MODEL</span>
          <span className="font-serif italic text-3xl">{selectedModel}</span>
        </div>
        <div className="flex flex-col items-center">
          <span className="font-mono text-[10px] opacity-30 uppercase tracking-[0.4em] mb-3">CRYPTOGRAPHIC_ID</span>
          <span className="font-mono text-[13px] font-bold tracking-widest underline decoration-foreground/10 decoration-wavy underline-offset-8">FG-X902-8871-AF92</span>
        </div>
      </div>
    </div>

    <div className="grid grid-cols-2 gap-32 mb-32 relative z-10">
      <div className="space-y-16">
        <div className="relative pl-10 border-l-[3px] border-accent/20">
          <h4 className="font-mono text-[11px] uppercase tracking-[0.4em] mb-6 opacity-40 font-bold underline decoration-accent/30 underline-offset-4">I. Causal Robustness</h4>
          <p className="text-[15px] leading-relaxed opacity-80 italic font-serif text-justify">
            "Subject model satisfies the Independent Causal Divergence threshold (δ &lt; 0.05). Under multivariate perturbation battery, protected attributes remain statistically decoupled from final prediction circuits beyond noise thresholds."
          </p>
        </div>
        
        <div className="relative pl-10 border-l-[3px] border-accent/20">
          <h4 className="font-mono text-[11px] uppercase tracking-[0.4em] mb-6 opacity-40 font-bold underline decoration-accent/30 underline-offset-4">II. Stability Index</h4>
          <p className="text-[15px] leading-relaxed opacity-80 italic font-serif text-justify">
            "Perturbation metrics indicate a global stability coefficient of 0.87. Prediction artifacts are bounded and non-propagating across synthetic outliers and minority clusters."
          </p>
        </div>
      </div>

      <div className="bg-foreground/[0.03] p-12 relative shadow-inner border border-foreground/5">
        <h4 className="font-mono text-[11px] uppercase tracking-[0.4em] mb-8 opacity-40 font-bold border-b border-foreground/10 pb-4">Regulatory Registry Mapping</h4>
        <table className="w-full font-mono text-[11px]">
          <tbody>
            {[
              { reg: 'NYC Local Law 144', status: 'PASS' },
              { reg: 'Colorado SB21-169', status: 'PASS' },
              { reg: 'EU AI Act (Art. 10)', status: 'PASS' },
              { reg: 'IEEE 7000-2021', status: 'PASS' }
            ].map((row, i) => (
              <tr key={i} className="border-b border-foreground/5">
                <td className="py-4 opacity-70 uppercase tracking-tighter">{row.reg}</td>
                <td className="py-4 text-right font-bold text-accent">[{row.status}]</td>
              </tr>
            ))}
          </tbody>
        </table>
        
        <div className="mt-16 pt-16 border-t border-foreground/10 text-center relative overflow-hidden">
            <div className="absolute -bottom-10 -right-10 opacity-[0.05]">
                <ShieldCheck size={120} />
            </div>
            <div className="inline-block p-6 border-2 border-foreground/10 mb-6 scale-90 opacity-20 relative z-10">
                <ShieldCheck size={80} />
            </div>
            <div className="font-mono text-[10px] opacity-40 uppercase tracking-[0.3em] leading-relaxed relative z-10">
                Non-Repudiable Signature<br/>
                <span className="text-foreground tracking-widest font-bold">FAIRGUARD-AUTH-A9D2-CC81-9021</span>
            </div>
        </div>
      </div>
    </div>

    <div className="flex justify-between items-end border-t border-foreground/5 pt-16 relative z-10">
      <Button onClick={() => onNavigate('dashboard')} variant="ghost" className="text-[11px] opacity-40 hover:opacity-100 uppercase tracking-widest group">
        <ChevronRight className="rotate-180 mr-4 group-hover:-translate-x-2 transition-transform" size={16} /> Return to Audit Center
      </Button>
      <div className="font-mono text-[9px] opacity-20 text-right uppercase tracking-[0.4em] leading-loose">
        Verification successful / Node 0492 / Cluster δ<br/>
        Valid only via Protocol 4.1 Attestation
      </div>
    </div>
  </motion.div>
);


// --- Root Component ---

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('home');
  const [theme, setTheme] = useState<Theme>('light');
  const [selectedModel, setSelectedModel] = useState<string>('gemini-2.0-flash');

  useEffect(() => {
    const savedTheme = getCookie('fairguard_theme') as Theme;
    if (savedTheme) {
      setTheme(savedTheme);
      document.documentElement.classList.toggle('dark', savedTheme === 'dark');
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    setCookie('fairguard_theme', newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-background text-foreground transition-colors duration-500 selection:bg-foreground selection:text-background font-sans overflow-hidden">
      {/* SVG Filters for UI Textures */}
      <svg className="absolute w-0 h-0 invisible pointer-events-none">
        <filter id="noiseFilter">
          <feTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
      </svg>

      <nav className="w-full lg:w-28 lg:h-screen lg:border-r border-b border-foreground/10 flex lg:flex-col items-center justify-between p-8 z-50 bg-background/80 backdrop-blur-xl lg:fixed lg:left-0 lg:top-0">
        <div 
          className="cursor-pointer hover:scale-110 transition-transform p-3 bg-foreground text-background"
          onClick={() => setCurrentPage('home')}
        >
          <ShieldCheck size={32} />
        </div>
        
        <div className="flex lg:flex-col gap-12">
          {[
            { id: 'upload', icon: Upload, label: 'Audit' },
            { id: 'dashboard', icon: BarChart3, label: 'Logs' },
            { id: 'certificate', icon: FileText, label: 'Cert' }
          ].map((item) => (
            <div 
              key={item.id}
              onClick={() => setCurrentPage(item.id as Page)}
              className={`group flex flex-col items-center gap-3 cursor-pointer transition-all relative ${currentPage === item.id ? 'opacity-100 scale-110' : 'opacity-20 hover:opacity-60'}`}
            >
              <item.icon size={26} className={currentPage === item.id ? 'text-accent' : ''} />
              <span className="font-mono text-[9px] uppercase tracking-[0.3em] font-bold hidden lg:block opacity-0 group-hover:opacity-100 transition-all absolute -right-32 bg-foreground text-background px-4 py-2 pointer-events-none shadow-2xl skew-x-[-10deg] border border-border">
                {item.label}
              </span>
              {currentPage === item.id && (
                <motion.div 
                  layoutId="active-nav-indicator"
                  className="absolute -left-8 w-1.5 h-10 bg-accent rounded-r-full hidden lg:block shadow-[0_0_15px_rgba(16,185,129,0.5)]" 
                />
              )}
            </div>
          ))}
        </div>

        <div className="flex lg:flex-col gap-8 items-center">
           <button 
            onClick={toggleTheme}
            className="p-4 border border-foreground/10 hover:border-foreground transition-all rounded-full group bg-foreground/5 shadow-inner"
          >
            {theme === 'light' ? <Moon size={20} className="group-hover:rotate-[-20deg] transition-transform" /> : <Sun size={20} className="group-hover:rotate-90 transition-transform" />}
          </button>
        </div>
      </nav>

      <main className="flex-1 lg:ml-28 overflow-y-auto min-h-screen tech-grid p-6 lg:p-0">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentPage}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.5, ease: [0.23, 1, 0.32, 1] }}
            className="min-h-full"
          >
            {currentPage === 'home' && <HomePage onNavigate={setCurrentPage} />}
            {currentPage === 'upload' && <UploadPage onNavigate={setCurrentPage} selectedModel={selectedModel} setSelectedModel={setSelectedModel} />}
            {currentPage === 'dashboard' && <DashboardPage onNavigate={setCurrentPage} selectedModel={selectedModel} />}
            {currentPage === 'certificate' && <CertificatePage onNavigate={setCurrentPage} selectedModel={selectedModel} />}
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
