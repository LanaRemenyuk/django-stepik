from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.urls import reverse

from ckeditor.fields import RichTextField
from mptt.models import MPTTModel, TreeForeignKey
from taggit.managers import TaggableManager

from apps.services.utils import unique_slugify


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
    
    def get_absolute_url(self):
        return reverse('post_by_category', kwargs={"slug": self.slug})


class PostManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().select_related('author', 'category').filter(status='published')
    

class Post(models.Model):
    """Модель постов для блога"""
    STATUS_OPTIONS = (
        ('published', 'Опубликовано'),
        ('draft', 'Черновик')
    )
    title = models.CharField(max_length=255, verbose_name='Название поста')
    slug = models.SlugField(max_length=255, blank=True, verbose_name ='URL')
    description = RichTextField(config_name='awesome_ckeditor', verbose_name='Краткое описание', max_length=500)
    text = RichTextField(config_name='awesome_ckeditor', verbose_name='Полный текст записи')
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

    objects = models.Manager()
    custom = PostManager()

    tags = TaggableManager()

    class Meta:
        db_table = 'blog_post'
        ordering = ['-fixed', '-create']
        indexes = [models.Index(fields=['-fixed', '-create', 'status'])]
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """
        Получаем прямую ссылку на статью
        """
        return reverse('post_detail', kwargs={'slug': self.slug}) 
    
    def save(self, *args, **kwargs):
        """
        При сохранении генерируем слаг и проверяем на уникальность
        """
        self.slug = unique_slugify(self, self.title, self.slug)
        super().save(*args, **kwargs)

    def get_sum_rating(self):
        return sum([rating.value for rating in self.ratings.all()])


class Comment(MPTTModel):
    """
    Модель древовидных комментариев
    """
    STATUS_OPTIONS = (
        ('published', 'Опубликовано'),
        ('draft', 'Черновик')
    )

    post = models.ForeignKey(Post, on_delete=models.CASCADE, verbose_name='Запись', related_name='comments')
    author = models.ForeignKey(User, verbose_name='Автор комментария', on_delete=models.CASCADE, related_name='comments_author')
    content = models.TextField(verbose_name='Текст комментария', max_length=3000)
    time_create = models.DateTimeField(verbose_name='Время добавления', auto_now_add=True)
    time_update = models.DateTimeField(verbose_name='Время обновления', auto_now=True)
    status = models.CharField(choices=STATUS_OPTIONS, default='published', verbose_name='Статус поста', max_length=10)
    parent = TreeForeignKey('self', verbose_name='Родительский комментарий', null=True, blank=True, related_name='children', on_delete=models.CASCADE)
    

    class MTTMeta:
        order_insertion_by = ('-time_create',)


    class Meta:
        ordering = ['-time_create']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'{self.author}:{self.content}'
    

class Rating(models.Model):
    """
    Модель рейтинга: Лайк - Дизлайк
    """
    post = models.ForeignKey(to=Post, verbose_name='Запись', on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(to=User, verbose_name='Пользователь', on_delete=models.CASCADE, blank=True, null=True)
    value = models.IntegerField(verbose_name='Значение', choices=[(1, 'Нравится'), (-1, 'Не нравится')])
    time_create = models.DateTimeField(verbose_name='Время добавления', auto_now_add=True)
    ip_address = models.GenericIPAddressField(verbose_name='IP Адрес')

    class Meta:
        unique_together = ('post', 'ip_address')
        ordering = ('-time_create',)
        indexes = [models.Index(fields=['-time_create', 'value'])]
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтинги'

    def __str__(self):
        return self.post.title