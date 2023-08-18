from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count
from django.urls import reverse
from django.utils import timezone

from .abstract_models import IsPublishedCreatedAt, TitleModel

User = get_user_model()


class OwnerPostManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related(
            'location',
            'author',
            'category',
        ).annotate(
            comment_count=Count('comments'),
        ).order_by('-pub_date')


class PublishedPostManager(OwnerPostManager):
    def get_queryset(self):
        return super().get_queryset().filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        )


class Post(TitleModel, IsPublishedCreatedAt):

    text = models.TextField(
        verbose_name='Текст',
    )

    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text='Если установить дату и время в будущем — '
                  'можно делать отложенные публикации.',
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
    )

    location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Местоположение',
    )

    category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Категория',
    )

    image = models.ImageField(
        'Фото',
        blank=True,
        upload_to=settings.FILE_PATH_UPLOAD_TO,
    )

    objects = models.Manager()
    published_manager = PublishedPostManager()
    owner_manager = OwnerPostManager()

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ['-pub_date']
        default_related_name = 'posts'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.pk},
        )


class Category(TitleModel, IsPublishedCreatedAt):

    description = models.TextField(
        verbose_name='Описание',
    )

    slug = models.SlugField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name='Идентификатор',
        help_text='Идентификатор страницы для URL; разрешены символы '
                  'латиницы, цифры, дефис и подчёркивание.',
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title


class Location(IsPublishedCreatedAt):

    name = models.CharField(
        max_length=256,
        verbose_name='Название места',
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class Comment(models.Model):

    text = models.TextField(
        'Текст комментария',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='публикация',
        related_name='comments',
    )
    created_at = models.DateTimeField(
        'время создания',
        auto_now_add=True,
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='автор',
    )

    class Meta:
        ordering = (
            'created_at',
        )
        default_related_name = 'comments'
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'

    def get_absolute_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'pk': self.post.pk},
        )
