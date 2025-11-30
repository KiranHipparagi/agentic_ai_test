"use client";

import { useState, useEffect } from "react";
import { ArrowUpDown, AlertCircle } from "lucide-react";

interface DataTableProps {
  title: string;
  columns: string[];
  compact?: boolean;
}

export default function DataTable({ title, columns, compact = false }: DataTableProps) {
  const [data, setData] = useState<any[]>([]);
  const [sortColumn, setSortColumn] = useState<number>(0);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    generateMockData();
    const interval = setInterval(generateMockData, 10000); // Update every 10s
    return () => clearInterval(interval);
  }, []);

  const generateMockData = () => {
    const mockData = Array.from({ length: compact ? 5 : 8 }, (_, i) => {
      if (columns.includes("Product")) {
        return [
          `Product ${String.fromCharCode(65 + i)}`,
          Math.floor(Math.random() * 100) + 10,
          Math.random() > 0.5 ? "Low" : "OK"
        ];
      } else if (columns.includes("SKU")) {
        return [
          `SKU-${1000 + i}`,
          Math.floor(Math.random() * 200),
          Math.floor(Math.random() * 300) + 100,
          "Reorder"
        ];
      } else {
        return [
          `Item ${i + 1}`,
          `$${Math.floor(Math.random() * 10000).toLocaleString()}`,
          `${(Math.random() * 30 - 10).toFixed(1)}%`
        ];
      }
    });

    setData(mockData);
  };

  const handleSort = (columnIndex: number) => {
    const newDirection = sortColumn === columnIndex && sortDirection === "asc" ? "desc" : "asc";
    setSortColumn(columnIndex);
    setSortDirection(newDirection);

    const sorted = [...data].sort((a, b) => {
      const aVal = a[columnIndex];
      const bVal = b[columnIndex];
      
      if (typeof aVal === "number" && typeof bVal === "number") {
        return newDirection === "asc" ? aVal - bVal : bVal - aVal;
      }
      
      return newDirection === "asc" 
        ? String(aVal).localeCompare(String(bVal))
        : String(bVal).localeCompare(String(aVal));
    });

    setData(sorted);
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-3 border border-gray-200">
      <h3 className="text-xs font-semibold text-gray-900 mb-2">{title}</h3>
      
      <div className="overflow-auto max-h-60">
        <table className="w-full text-[10px]">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className="px-2 py-1.5 text-left font-semibold text-gray-700 cursor-pointer hover:bg-gray-100 transition-colors"
                  onClick={() => handleSort(idx)}
                >
                  <div className="flex items-center gap-1">
                    {col}
                    <ArrowUpDown className="w-3 h-3 text-gray-400" />
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className="hover:bg-gray-50 transition-colors"
              >
                {row.map((cell: any, cellIdx: number) => (
                  <td key={cellIdx} className="px-2 py-1.5 text-gray-700">
                    {cellIdx === row.length - 1 && (cell === "Low" || cell === "Critical") ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-700">
                        <AlertCircle className="w-3 h-3" />
                        {cell}
                      </span>
                    ) : cellIdx === row.length - 1 && cell === "Reorder" ? (
                      <button className="text-xs px-2 py-1 bg-[#D04A02] text-white rounded hover:bg-[#A83C02] transition-colors">
                        {cell}
                      </button>
                    ) : String(cell).includes("%") && parseFloat(cell) > 0 ? (
                      <span className="text-green-600 font-medium">{cell}</span>
                    ) : String(cell).includes("%") && parseFloat(cell) < 0 ? (
                      <span className="text-red-600 font-medium">{cell}</span>
                    ) : (
                      cell
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
