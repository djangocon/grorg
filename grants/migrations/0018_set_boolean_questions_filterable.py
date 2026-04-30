from __future__ import annotations

from django.db import migrations


def set_boolean_questions_filterable(apps, schema_editor):
    Question = apps.get_model("grants", "Question")
    Question.objects.filter(type="boolean").update(filterable=True)


def unset_filterable(apps, schema_editor):
    Question = apps.get_model("grants", "Question")
    Question.objects.update(filterable=False)


class Migration(migrations.Migration):
    dependencies = [
        ("grants", "0017_question_filterable"),
    ]

    operations = [
        migrations.RunPython(set_boolean_questions_filterable, unset_filterable),
    ]
