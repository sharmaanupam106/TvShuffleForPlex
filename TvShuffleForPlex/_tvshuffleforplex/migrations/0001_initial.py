# Generated by Django 3.1.5 on 2021-01-07 02:48

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SavedLists',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inserted_date', models.DateField(auto_now=True)),
                ('user', models.TextField(default=None)),
                ('name', models.TextField(default=None)),
                ('list', models.TextField(null=True)),
            ],
        ),
    ]
