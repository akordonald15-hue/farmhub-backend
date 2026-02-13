# Generated manually to ensure proper dependency ordering in tests.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GeneratedReport",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("report_type", models.CharField(choices=[("users", "Users"), ("orders", "Orders"), ("payments", "Payments"), ("reviews", "Reviews"), ("dashboard", "Dashboard")], max_length=32)),
                ("generated_at", models.DateTimeField(auto_now_add=True)),
                ("parameters", models.JSONField(blank=True, help_text="Parameters used for report generation (e.g., date range)", null=True)),
                ("result_snapshot", models.JSONField(blank=True, help_text="Optional snapshot of the report data", null=True)),
                ("generated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="generated_reports", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-generated_at"],
                "verbose_name": "Generated Report",
                "verbose_name_plural": "Generated Reports",
            },
        ),
    ]
