from jinja2 import Template

class ReportGeneratorTool:
    def run(self, upgrade_data: dict):
        try:
            # Use a template to generate a report
            template = Template("""
            # .NET Upgrade Report
            ## Status: {{ status }}
            ## Errors: {{ errors }}
            ## Recommendations: {{ recommendations }}
            """)
            report = template.render(**upgrade_data)
            
            with open("upgrade_report.md", "w") as f:
                f.write(report)
            return "Report generated: upgrade_report.md"
        except Exception as e:
            return f"Report generation failed: {str(e)}"