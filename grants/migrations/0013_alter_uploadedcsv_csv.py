# Generated by Django 3.2.13 on 2022-06-18 17:58

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("grants", "0012_auto_20160119_0428"),
    ]

    operations = [
        migrations.AlterField(
            model_name="uploadedcsv",
            name="csv",
            field=models.TextField(),
        ),
    ]
