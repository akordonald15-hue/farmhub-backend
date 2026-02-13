from django.db import models

# Create your models here.

from django.conf import settings

class GeneratedReport(models.Model):
	"""
	Optional model for saving generated reports or audit logs.
	Stores metadata about report generation for auditing/admin purposes.
	"""
	REPORT_TYPE_CHOICES = [
		("users", "Users"),
		("orders", "Orders"),
		("payments", "Payments"),
		("reviews", "Reviews"),
		("dashboard", "Dashboard"),
	]

	report_type = models.CharField(max_length=32, choices=REPORT_TYPE_CHOICES)
	generated_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name="generated_reports"
	)
	generated_at = models.DateTimeField(auto_now_add=True)
	parameters = models.JSONField(blank=True, null=True, help_text="Parameters used for report generation (e.g., date range)")
	result_snapshot = models.JSONField(blank=True, null=True, help_text="Optional snapshot of the report data")

	class Meta:
		ordering = ["-generated_at"]
		verbose_name = "Generated Report"
		verbose_name_plural = "Generated Reports"

	def __str__(self):
		return f"{self.get_report_type_display()} report at {self.generated_at:%Y-%m-%d %H:%M:%S}"
