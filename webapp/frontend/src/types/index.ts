// TypeScript interfaces for BNPL Copilot

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    hasAnalytics?: boolean;
}

export interface KPI {
    label: string;
    value: string;
    unit?: string;
}

export interface ChartSeries {
    dataKey: string;
    color?: string;
}

export interface ChartData {
    id: string;
    kind: 'bar' | 'line' | 'doughnut' | 'pie' | 'area' | 'scatter' | 'radar' | 'funnel' | 'treemap' | 'radialBar';
    title: string;
    xKey: string;
    series: ChartSeries[];
    rows: Record<string, any>[];
}

export interface TableData {
    id: string;
    title: string;
    columns: string[];
    rows: Record<string, any>[];
}

export interface CardData {
    title: string;
    items: string[];
}

export interface AnalyticsPayload {
    kpis?: KPI[];
    charts?: ChartData[];
    tables?: TableData[];
    cards?: CardData[];
}

export interface ChatHistory {
    id: string;
    title: string;
    date: Date;
}

export interface ChatResponse {
    id: string;
    role: string;
    content: string;
    hasAnalytics: boolean;
    analytics?: AnalyticsPayload;
}
