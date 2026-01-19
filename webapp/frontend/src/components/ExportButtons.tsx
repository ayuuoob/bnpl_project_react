import { useState } from "react";
import { FileDown, FileSpreadsheet, Loader2 } from "lucide-react";
import { getCurrentUser } from "../lib/auth";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import * as XLSX from "xlsx";
import { saveAs } from "file-saver";

interface ExportButtonsProps {
    title: string;
    columns: string[];
    rows: Record<string, unknown>[];
}

export function ExportButtons({ title, columns, rows }: ExportButtonsProps) {
    const [exporting, setExporting] = useState<"pdf" | "excel" | null>(null);
    const user = getCurrentUser();

    // Only show for admin and analyst
    if (!user || !["admin", "analyst"].includes(user.role)) {
        return null;
    }

    const handleExportPDF = async () => {
        setExporting("pdf");
        try {
            const doc = new jsPDF();

            // Title
            doc.setFontSize(16);
            doc.text(title, 14, 20);

            // Date
            doc.setFontSize(10);
            doc.text(`Generated: ${new Date().toLocaleString()}`, 14, 28);
            doc.text(`Exported by: ${user?.name} (${user?.role})`, 14, 34);

            // Table
            const tableData = rows.map((row) =>
                columns.map((col) => {
                    const value = row[col] ?? row[col.toLowerCase()] ?? "";
                    return String(value);
                })
            );

            autoTable(doc, {
                head: [columns],
                body: tableData,
                startY: 40,
                styles: { fontSize: 8 },
                headStyles: { fillColor: [88, 32, 152] }, // #582098
            });

            doc.save(`${title.replace(/\s+/g, "_")}_${Date.now()}.pdf`);
        } catch (error) {
            console.error("PDF export failed:", error);
        }
        setExporting(null);
    };

    const handleExportExcel = async () => {
        setExporting("excel");
        try {
            // Create worksheet data
            const wsData = [
                columns,
                ...rows.map((row) =>
                    columns.map((col) => {
                        const value = row[col] ?? row[col.toLowerCase()] ?? "";
                        return value;
                    })
                ),
            ];

            const ws = XLSX.utils.aoa_to_sheet(wsData);
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, title.slice(0, 31)); // Sheet name max 31 chars

            // Generate buffer and save
            const excelBuffer = XLSX.write(wb, { bookType: "xlsx", type: "array" });
            const blob = new Blob([excelBuffer], {
                type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            });
            saveAs(blob, `${title.replace(/\s+/g, "_")}_${Date.now()}.xlsx`);
        } catch (error) {
            console.error("Excel export failed:", error);
        }
        setExporting(null);
    };

    return (
        <div className="flex items-center gap-2">
            <button
                onClick={handleExportPDF}
                disabled={exporting !== null}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-[#582098] rounded-lg hover:bg-[#582098]/90 disabled:opacity-50 transition-colors"
                title="Export as PDF"
            >
                {exporting === "pdf" ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                    <FileDown className="h-3.5 w-3.5" />
                )}
                PDF
            </button>
            <button
                onClick={handleExportExcel}
                disabled={exporting !== null}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-[#608818] rounded-lg hover:bg-[#608818]/90 disabled:opacity-50 transition-colors"
                title="Export as Excel"
            >
                {exporting === "excel" ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                    <FileSpreadsheet className="h-3.5 w-3.5" />
                )}
                Excel
            </button>
        </div>
    );
}
