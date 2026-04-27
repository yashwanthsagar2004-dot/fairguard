import React from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceArea } from "recharts";

const DriftDashboard = ({ audit_id, history }) => {
  if (!history || history.length === 0) {
    return (
      <div className="p-6 bg-gray-900 rounded-lg border border-dashed border-gray-700 text-center">
        <h3 className="text-xl font-semibold text-white mb-2">No Drift Monitor Registered</h3>
        <p className="text-gray-400 mb-4">Longitudinal fairness monitoring is not active for this audit.</p>
        <button className="px-6 py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors">
          Register Drift Monitor
        </button>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-900 rounded-xl border border-gray-800 shadow-2xl">
      <h2 className="text-2xl font-bold text-white mb-6">Longitudinal Fairness Drift (30 Days)</h2>
      <div className="h-80 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={history}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey="date" stroke="#888" />
            <YAxis stroke="#888" />
            <Tooltip 
              contentStyle={{ backgroundColor: "#111", border: "#333", borderRadius: "8px" }}
              itemStyle={{ color: "#fff" }}
            />
            <Legend />
            {/* 2 Sigma Band Placeholder */}
            <ReferenceArea y1={0} y2={0.1} fill="#fbbf24" fillOpacity={0.1} />
            <Line type="monotone" dataKey="dp_diff" name="DP Diff" stroke="#3b82f6" strokeWidth={3} dot={false} />
            <Line type="monotone" dataKey="eo_gap" name="EO Gap" stroke="#a855f7" strokeWidth={3} dot={false} />
            <Line type="monotone" dataKey="impact_ratio" name="Impact Ratio" stroke="#10b981" strokeWidth={3} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 grid grid-cols-3 gap-4">
        <div className="p-4 bg-gray-800 rounded-lg">
          <p className="text-sm text-gray-400">Demographic Parity</p>
          <p className="text-xl font-bold text-blue-400">{history[history.length-1].dp_diff.toFixed(3)}</p>
        </div>
        <div className="p-4 bg-gray-800 rounded-lg">
          <p className="text-sm text-gray-400">Equalized Odds</p>
          <p className="text-xl font-bold text-purple-400">{history[history.length-1].eo_gap.toFixed(3)}</p>
        </div>
        <div className="p-4 bg-gray-800 rounded-lg">
          <p className="text-sm text-gray-400">Impact Ratio</p>
          <p className="text-xl font-bold text-emerald-400">{history[history.length-1].impact_ratio.toFixed(3)}</p>
        </div>
      </div>
    </div>
  );
};

export default DriftDashboard;
