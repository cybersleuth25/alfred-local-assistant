import { useEffect, useState, useRef } from 'react'
import ShaderBackground from './components/ui/shader-background'
import CommandCenter from './components/CommandCenter'
import './index.css'

type AppState = "idle" | "listening" | "processing" | "speaking";

interface TranscriptLine {
  author: string;
  text: string;
  id: number;
}

interface NowPlayingData {
  song: string;
  artist: string;
  playing: boolean;
}

function App() {
  const [orbState, setOrbState] = useState<AppState>("idle");
  const [commandCenter, setCommandCenter] = useState(false);
  const [caption, setCaption] = useState("");
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [connected, setConnected] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [nowPlaying, setNowPlaying] = useState<NowPlayingData | null>(null);
  const [mood, setMood] = useState("standby");
  const [commandCount, setCommandCount] = useState(0);
  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const lineIdRef = useRef(0);
  const idleTimerRef = useRef(0);

  // Clock
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Mood tracker
  useEffect(() => {
    if (orbState === 'processing' || orbState === 'listening') {
      setCommandCount(c => c + 1);
      idleTimerRef.current = 0;
    }
  }, [orbState]);

  useEffect(() => {
    const moodTimer = setInterval(() => {
      idleTimerRef.current += 1;
      if (idleTimerRef.current > 120) setMood("dormant");
      else if (idleTimerRef.current > 60) setMood("idle");
      else if (commandCount > 10) setMood("engaged");
      else setMood("standby");
    }, 1000);
    return () => clearInterval(moodTimer);
  }, [commandCount]);

  // Spotify Now Playing
  useEffect(() => {
    const fetchNowPlaying = async () => {
      try {
        const r = await fetch('/api/spotify/now_playing');
        const d = await r.json();
        if (d && d.song && d.playing) setNowPlaying(d);
        else setNowPlaying(null);
      } catch { setNowPlaying(null); }
    };
    fetchNowPlaying();
    const interval = setInterval(fetchNowPlaying, 8000);
    return () => clearInterval(interval);
  }, []);

  // SSE Stream
  useEffect(() => {
    const evtSource = new EventSource("/stream");
    
    evtSource.onopen = () => setConnected(true);
    evtSource.onerror = () => setConnected(false);
    
    evtSource.onmessage = function(event) {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'state') {
          setOrbState(data.value as AppState);
        } else if (data.type === 'caption') {
          setCaption(data.value || "");
        } else if (data.type === 'transcript') {
          lineIdRef.current += 1;
          setTranscript(prev => {
            const updated = [...prev, { author: data.author, text: data.value, id: lineIdRef.current }];
            return updated.slice(-50);
          });
        }
      } catch (e) {}
    };

    return () => evtSource.close();
  }, []);

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [transcript]);

  const formatTime = (d: Date) => {
    return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false });
  };

  const formatDate = (d: Date) => {
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  const moodLabel = mood === 'engaged' ? 'ENGAGED' : mood === 'dormant' ? 'DORMANT' : mood === 'idle' ? 'IDLE' : 'STANDBY';

  // State accent color for bottom bar
  const stateColor = orbState === 'listening' ? '#14b8a6'
    : orbState === 'processing' ? '#f59e0b'
    : orbState === 'speaking' ? '#8b5cf6'
    : '#71717a';

  return (
    <div className="w-screen h-screen bg-cinematic flex flex-col items-center justify-center relative overflow-hidden font-sans text-white">

      <CommandCenter active={commandCenter} />

      {/* ── Top Bar ── */}
      <div className="absolute top-0 left-0 right-0 z-40 pointer-events-auto px-8 py-5 flex items-center justify-between border-b border-[#27272a] bg-[#09090b]/80 backdrop-blur-sm">
        
        {/* Left: Brand + Link Status + Mood */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className={`w-2 h-2 rounded-full transition-colors duration-500 ${
              connected ? 'bg-[#14b8a6] status-breathe' : 'bg-red-500'
            }`} />
            <span className="text-[11px] tracking-[0.1em] text-[#f4f4f5] font-semibold uppercase">Alfred</span>
          </div>
          <div className="w-px h-4 bg-[#27272a]"></div>
          <span className={`text-[10px] tracking-[0.1em] font-medium uppercase transition-colors duration-500 ${
            connected ? 'text-[#14b8a6]' : 'text-red-500'
          }`}>{connected ? 'LINK' : 'OFFLINE'}</span>
          <div className="w-px h-4 bg-[#27272a]"></div>
          <span className="text-[10px] tracking-[0.1em] text-[#71717a] font-medium uppercase">{moodLabel}</span>
        </div>

        {/* Center: Command Center toggle */}
        <button 
          onClick={() => setCommandCenter(!commandCenter)}
          className={`px-6 py-2 text-[10px] tracking-[0.1em] font-medium rounded-md transition-all duration-300 border ${
            commandCenter 
            ? 'bg-[#27272a] text-[#f4f4f5] border-[#52525b]'
            : 'bg-transparent text-[#a1a1aa] border-[#27272a] hover:bg-[#18181b]'
          }`}
        >
          {commandCenter ? 'CLOSE DASHBOARD' : 'OPEN DASHBOARD'}
        </button>

        {/* Right: Clock */}
        <div className="text-right flex items-center gap-3">
          <div className="text-[11px] text-[#71717a] font-medium uppercase">{formatDate(currentTime)}</div>
          <div className="w-px h-4 bg-[#27272a]"></div>
          <div className="text-[13px] font-mono text-[#f4f4f5] font-medium tabular-nums">{formatTime(currentTime)}</div>
        </div>
      </div>

      {/* ── Sentinel 3D Crystal ── */}
      <div className={`absolute inset-0 pointer-events-none flex items-center justify-center transition-all duration-[800ms] ease-[cubic-bezier(0.16,1,0.3,1)] ${
        commandCenter 
          ? 'scale-[0.95] opacity-40 z-0' 
          : 'scale-100 opacity-100 z-20' 
      }`}>
        <ShaderBackground state={orbState} />
        {/* Protocol Watermark */}
        {!commandCenter && (
          <div className="absolute bottom-[18vh] left-1/2 -translate-x-1/2 z-25">
            <div className="text-[9px] tracking-[0.5em] text-white/10 font-light uppercase sentinel-watermark">Alfred Protocol</div>
          </div>
        )}
      </div>

      {/* ── Caption Overlay ── */}
      {caption && !commandCenter && (
        <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-30 max-w-2xl px-8">
          <div className="caption-container">
            <div className="sentinel-caption text-center text-[13px] font-light leading-relaxed tracking-wide">
              {caption}
            </div>
          </div>
        </div>
      )}

      {/* ── Spotify Now Playing — bottom left ── */}
      {nowPlaying && !commandCenter && (
        <div className="absolute bottom-[80px] left-8 z-30 flex items-center gap-4 px-4 py-3 rounded-lg bg-[#18181b] border border-[#27272a] shadow-sm animate-fade-in">
          {/* Equalizer bars */}
          <div className="flex items-end h-4 gap-0.5">
            <span className="eq-bar"></span>
            <span className="eq-bar"></span>
            <span className="eq-bar"></span>
            <span className="eq-bar"></span>
          </div>
          <div>
            <div className="text-[12px] text-[#f4f4f5] font-medium truncate max-w-[180px]">{nowPlaying.song}</div>
            <div className="text-[10px] text-[#a1a1aa] truncate max-w-[180px] mt-0.5">{nowPlaying.artist}</div>
          </div>
        </div>
      )}

      {/* ── Bottom Bar: Status + Transcript ── */}
      <div className={`absolute bottom-0 left-0 right-0 z-40 transition-all duration-700 bg-[#09090b]/80 backdrop-blur-sm border-t border-[#27272a] ${commandCenter ? 'opacity-0 translate-y-full' : 'opacity-100'}`}>
        <div className="px-8 py-3 flex items-center justify-between">
          
          {/* Left: State indicator */}
          <div className="flex items-center gap-4">
            <div className="text-[10px] text-[#71717a] font-medium uppercase">System Status</div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full" style={{ backgroundColor: stateColor }} />
              <div className="text-[12px] font-semibold uppercase tracking-wider transition-colors duration-500" style={{ color: stateColor }}>
                {orbState}
              </div>
            </div>
          </div>

          {/* Right: Mini transcript log */}
          <div className="max-w-md w-96 max-h-16 overflow-hidden">
            <div className="flex flex-col justify-end h-full">
              {transcript.slice(-2).map((line) => (
                <div key={line.id} className="text-[11px] leading-relaxed animate-fade-in flex gap-3">
                  <span className={`shrink-0 font-medium w-8 ${
                    line.author === 'User' ? 'text-[#14b8a6]' : line.author === 'Alfred' ? 'text-[#f4f4f5]' : 'text-[#f59e0b]'
                  }`}>{line.author === 'User' ? 'YOU' : line.author === 'Alfred' ? 'ALF' : 'SYS'}</span>
                  <span className="text-[#a1a1aa] truncate">{line.text}</span>
                </div>
              ))}
              <div ref={transcriptEndRef} />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
