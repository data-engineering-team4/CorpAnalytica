# Generated by Django 4.2 on 2023-08-27 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='corp_basic',
            fields=[
                ('entno', models.CharField(max_length=8, primary_key=True, serialize=False)),
                ('corpname', models.CharField(max_length=100)),
                ('code', models.CharField(max_length=6)),
                ('crno', models.CharField(max_length=13)),
                ('stock_type', models.CharField(max_length=30, null=True)),
            ],
            options={
                'db_table': 'corp_basic',
            },
        ),
    ]
