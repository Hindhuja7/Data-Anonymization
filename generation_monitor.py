"""
Generation Monitoring System for CRM Dataset Generator
Tracks and reports generation metrics
"""
import json
import time
from datetime import datetime
from collections import defaultdict

class GenerationMonitor:
    """Monitor and track generation metrics"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.total_batches = 0
        self.deadlock_count = 0
        self.readonly_count = 0
        self.readonly_wait_time = 0  # Total seconds spent waiting
        self.readonly_events = []  # Track individual events
        self.batch_times = []  # Track individual batch times
        self.batch_rows = []  # Track rows per batch
        self.resume_count = 0
        self.table_metrics = defaultdict(dict)
        self.peak_throughput = 0
        self.total_rows_inserted = 0
        self.generation_start = None
        self.last_update = None
        
    def start(self):
        """Start monitoring"""
        self.start_time = time.time()
        self.generation_start = datetime.now().isoformat()
        self.last_update = self.generation_start
        
    def stop(self):
        """Stop monitoring"""
        self.end_time = time.time()
        self.last_update = datetime.now().isoformat()
        
    def record_batch(self, table_name, rows, batch_time):
        """Record a completed batch"""
        self.total_batches += 1
        self.batch_times.append(batch_time)
        self.batch_rows.append(rows)
        self.total_rows_inserted += rows
        
        # Calculate throughput for this batch
        throughput = rows / batch_time if batch_time > 0 else 0
        if throughput > self.peak_throughput:
            self.peak_throughput = throughput
        
        # Track table-specific metrics
        if table_name not in self.table_metrics:
            self.table_metrics[table_name] = {
                'batches': 0,
                'rows': 0,
                'total_time': 0,
                'deadlocks': 0,
                'readonly_events': 0
            }
        
        self.table_metrics[table_name]['batches'] += 1
        self.table_metrics[table_name]['rows'] += rows
        self.table_metrics[table_name]['total_time'] += batch_time
        
        self.last_update = datetime.now().isoformat()
        
    def record_deadlock(self, table_name=None):
        """Record a deadlock event"""
        self.deadlock_count += 1
        if table_name:
            self.table_metrics[table_name]['deadlocks'] += 1
        self.last_update = datetime.now().isoformat()
        
    def record_readonly(self, wait_time):
        """Record a read-only event with wait time"""
        self.readonly_count += 1
        self.readonly_wait_time += wait_time
        self.readonly_events.append({
            'timestamp': datetime.now().isoformat(),
            'wait_time': wait_time
        })
        self.last_update = datetime.now().isoformat()
        
    def record_resume(self):
        """Record a resume event"""
        self.resume_count += 1
        self.last_update = datetime.now().isoformat()
        
    def get_total_execution_time(self):
        """Get total execution time in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        elif self.start_time:
            return time.time() - self.start_time
        return 0
        
    def get_average_batch_time(self):
        """Get average batch insertion time"""
        if not self.batch_times:
            return 0
        return sum(self.batch_times) / len(self.batch_times)
        
    def get_average_throughput(self):
        """Get average rows per second"""
        total_time = self.get_total_execution_time()
        if total_time > 0 and self.total_rows_inserted > 0:
            return self.total_rows_inserted / total_time
        return 0
        
    def get_summary(self):
        """Get summary of all metrics"""
        return {
            'generation_info': {
                'start_time': self.generation_start,
                'end_time': self.last_update if self.end_time else None,
                'total_execution_time_seconds': self.get_total_execution_time(),
                'total_execution_time_formatted': self._format_duration(self.get_total_execution_time())
            },
            'batch_metrics': {
                'total_batches': self.total_batches,
                'total_rows_inserted': self.total_rows_inserted,
                'average_batch_time_seconds': self.get_average_batch_time(),
                'average_rows_per_second': self.get_average_throughput(),
                'peak_throughput_rows_per_second': self.peak_throughput
            },
            'error_handling': {
                'deadlock_count': self.deadlock_count,
                'readonly_event_count': self.readonly_count,
                'total_readonly_wait_time_seconds': self.readonly_wait_time,
                'total_readonly_wait_time_formatted': self._format_duration(self.readonly_wait_time),
                'average_readonly_wait_time_seconds': self.readonly_wait_time / self.readonly_count if self.readonly_count > 0 else 0
            },
            'resilience': {
                'resume_count': self.resume_count
            },
            'table_breakdown': dict(self.table_metrics),
            'readonly_events': self.readonly_events
        }
        
    def _format_duration(self, seconds):
        """Format duration in human-readable format"""
        if seconds == 0:
            return "0s"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
            
    def export_json(self, filename):
        """Export metrics to JSON file"""
        summary = self.get_summary()
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        return filename
        
    def export_pdf(self, filename):
        """Export metrics to PDF file"""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
        except ImportError:
            print("Warning: reportlab not installed. Generating HTML report instead.")
            # Fallback to HTML file
            return self.export_html(filename.replace('.pdf', '.html'))
        
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title = Paragraph("CRM Dataset Generation Report", styles['Title'])
        story.append(title)
        story.append(Spacer(1, 0.25*inch))
        
        # Summary
        summary = self.get_summary()
        
        # Generation Info
        story.append(Paragraph("Generation Information", styles['Heading2']))
        gen_info = [
            ['Start Time', summary['generation_info']['start_time']],
            ['End Time', summary['generation_info']['end_time'] or 'In Progress'],
            ['Total Execution Time', summary['generation_info']['total_execution_time_formatted']]
        ]
        gen_table = Table(gen_info, colWidths=[2*inch, 4*inch])
        gen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(gen_table)
        story.append(Spacer(1, 0.25*inch))
        
        # Batch Metrics
        story.append(Paragraph("Batch Metrics", styles['Heading2']))
        batch_info = [
            ['Total Batches', str(summary['batch_metrics']['total_batches'])],
            ['Total Rows Inserted', f"{summary['batch_metrics']['total_rows_inserted']:,}"],
            ['Average Batch Time', f"{summary['batch_metrics']['average_batch_time_seconds']:.4f}s"],
            ['Average Throughput', f"{summary['batch_metrics']['average_rows_per_second']:.2f} rows/sec"],
            ['Peak Throughput', f"{summary['batch_metrics']['peak_throughput_rows_per_second']:.2f} rows/sec"]
        ]
        batch_table = Table(batch_info, colWidths=[2*inch, 4*inch])
        batch_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(batch_table)
        story.append(Spacer(1, 0.25*inch))
        
        # Error Handling
        story.append(Paragraph("Error Handling", styles['Heading2']))
        error_info = [
            ['Deadlock Count', str(summary['error_handling']['deadlock_count'])],
            ['Read-Only Event Count', str(summary['error_handling']['readonly_event_count'])],
            ['Total Read-Only Wait Time', summary['error_handling']['total_readonly_wait_time_formatted']],
            ['Average Read-Only Wait Time', f"{summary['error_handling']['average_readonly_wait_time_seconds']:.2f}s"]
        ]
        error_table = Table(error_info, colWidths=[2*inch, 4*inch])
        error_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(error_table)
        story.append(Spacer(1, 0.25*inch))
        
        # Resilience
        story.append(Paragraph("Resilience Metrics", styles['Heading2']))
        resilience_info = [
            ['Resume Count', str(summary['resilience']['resume_count'])]
        ]
        resilience_table = Table(resilience_info, colWidths=[2*inch, 4*inch])
        resilience_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(resilience_table)
        story.append(Spacer(1, 0.25*inch))
        
        # Table Breakdown
        if summary['table_breakdown']:
            story.append(Paragraph("Table Breakdown", styles['Heading2']))
            table_data = [['Table', 'Batches', 'Rows', 'Total Time (s)', 'Deadlocks', 'Read-Only Events']]
            for table_name, metrics in summary['table_breakdown'].items():
                table_data.append([
                    table_name,
                    str(metrics['batches']),
                    f"{metrics['rows']:,}",
                    f"{metrics['total_time']:.2f}",
                    str(metrics['deadlocks']),
                    str(metrics['readonly_events'])
                ])
            
            table_breakdown = Table(table_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1.5*inch, 1*inch, 1.5*inch])
            table_breakdown.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9)
            ]))
            story.append(table_breakdown)
        
        # Build PDF
        doc.build(story)
        return filename
        
    def export_text(self, filename):
        """Export metrics to text file (fallback for PDF)"""
        summary = self.get_summary()
        
        with open(filename, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("CRM DATASET GENERATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("GENERATION INFORMATION\n")
            f.write("-" * 80 + "\n")
            f.write(f"Start Time: {summary['generation_info']['start_time']}\n")
            f.write(f"End Time: {summary['generation_info']['end_time'] or 'In Progress'}\n")
            f.write(f"Total Execution Time: {summary['generation_info']['total_execution_time_formatted']}\n\n")
            
            f.write("BATCH METRICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Total Batches: {summary['batch_metrics']['total_batches']}\n")
            f.write(f"Total Rows Inserted: {summary['batch_metrics']['total_rows_inserted']:,}\n")
            f.write(f"Average Batch Time: {summary['batch_metrics']['average_batch_time_seconds']:.4f}s\n")
            f.write(f"Average Throughput: {summary['batch_metrics']['average_rows_per_second']:.2f} rows/sec\n")
            f.write(f"Peak Throughput: {summary['batch_metrics']['peak_throughput_rows_per_second']:.2f} rows/sec\n\n")
            
            f.write("ERROR HANDLING\n")
            f.write("-" * 80 + "\n")
            f.write(f"Deadlock Count: {summary['error_handling']['deadlock_count']}\n")
            f.write(f"Read-Only Event Count: {summary['error_handling']['readonly_event_count']}\n")
            f.write(f"Total Read-Only Wait Time: {summary['error_handling']['total_readonly_wait_time_formatted']}\n")
            f.write(f"Average Read-Only Wait Time: {summary['error_handling']['average_readonly_wait_time_seconds']:.2f}s\n\n")
            
            f.write("RESILIENCE METRICS\n")
            f.write("-" * 80 + "\n")
            f.write(f"Resume Count: {summary['resilience']['resume_count']}\n\n")
            
            if summary['table_breakdown']:
                f.write("TABLE BREAKDOWN\n")
                f.write("-" * 80 + "\n")
                f.write(f"{'Table':<20} {'Batches':<10} {'Rows':<15} {'Total Time (s)':<15} {'Deadlocks':<10} {'Read-Only':<10}\n")
                f.write("-" * 80 + "\n")
                for table_name, metrics in summary['table_breakdown'].items():
                    f.write(f"{table_name:<20} {metrics['batches']:<10} {metrics['rows']:<15,} {metrics['total_time']:<15.2f} {metrics['deadlocks']:<10} {metrics['readonly_events']:<10}\n")
                f.write("\n")
            
            f.write("=" * 80 + "\n")
            f.write("END OF REPORT\n")
            f.write("=" * 80 + "\n")
        
        return filename
        
    def export_html(self, filename):
        """Export metrics to HTML file (fallback for PDF)"""
        summary = self.get_summary()
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>CRM Dataset Generation Report</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
            border-bottom: 1px solid #ddd;
            padding-bottom: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #007bff;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px;
            background-color: #f8f9fa;
            margin: 5px 0;
            border-radius: 4px;
        }}
        .metric-label {{
            font-weight: bold;
            color: #555;
        }}
        .metric-value {{
            color: #007bff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>CRM Dataset Generation Report</h1>
        
        <h2>Generation Information</h2>
        <div class="metric">
            <span class="metric-label">Start Time:</span>
            <span class="metric-value">{summary['generation_info']['start_time']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">End Time:</span>
            <span class="metric-value">{summary['generation_info']['end_time'] or 'In Progress'}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Total Execution Time:</span>
            <span class="metric-value">{summary['generation_info']['total_execution_time_formatted']}</span>
        </div>
        
        <h2>Batch Metrics</h2>
        <div class="metric">
            <span class="metric-label">Total Batches:</span>
            <span class="metric-value">{summary['batch_metrics']['total_batches']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Total Rows Inserted:</span>
            <span class="metric-value">{summary['batch_metrics']['total_rows_inserted']:,}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Average Batch Time:</span>
            <span class="metric-value">{summary['batch_metrics']['average_batch_time_seconds']:.4f}s</span>
        </div>
        <div class="metric">
            <span class="metric-label">Average Throughput:</span>
            <span class="metric-value">{summary['batch_metrics']['average_rows_per_second']:.2f} rows/sec</span>
        </div>
        <div class="metric">
            <span class="metric-label">Peak Throughput:</span>
            <span class="metric-value">{summary['batch_metrics']['peak_throughput_rows_per_second']:.2f} rows/sec</span>
        </div>
        
        <h2>Error Handling</h2>
        <div class="metric">
            <span class="metric-label">Deadlock Count:</span>
            <span class="metric-value">{summary['error_handling']['deadlock_count']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Read-Only Event Count:</span>
            <span class="metric-value">{summary['error_handling']['readonly_event_count']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Total Read-Only Wait Time:</span>
            <span class="metric-value">{summary['error_handling']['total_readonly_wait_time_formatted']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Average Read-Only Wait Time:</span>
            <span class="metric-value">{summary['error_handling']['average_readonly_wait_time_seconds']:.2f}s</span>
        </div>
        
        <h2>Resilience Metrics</h2>
        <div class="metric">
            <span class="metric-label">Resume Count:</span>
            <span class="metric-value">{summary['resilience']['resume_count']}</span>
        </div>
        
        """
        
        # Add table breakdown if available
        if summary['table_breakdown']:
            html_content += """
        <h2>Table Breakdown</h2>
        <table>
            <tr>
                <th>Table</th>
                <th>Batches</th>
                <th>Rows</th>
                <th>Total Time (s)</th>
                <th>Deadlocks</th>
                <th>Read-Only Events</th>
            </tr>
            """
            for table_name, metrics in summary['table_breakdown'].items():
                html_content += f"""
            <tr>
                <td>{table_name}</td>
                <td>{metrics['batches']}</td>
                <td>{metrics['rows']:,}</td>
                <td>{metrics['total_time']:.2f}</td>
                <td>{metrics['deadlocks']}</td>
                <td>{metrics['readonly_events']}</td>
            </tr>
            """
            html_content += """
        </table>
            """
        
        html_content += f"""
        
        <p style="color: #666; font-size: 12px; margin-top: 30px;">
            Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </p>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w') as f:
            f.write(html_content)
        
        return filename
