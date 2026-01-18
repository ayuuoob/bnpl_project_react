import React, { useState } from 'react';
import type { AnalyticsPayload } from '../types';
import ChartRenderer from './ChartRenderer';
import { TrendingUp, DollarSign, AlertTriangle, Clock, X, BarChart3, FileText, LayoutGrid } from 'lucide-react';

interface Props {
    data?: AnalyticsPayload;
    onClose?: () => void;
}

type TabType = 'overview' | 'charts' | 'details';

const AnalyticsPanel: React.FC<Props> = ({ data, onClose }) => {
    const [activeTab, setActiveTab] = useState<TabType>('overview');

    if (!data || (!data.kpis?.length && !data.charts?.length && !data.tables?.length && !data.cards?.length)) {
        return (
            <div className="h-full w-full flex flex-col bg-white">
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                    <h2 className="text-lg font-semibold text-[#303848]">Analytics</h2>
                    {onClose && (
                        <button onClick={onClose} className="p-1.5 hover:bg-[#F8F8F8] rounded-lg transition-colors">
                            <X size={18} className="text-[#505050]" />
                        </button>
                    )}
                </div>
                <div className="flex-1 flex flex-col items-center justify-center text-[#505050] p-8 text-center overflow-y-auto">
                    <BarChart3 size={48} className="mb-4 opacity-20 text-[#582098]" />
                    <p className="text-sm">Ask a data-related question to see analytics here.</p>
                </div>
            </div>
        );
    }

    const tabs = [
        { id: 'overview' as TabType, label: 'Overview', icon: LayoutGrid },
        { id: 'charts' as TabType, label: 'Charts', icon: BarChart3 },
        { id: 'details' as TabType, label: 'Details', icon: FileText },
    ];

    const getKpiIcon = (label: string) => {
        const l = label.toLowerCase();
        if (l.includes('rate') || l.includes('approval')) return TrendingUp;
        if (l.includes('gmv') || l.includes('amount') || l.includes('value')) return DollarSign;
        if (l.includes('risk') || l.includes('late')) return AlertTriangle;
        return Clock;
    };

    const getKpiColor = (label: string) => {
        const l = label.toLowerCase();
        if (l.includes('risk') || l.includes('late') || l.includes('reject')) return 'text-[#dc2626] bg-[#dc2626]/10';
        if (l.includes('approval') || l.includes('success')) return 'text-[#608818] bg-[#608818]/10';
        if (l.includes('gmv') || l.includes('amount')) return 'text-[#582098] bg-[#582098]/10';
        return 'text-[#582098] bg-[#582098]/10';
    };

    return (
        <div className="h-full w-full flex flex-col bg-white overflow-hidden">
            <div className="flex items-center justify-between px-6 py-4 border-b border-border flex-shrink-0">
                <h2 className="text-lg font-semibold text-[#303848]">Analytics</h2>
                {onClose && (
                    <button onClick={onClose} className="p-1.5 hover:bg-[#F8F8F8] rounded-lg transition-colors">
                        <X size={18} className="text-[#505050]" />
                    </button>
                )}
            </div>

            <div className="flex border-b border-border px-6 flex-shrink-0">
                {tabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${activeTab === tab.id
                            ? 'border-[#582098] text-[#582098]'
                            : 'border-transparent text-[#505050] hover:text-[#303848]'
                            }`}
                    >
                        <tab.icon size={16} />
                        {tab.label}
                    </button>
                ))}
            </div>

            <div className="flex-1 overflow-y-auto p-6">
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        {data.kpis && data.kpis.length > 0 && (
                            <div className="grid grid-cols-2 gap-3">
                                {data.kpis.map((kpi, i) => {
                                    const Icon = getKpiIcon(kpi.label);
                                    const colorClass = getKpiColor(kpi.label);
                                    return (
                                        <div key={i} className="bg-white p-3 rounded-xl shadow-[0_2px_8px_-2px_rgba(6,81,237,0.1)] border border-blue-50/50 hover:shadow-md transition-shadow">
                                            <div className="flex items-start justify-between mb-1">
                                                <div className={`p-1.5 rounded-md ${colorClass}`}>
                                                    <Icon size={14} />
                                                </div>
                                            </div>
                                            <h3 className="text-gray-500 text-[10px] font-semibold uppercase tracking-wide">{kpi.label}</h3>
                                            <div className="mt-0.5 flex items-baseline gap-1.5">
                                                <span className="text-xl font-bold text-gray-900">{kpi.value}</span>
                                                <span className="text-[10px] font-medium text-red-500 bg-red-50 px-1 rounded">+2.1%</span>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}

                        {data.cards && data.cards.length > 0 && (
                            <div className="space-y-4">
                                {data.cards.map((card, i) => (
                                    <div key={i} className="bg-gray-50 p-5 rounded-xl border border-l-4 border-l-indigo-500">
                                        <h4 className="font-semibold text-gray-800 mb-3">{card.title}</h4>
                                        <ul className="space-y-2">
                                            {card.items.map((item, j) => (
                                                <li key={j} className="text-sm text-gray-600 flex items-start gap-2">
                                                    <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0" />
                                                    {item}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                ))}
                            </div>
                        )}

                        {data.charts && data.charts.length > 0 && (
                            <div>
                                <ChartRenderer data={data.charts[0]} />
                            </div>
                        )}
                        {/* Render tables in overview with a card style */}
                        {data.tables && data.tables.length > 0 && (
                            <div className="space-y-4 mt-4">
                                {data.tables.map((table) => (
                                    <div key={table.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                                        <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
                                            <h3 className="text-sm font-semibold text-gray-700">{table.title}</h3>
                                        </div>
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm text-left">
                                                <thead className="text-xs text-gray-500 uppercase bg-gray-50/50">
                                                    <tr>
                                                        {table.columns.map((col) => (
                                                            <th key={col} className="px-4 py-3 font-medium">{col}</th>
                                                        ))}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {table.rows.map((row, i) => (
                                                        <tr key={i} className="border-b border-gray-50 last:border-0 hover:bg-gray-50/50">
                                                            {table.columns.map((col) => (
                                                                <td key={col} className="px-4 py-3 text-gray-700 font-mono text-xs">
                                                                    {typeof row[col] === 'number'
                                                                        ? Number(row[col]).toLocaleString()
                                                                        : String(row[col] ?? '-')}
                                                                </td>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'charts' && (
                    <div className="space-y-6">
                        {data.charts && data.charts.length > 0 ? (
                            data.charts.map((chart) => (
                                <ChartRenderer key={chart.id} data={chart} />
                            ))
                        ) : (
                            <div className="text-center text-gray-400 py-12">
                                <BarChart3 size={32} className="mx-auto mb-2 opacity-40" />
                                <p className="text-sm">No charts available for this query</p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'details' && (
                    <div className="space-y-6">
                        {data.tables && data.tables.length > 0 ? (
                            data.tables.map((table) => (
                                <div key={table.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                                    <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
                                        <h3 className="text-sm font-semibold text-gray-700">{table.title}</h3>
                                    </div>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm text-left">
                                            <thead className="text-xs text-gray-500 uppercase bg-gray-50/50">
                                                <tr>
                                                    {table.columns.map((col) => (
                                                        <th key={col} className="px-4 py-3 font-medium">{col}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {table.rows.map((row, i) => (
                                                    <tr key={i} className="border-b border-gray-50 last:border-0 hover:bg-gray-50/50">
                                                        {table.columns.map((col) => (
                                                            <td key={col} className="px-4 py-3 text-gray-700 font-mono text-xs">
                                                                {typeof row[col] === 'number'
                                                                    ? Number(row[col]).toLocaleString()
                                                                    : String(row[col] ?? '-')}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center text-gray-400 py-12">
                                <FileText size={32} className="mx-auto mb-2 opacity-40" />
                                <p className="text-sm">No detailed data available for this query</p>
                            </div>
                        )}

                        {data.kpis && data.kpis.length > 0 && (
                            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                                <div className="px-4 py-3 border-b border-gray-100 bg-gray-50">
                                    <h3 className="text-sm font-semibold text-gray-700">Key Metrics Summary</h3>
                                </div>
                                <div className="divide-y divide-gray-50">
                                    {data.kpis.map((kpi, i) => (
                                        <div key={i} className="flex justify-between items-center px-4 py-3">
                                            <span className="text-sm text-gray-600">{kpi.label}</span>
                                            <span className="text-sm font-semibold text-gray-900">
                                                {kpi.value} {kpi.unit && <span className="text-gray-400 font-normal">{kpi.unit}</span>}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default AnalyticsPanel;
