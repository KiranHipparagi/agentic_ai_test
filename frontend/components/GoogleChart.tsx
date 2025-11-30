"use client";

import { useEffect, useRef, useState } from "react";

interface GoogleChartProps {
  chartConfig: any;
}

declare global {
  interface Window {
    google: any;
  }
}

export default function GoogleChart({ chartConfig }: GoogleChartProps) {
  const chartRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load Google Charts
    if (!window.google) {
      const script = document.createElement('script');
      script.src = 'https://www.gstatic.com/charts/loader.js';
      script.onload = () => {
        window.google.charts.load('current', { packages: ['corechart', 'geochart'] });
        window.google.charts.setOnLoadCallback(() => drawChart());
      };
      document.head.appendChild(script);
    } else {
      if (window.google.visualization) {
        drawChart();
      } else {
        window.google.charts.setOnLoadCallback(() => drawChart());
      }
    }
  }, [chartConfig]);

  const drawChart = () => {
    if (!chartRef.current || !chartConfig) return;

    try {
      setLoading(true);
      setError(null);

      const { chartType, data, options } = chartConfig;

      console.log('🎨 Drawing chart:', { chartType, rows: data?.length });

      // Validate data
      if (!data || !Array.isArray(data) || data.length < 2) {
        throw new Error('Invalid data format');
      }

      // Create DataTable
      const dataTable = window.google.visualization.arrayToDataTable(data);

      // Create chart based on type
      let chart;
      const actualChartType = chartType;  // Use the actual chart type from backend
      
      switch (actualChartType) {
        case 'BarChart':
          chart = new window.google.visualization.BarChart(chartRef.current);
          break;
        case 'ColumnChart':
          chart = new window.google.visualization.ColumnChart(chartRef.current);
          break;
        case 'LineChart':
          chart = new window.google.visualization.LineChart(chartRef.current);
          break;
        case 'PieChart':
          chart = new window.google.visualization.PieChart(chartRef.current);
          break;
        case 'ScatterChart':
          chart = new window.google.visualization.ScatterChart(chartRef.current);
          break;
        case 'GeoChart':
          chart = new window.google.visualization.GeoChart(chartRef.current);
          break;
        case 'AreaChart':
          chart = new window.google.visualization.AreaChart(chartRef.current);
          break;
        case 'Table':
          chart = new window.google.visualization.Table(chartRef.current);
          break;
        default:
          console.warn(`Unknown chart type: ${actualChartType}, defaulting to ColumnChart`);
          chart = new window.google.visualization.ColumnChart(chartRef.current);
      }

      // ✅ ENHANCED: Larger chart with better spacing
      const finalOptions = {
        ...options,
        backgroundColor: 'transparent',
        fontName: 'Inter, system-ui, sans-serif',
        fontSize: 14,
        // Remove explicit width/height strings as they can cause issues
        // width: '100%', 
        // height: '100%',
        animation: {
          startup: true,
          duration: 500,
          easing: 'out'
        },
        tooltip: {
          textStyle: { fontSize: 14 },
          showColorCode: true
        },
        // ✅ Maximum chart area - Full size with minimal padding
        chartArea: {
          width: '95%',
          height: '88%',
          top: 10,
          left: 'auto',
          right: 'auto',
          bottom: 'auto',
          ...(options?.chartArea || {})
        },
        // Larger legend
        legend: {
          textStyle: { fontSize: 14 },
          alignment: 'center',
          position: 'bottom',
          ...(options?.legend || {})
        },
        // Larger axis labels
        hAxis: {
          textStyle: { fontSize: 14 },
          titleTextStyle: { fontSize: 16 },
          ...(options?.hAxis || {})
        },
        vAxis: {
          textStyle: { fontSize: 14 },
          titleTextStyle: { fontSize: 16 },
          ...(options?.vAxis || {})
        },
        // GeoChart specific
        ...(actualChartType === 'GeoChart' && {
          region: 'US',
          displayMode: 'regions',
          resolution: 'provinces',
          colorAxis: { colors: ['#D1FAE5', '#10B981', '#065F46'] },
          backgroundColor: 'transparent',
          datalessRegionColor: '#E5E7EB',
          defaultColor: '#10B981'
        })
      };

      // Draw chart
      chart.draw(dataTable, finalOptions);

      console.log('✅ Chart drawn successfully!');
      setLoading(false);

    } catch (err: any) {
      console.error('❌ Chart drawing error:', err);
      setError(err.message || 'Failed to render chart');
      setLoading(false);
    }
  };

  if (!chartConfig || !chartConfig.data) {
    return (
      <div style={{
        padding: '0.5rem',
        textAlign: 'center',
        color: '#EF4444',
        backgroundColor: '#FEE2E2',
        borderRadius: '0.5rem',
        fontSize: '0.875rem'
      }}>
        ⚠️ No chart data available
      </div>
    );
  }

  // ✅ Optimized container - Maximum chart size with zero padding
  return (
    <div style={{ 
      width: '100%',
      height: '100%',
      minHeight: '700px',
      position: 'relative',
      backgroundColor: 'transparent',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: 0,
      margin: 0
    }}>
      {loading && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '100%',
          height: '100%',
          color: '#6B7280',
          fontSize: '14px'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>📊</div>
            <div>Generating visualization...</div>
          </div>
        </div>
      )}
      
      <div 
        ref={chartRef} 
        style={{ 
          width: '100%',
          height: '700px',
          display: loading ? 'none' : 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          padding: 0,
          margin: 0
        }}
      />
      
      {error && (
        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          backgroundColor: '#FEE2E2',
          color: '#DC2626',
          padding: '0.5rem',
          borderRadius: '0.5rem',
          fontSize: '0.875rem',
          textAlign: 'center',
          maxWidth: '90%',
          border: '1px solid #DC2626',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          zIndex: 10
        }}>
          <div style={{ fontSize: '2rem', marginBottom: '0.75rem' }}>⚠️</div>
          <strong>Chart Error:</strong><br />
          {error}
        </div>
      )}
    </div>
  );
}
