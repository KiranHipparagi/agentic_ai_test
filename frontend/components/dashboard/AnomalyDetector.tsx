"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, TrendingDown, TrendingUp, Zap } from "lucide-react";

interface Anomaly {
  id: string;
  type: "spike" | "drop" | "unusual" | "critical";
  metric: string;
  value: string;
  deviation: string;
  timestamp: Date;
}

export default function AnomalyDetector() {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);

  useEffect(() => {
    detectAnomalies();
    const interval = setInterval(detectAnomalies, 20000); // Check every 20s
    return () => clearInterval(interval);
  }, []);

  const detectAnomalies = () => {
    const detectedAnomalies: Anomaly[] = [];

    // Simulate anomaly detection
    if (Math.random() > 0.7) {
      detectedAnomalies.push({
        id: `anom-${Date.now()}-1`,
        type: "spike",
        metric: "Sales Velocity",
        value: "+347%",
        deviation: "3.2σ above normal",
        timestamp: new Date()
      });
    }

    if (Math.random() > 0.6) {
      detectedAnomalies.push({
        id: `anom-${Date.now()}-2`,
        type: "drop",
        metric: "Customer Traffic",
        value: "-28%",
        deviation: "2.1σ below normal",
        timestamp: new Date()
      });
    }

    if (Math.random() > 0.8) {
      detectedAnomalies.push({
        id: `anom-${Date.now()}-3`,
        type: "critical",
        metric: "Inventory Turnover",
        value: "0.3x",
        deviation: "Critical threshold",
        timestamp: new Date()
      });
    }

    if (Math.random() > 0.75) {
      detectedAnomalies.push({
        id: `anom-${Date.now()}-4`,
        type: "unusual",
        metric: "Avg Order Value",
        value: "$342",
        deviation: "Unusual pattern",
        timestamp: new Date()
      });
    }

    setAnomalies(detectedAnomalies.slice(0, 5));
  };

  const getAnomalyStyle = (type: Anomaly["type"]) => {
    switch (type) {
      case "spike":
        return {
          bg: "bg-green-50",
          border: "border-green-200",
          text: "text-green-700",
          icon: TrendingUp,
          iconColor: "text-green-600"
        };
      case "drop":
        return {
          bg: "bg-red-50",
          border: "border-red-200",
          text: "text-red-700",
          icon: TrendingDown,
          iconColor: "text-red-600"
        };
      case "critical":
        return {
          bg: "bg-red-100",
          border: "border-red-300",
          text: "text-red-800",
          icon: AlertTriangle,
          iconColor: "text-red-700"
        };
      case "unusual":
        return {
          bg: "bg-amber-50",
          border: "border-amber-200",
          text: "text-amber-700",
          icon: Zap,
          iconColor: "text-amber-600"
        };
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-4 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-900">Anomaly Detection</h3>
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Zap className="w-3 h-3 text-yellow-500 animate-pulse" />
          Live Monitoring
        </div>
      </div>

      <div className="space-y-2 max-h-64 overflow-auto">
        {anomalies.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-xs">No anomalies detected</p>
          </div>
        ) : (
          anomalies.map((anomaly) => {
            const style = getAnomalyStyle(anomaly.type);
            const Icon = style.icon;

            return (
              <div
                key={anomaly.id}
                className={`${style.bg} ${style.border} border rounded-lg p-3 transition-all hover:shadow-md`}
              >
                <div className="flex items-start gap-2">
                  <Icon className={`w-4 h-4 ${style.iconColor} flex-shrink-0 mt-0.5`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className={`text-xs font-semibold ${style.text}`}>
                        {anomaly.metric}
                      </p>
                      <span className={`text-xs font-bold ${style.text}`}>
                        {anomaly.value}
                      </span>
                    </div>
                    <p className="text-xs text-gray-600">{anomaly.deviation}</p>
                    <p className="text-xs text-gray-400 mt-1">
                      {anomaly.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
