from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User

from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    """Модель категорий с вложенностью"""
    title = models.CharField(max_length=255, verbose_name='Название категории')
    slug = models.SlugField(max_length=255, blank=True, verbose_name='URL категории')
    description = models.TextField(max_length=300, verbose_name='Описание категории')
    parent = TreeForeignKey('self',
                            on_delete=models.CASCADE,
                            null=True,
                            blank=True,
                            db_index=True,
                            related_name='children',
                            verbose_name='Родительская категория')
    class MPPTMeta:
        """Сортировка по вложенности"""
        order_insertion_by = ('title',)

    class Meta:
        """Сортировка, название модели в админ панели, таблица с данными"""
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        db_table = 'app_categories'

    def __str__(self):
        return self.title



class Post(models.Model):
    """Модель постов для блога"""
    STATUS_OPTIONS = (
        ('published', 'Опубликовано'),
        ('draft', 'Черновик')
    )
    title = models.CharField(max_length=255, verbose_name='Название поста')
    slug = models.SlugField(max_length=255, blank=True, verbose_name ='URL')
    description = models.TextField(max_length=500, verbose_name='Краткое описание')
    text = models.TextField(verbose_name='Полный текст поста')
    thumbnail = models.ImageField(default='default.jpg',
                                  blank=True,
                                  upload_to='images/thumbnails/%Y/%m/%d/',
                                  validators=[FileExtensionValidator(allowed_extensions=('png','jpg','webp','jpeg', 'gif'))]
                                  )
    status = models.CharField(choices=STATUS_OPTIONS, default='published', max_length=10, verbose_name='Статус записи')
    create = models.DateTimeField(auto_now_add=True, verbose_name='Время добавления')
    update = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    author = models.ForeignKey(to=User,
                               on_delete=models.SET_DEFAULT, related_name='author_posts', default=1, verbose_name='Автор')
    updater = models.ForeignKey(to=User,
                                on_delete=models.SET_NULL, related_name='updater_posts', null=True, blank=True, verbose_name='Обновил' )
    
    fixed = models.BooleanField(default=False, verbose_name='Закреплено')
    category = TreeForeignKey('Category', on_delete=models.PROTECT, related_name='posts', verbose_name='Категория')

    class Meta:
        db_table='blog_post'
        ordering =['-fixed', '-create']
        indexes = [models.Index(fields=['-fixed', '-create', 'status'])]
        verbose_name = 'Пост'
        verbose_name_plural = 'Статьи'

    def __str__(self):
        return self.title