from django.contrib import admin
from django.urls import include, path, reverse_lazy
from django.conf import settings
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.conf.urls.static import static

# from core.views import server_error, page_not_found
# from core import views

urlpatterns = [

    path(
        'admin/',
        admin.site.urls,
    ),

    path(
        '',
        include(
            'blog.urls',
            namespace='blog',
        )
    ),

    path(
        'pages/',
        include(
            'pages.urls',
            namespace='pages',
        )
    ),

    path(
        'auth/',
        include(
            'django.contrib.auth.urls'
        )
    ),

    path(
        'auth/registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('blog:index'),
        ),
        name='registration',
    ),

]

if settings.DEBUG:
    import debug_toolbar
    # Добавить к списку urlpatterns список адресов из приложения debug_toolbar:
    urlpatterns += (
        path(
            '__debug__/',
            include(debug_toolbar.urls)
        ),
    )
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )

handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'
