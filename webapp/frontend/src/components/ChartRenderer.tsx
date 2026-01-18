import React from 'react';
import {
    LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area, ScatterChart, Scatter,
    RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, RadialBarChart, RadialBar,
    Treemap, FunnelChart, Funnel, LabelList,
    XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import type { ChartData } from '../types';

interface Props {
    data: ChartData;
}

const COLORS = ['#10B981', '#F59E0B', '#EF4444', '#3B82F6', '#8B5CF6', '#EC4899', '#6366F1'];

const ChartRenderer: React.FC<Props> = ({ data }) => {
    const { kind, xKey, series, rows, title } = data;

    const renderChart = () => {
        switch (kind) {
            case 'line':
                return (
                    <LineChart data={rows}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                        <XAxis dataKey={xKey || 'name'} tick={{ fontSize: 10 }} stroke="#9ca3af" />
                        <YAxis tick={{ fontSize: 10 }} stroke="#9ca3af" />
                        <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Legend wrapperStyle={{ paddingTop: '5px', fontSize: '10px' }} />
                        {series.map((s, i) => (
                            <Line key={i} type="monotone" dataKey={s.dataKey} stroke={s.color || COLORS[i % COLORS.length]} strokeWidth={2} dot={false} />
                        ))}
                    </LineChart>
                );
            case 'area':
                return (
                    <AreaChart data={rows}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                        <XAxis dataKey={xKey || 'name'} tick={{ fontSize: 10 }} stroke="#9ca3af" />
                        <YAxis tick={{ fontSize: 10 }} stroke="#9ca3af" />
                        <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Legend wrapperStyle={{ paddingTop: '5px', fontSize: '10px' }} />
                        {series.map((s, i) => (
                            <Area key={i} type="monotone" dataKey={s.dataKey} fill={s.color || COLORS[i % COLORS.length]} stroke={s.color || COLORS[i % COLORS.length]} fillOpacity={0.3} />
                        ))}
                    </AreaChart>
                );
            case 'doughnut':
            case 'pie':
                return (
                    <PieChart>
                        <Pie
                            data={rows}
                            cx="50%"
                            cy="50%"
                            innerRadius={kind === 'doughnut' ? 60 : 0}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                        >
                            {rows.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip />
                        <Legend verticalAlign="middle" align="right" layout="vertical" iconType="circle" wrapperStyle={{ fontSize: '10px' }} />
                    </PieChart>
                );
            case 'radar':
                return (
                    <RadarChart cx="50%" cy="50%" outerRadius="80%" data={rows}>
                        <PolarGrid stroke="#e5e7eb" />
                        <PolarAngleAxis dataKey={xKey || 'name'} tick={{ fontSize: 10 }} />
                        <PolarRadiusAxis angle={30} domain={[0, 'auto']} tick={false} axisLine={false} />
                        <Tooltip />
                        <Legend wrapperStyle={{ paddingTop: '5px', fontSize: '10px' }} />
                        {series.map((s, i) => (
                            <Radar key={i} name={s.dataKey} dataKey={s.dataKey} stroke={s.color || COLORS[i % COLORS.length]} fill={s.color || COLORS[i % COLORS.length]} fillOpacity={0.4} />
                        ))}
                    </RadarChart>
                );
            case 'radialBar':
                return (
                    <RadialBarChart cx="50%" cy="50%" innerRadius="10%" outerRadius="100%" barSize={10} data={rows}>
                        <RadialBar label={{ position: 'insideStart', fill: '#fff' }} background dataKey="value" />
                        <Legend iconSize={10} layout="vertical" verticalAlign="middle" wrapperStyle={{ right: 0 }} />
                        <Tooltip />
                    </RadialBarChart>
                );
            case 'treemap':
                return (
                    <Treemap
                        data={rows}
                        dataKey="value"
                        aspectRatio={4 / 3}
                        stroke="#fff"
                        fill="#8884d8"
                    >
                        <Tooltip />
                    </Treemap>
                );
            case 'funnel':
                return (
                    <FunnelChart>
                        <Tooltip />
                        <Funnel
                            data={rows}
                            dataKey="value"
                            nameKey="name"
                        >
                            <LabelList position="right" fill="#000" stroke="none" dataKey="name" />
                        </Funnel>
                    </FunnelChart>
                );
            case 'scatter':
                return (
                    <ScatterChart>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis type="number" dataKey={xKey} name={xKey} />
                        <YAxis type="number" dataKey="value" name="Value" />
                        <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                        <Scatter name={title} data={rows} fill="#8884d8" />
                    </ScatterChart>
                );
            default: // Bar
                return (
                    <BarChart data={rows}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                        <XAxis dataKey={xKey || 'name'} tick={{ fontSize: 10 }} stroke="#9ca3af" />
                        <YAxis tick={{ fontSize: 10 }} stroke="#9ca3af" />
                        <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                        <Legend wrapperStyle={{ paddingTop: '5px', fontSize: '10px' }} />
                        {series.map((s, i) => (
                            <Bar key={i} dataKey={s.dataKey} fill={s.color || COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
                        ))}
                    </BarChart>
                );
        }
    };

    return (
        <div className="bg-white p-3 rounded-xl shadow-[0_2px_8px_-2px_rgba(6,81,237,0.1)] border border-blue-50/50 mb-4 transition-all hover:shadow-md">
            <h3 className="text-xs font-semibold text-gray-800 mb-2 flex items-center gap-1.5 uppercase tracking-wide">
                {kind === 'doughnut' && <span className="w-1.5 h-1.5 rounded-full bg-orange-400"></span>}
                {title}
            </h3>
            <div className="h-48 w-full">
                <ResponsiveContainer width="100%" height="100%">
                    {renderChart()}
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default ChartRenderer;
