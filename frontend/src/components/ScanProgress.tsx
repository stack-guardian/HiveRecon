import React from 'react';
import { useScanSocket } from '../hooks/useScanSocket';

interface ScanProgressProps {
  scanId: string;
}

const ScanProgress: React.FC<ScanProgressProps> = ({ scanId }) => {
  const { stage, pct, message, findingsCount, isComplete, error } = useScanSocket(scanId);

  const getStageLabel = (stageStr: string) => {
    switch (stageStr) {
      case 'subdomain_enum': return 'Subdomain Discovery';
      case 'port_scan': return 'Port Scanning';
      case 'endpoint_discovery': return 'Endpoint Discovery';
      case 'vuln_scan': return 'Vulnerability Scanning (Nuclei)';
      case 'correlation': return 'AI Correlation & Enrichment';
      case 'complete': return 'Scan Complete';
      default: return stageStr.charAt(0).toUpperCase() + stageStr.slice(1);
    }
  };

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/50 p-4 rounded-lg text-red-200">
        <p className="font-bold">WebSocket Error</p>
        <p className="text-sm">{error}</p>
      </div>
    );
  }

  return (
    <div className="bg-zinc-900/80 border border-zinc-800 p-6 rounded-xl shadow-2xl backdrop-blur-sm">
      <div className="flex justify-between items-end mb-4">
        <div>
          <h3 className="text-zinc-400 text-sm font-medium uppercase tracking-wider mb-1">Current Stage</h3>
          <p className="text-xl font-bold text-zinc-100 flex items-center">
            {getStageLabel(stage)}
            {!isComplete && (
              <span className="ml-2 flex h-2 w-2 rounded-full bg-indigo-500 animate-pulse"></span>
            )}
          </p>
        </div>
        <div className="text-right">
          <p className="text-3xl font-mono font-bold text-indigo-400">{pct}%</p>
        </div>
      </div>

      <div className="relative h-3 w-full bg-zinc-800 rounded-full overflow-hidden mb-6">
        <div 
          className="absolute top-0 left-0 h-full bg-gradient-to-r from-indigo-600 to-violet-500 transition-all duration-500 ease-out shadow-[0_0_15px_rgba(99,102,241,0.5)]"
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-zinc-950/50 p-3 rounded-lg border border-zinc-800/50">
          <p className="text-zinc-500 text-xs uppercase mb-1">Findings Discovered</p>
          <p className="text-2xl font-bold text-emerald-400">{findingsCount}</p>
        </div>
        <div className="bg-zinc-950/50 p-3 rounded-lg border border-zinc-800/50">
          <p className="text-zinc-500 text-xs uppercase mb-1">Status</p>
          <p className="text-sm text-zinc-300 truncate" title={message}>
            {message}
          </p>
        </div>
      </div>

      {isComplete && (
        <div className="mt-6 flex justify-center">
          <div className="px-4 py-1.5 bg-emerald-900/30 text-emerald-400 text-xs font-bold rounded-full border border-emerald-500/30 animate-in fade-in zoom-in duration-500">
            PIPELINE COMPLETE
          </div>
        </div>
      )}
    </div>
  );
};

export default ScanProgress;
