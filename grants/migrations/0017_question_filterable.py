from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("grants", "0016_applicant_rejection_reason_applicant_status_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="question",
            name="filterable",
            field=models.BooleanField(
                default=False,
                help_text="Show this question as a filter on the applicants list",
            ),
        ),
    ]
