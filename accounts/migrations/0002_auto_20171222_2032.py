# Generated by Django 2.0 on 2017-12-23 04:32

import accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('email', models.EmailField(max_length=254, primary_key=True, serialize=False)),
            ],
        ),
        migrations.AlterField(
            model_name='token',
            name='uid',
            field=models.CharField(default=accounts.models.Token.create_uid, max_length=40),
        ),
    ]
