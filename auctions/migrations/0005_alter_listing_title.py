# Generated by Django 5.1.2 on 2024-11-27 02:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('auctions', '0004_alter_listing_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='title',
            field=models.CharField(max_length=64),
        ),
    ]
