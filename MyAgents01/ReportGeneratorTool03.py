class ReportGeneratorTool(BaseTool):
    def run(self, upgrade_data: dict):
        try:
            self._log("Generating upgrade report")
            template = Template("""
            # .NET Upgrade Report
            ## Status: {{ status }}
            {% if errors %}
            ## Errors: {{ errors }}
            {% endif %}
            {% if suggestions %}
            ## AI Suggestions: {{ suggestions }}
            {% endif %}
            """)
            report = template.render(**upgrade_data)
            
            with open("upgrade_report.md", "w") as f:
                f.write(report)
            
            self._log("Report generated: upgrade_report.md")
            return {"status": "success", "report_path": "upgrade_report.md"}
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            self._log(error_msg, "error")
            return {"status": "error", "error": error_msg}