"use client";

import { useEffect, useState } from "react";
import GoogleChart from "./GoogleChart";

interface SalesChartProps {
  locationId: string;
  productId: string;
}

export default function SalesChart({ locationId, productId }: SalesChartProps) {
  const [chartConfig, setChartConfig] = useState<any>(null);

  useEffect(() => {
    fetchSalesTrends();
  }, [locationId, productId]);

  const fetchSalesTrends = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/analytics/trends/sales?location_id=${locationId}&product_id=${productId}`
      );
      const result = await response.json();
      
      // Convert to Google Charts format
      const data = result.data || [];
      if (data.length > 0) {
        const chartData = [['Date', 'Quantity', 'Revenue']];
        data.forEach((row: any) => {
          chartData.push([row.date, row.quantity, row.revenue]);
        });
        
        setChartConfig({
          chartType: 'LineChart',
          data: chartData,
          options: {
            title: 'Sales Trends',
            colors: ['#D04A02', '#3B82F6'],
            curveType: 'function',
            legend: { position: 'top' },
            chartArea: { width: '85%', height: '75%' }
          }
        });
      }
    } catch (error) {
      console.error("Failed to fetch sales trends:", error);
    }
  };

  return (
    <div style={{ 
      width: '100%', 
      padding: '1.5rem',
      backgroundColor: '#ffffff',
      borderRadius: '0.75rem',
      border: '1px solid #E5E7EB',
      boxShadow: '0 2px 4px rgba(0, 0, 0, 0.05)'
    }}>
      {chartConfig ? (
        <GoogleChart chartConfig={chartConfig} />
      ) : (
        <div style={{ 
          textAlign: 'center', 
          padding: '4rem', 
          color: '#6B7280',
          height: '700px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <div>
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
            <div>Loading chart...</div>
          </div>
        </div>
      )}
    </div>
  );
}
