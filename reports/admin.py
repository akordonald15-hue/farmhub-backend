
from django.contrib import admin
from .models import GeneratedReport

@admin.register(GeneratedReport)
class GeneratedReportAdmin(admin.ModelAdmin):
	list_display = ("id", "report_type", "generated_by", "generated_at")
	list_filter = ("report_type", "generated_at")
	search_fields = ("generated_by__username", "parameters")
	readonly_fields = ("report_type", "generated_by", "generated_at", "parameters", "result_snapshot")
	date_hierarchy = "generated_at"
	ordering = ("-generated_at",)

	def has_add_permission(self, request):
		return False

	def has_change_permission(self, request, obj=None):
		return False

	def has_delete_permission(self, request, obj=None):
		return False
