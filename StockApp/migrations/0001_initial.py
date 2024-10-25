# Generated by Django 5.1.2 on 2024-10-22 23:15

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PredictedStockData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=10)),
                ('timestamp', models.BigIntegerField()),
                ('predicted_close_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('predicted_open_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('predicted_high_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('predicted_low_price', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('predicted_volume', models.DecimalField(blank=True, decimal_places=8, max_digits=20, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-timestamp'],
                'unique_together': {('symbol', 'timestamp')},
            },
        ),
        migrations.CreateModel(
            name='StockHistoryData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=10)),
                ('timestamp', models.BigIntegerField()),
                ('open_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('close_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('high_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('low_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('volume', models.DecimalField(decimal_places=8, max_digits=20)),
            ],
            options={
                'ordering': ['-timestamp'],
                'unique_together': {('symbol', 'timestamp')},
            },
        ),
    ]