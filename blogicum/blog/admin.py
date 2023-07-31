from django.contrib import admin

from .models import Category, Location, Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):

    list_display = (
        'title',
        'pub_date',
        'author',
        'location',
        'category',
        'is_published',
        'created_at',
    )

    list_editable = (
        'is_published',
        'category',
    )

    search_fields = (
        'title',
    )

    list_filter = (
        'category',
    )

    list_display_links = (
        'title',
    )


# Подготавливаем модель Post для вставки на страницу другой модели.
class PostInline(admin.TabularInline):

    model = Post
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    inlines = (
        PostInline,
    )

    list_display = (
        'title',
        'description',
        'slug',
        'is_published',
        'created_at',
    )

    list_editable = (
        'is_published',
    )

    search_fields = (
        'title',
        'description',
    )

    list_filter = (
        'is_published',
    )

    list_display_links = (
        'title',
    )


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'is_published',
        'created_at',
    )

    list_editable = (
        'is_published',
    )

    search_fields = (
        'name',
    )

    list_filter = (
        'is_published',
    )

    list_display_links = (
        'name',
    )


# значение, которое будет отображаться в административной панели,
# когда поле объекта не имеет значения.
admin.site.empty_value_display = 'Не задано'