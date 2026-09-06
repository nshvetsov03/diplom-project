from django.db import models

# Create your models here.

class User(models.Model):
    pass



class Location(models.Model):
    name = models.CharField(verbose_name='Название', max_length=30)
    url = models.CharField(verbose_name='Ссылка', max_length=100)
    adress = models.CharField(verbose_name='Адрес', max_length=60)

    # filename

    class Meta:
        verbose_name = 'Локация'
        verbose_name_plural = 'Локации'
        ordering = ['-name']

class Category(models.Model):
    name = models.CharField(verbose_name='Категория', max_length=30)
    shops = models.ManyToManyField
    pass