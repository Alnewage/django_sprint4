from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import Http404, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)
from django.views.generic.list import MultipleObjectMixin

from .forms import CommentForm, PostForm, ProfileEditForm
from .models import Category, Comment, Post

User = get_user_model()

# ------------------------------------------------------------
# --------------------------MIXINS----------------------------
# ------------------------------------------------------------


class ModelFormPostMixin:

    model = Post
    form_class = PostForm


class ModelFormCommentMixin:

    model = Comment
    form_class = CommentForm


class PostCheckUserMixin:

    object = None
    queryset = Post.objects.select_related(
        'author',
        'location',
        'category',
    )

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author != request.user:
            return redirect(
                self.object.get_absolute_url(),
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())


class SuccessUrlMixin:

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={
                'username': self.request.user.username,
            },
        )


class CommentDefPostMixin:

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect(
                'blog:post_detail',
                pk=comment.post.pk,
            )
        return super().post(request, *args, **kwargs)

# ------------------------------------------------------------
# ----------------------------CBV-----------------------------
# ------------------------------------------------------------


class PostListView(ListView):

    model = Post
    template_name = 'blog/index.html'
    paginate_by = settings.POSTS_LIMIT
    queryset = Post.published_manager.all()


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'
    queryset = Post.objects.select_related(
        'author',
        'location',
        'category',
    )

    def get(self, request, *args, **kwargs):
        get_super = super().get(request, *args, **kwargs)
        if self.object.author != request.user and any(
            [
                not self.object.is_published,
                not self.object.category.is_published,
                not (self.object.pub_date < timezone.now()),
            ]
        ):
            raise Http404("Страница не найдена")
        return get_super

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            form=CommentForm(),
            comments=self.object.comments.select_related('author'),
        )


class PostCreateView(
    LoginRequiredMixin, SuccessUrlMixin, ModelFormPostMixin, CreateView,
):

    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(
    LoginRequiredMixin, PostCheckUserMixin, ModelFormPostMixin, UpdateView,
):

    template_name = 'blog/create.html'


class PostDeleteView(
    LoginRequiredMixin, SuccessUrlMixin, ModelFormPostMixin,
    PostCheckUserMixin, DeleteView,
):

    template_name = 'blog/create.html'

    def get_context_data(self, **kwargs):
        return dict(
            **super().get_context_data(**kwargs),
            form=PostForm(instance=self.object),
        )


class CategoryPostsView(ListView):

    template_name = 'blog/category.html'
    paginate_by = settings.POSTS_LIMIT
    category = None

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )

        return self.category.posts(
            manager='published_manager',
        ).all()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileDetailView(DetailView, MultipleObjectMixin):

    model = User
    template_name = 'blog/profile.html'
    paginate_by = settings.POSTS_LIMIT
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context_object_name = 'profile'
        context = super(DetailView, self).get_context_data(**kwargs)
        context_object_name = None
        queryset = self.object.posts(
            manager='owner_manager' if (
                self.request.user == self.object
            ) else 'published_manager'
        ).all()
        context.update(
            super(MultipleObjectMixin, self).get_context_data(
                object_list=queryset,
                **kwargs,
            )
        )
        return context

# class ProfileDetailView(DetailView):
#
#     model = User
#     template_name = 'blog/profile.html'
#     context_object_name = 'profile'
#     paginate_by = settings.POSTS_LIMIT
#     slug_field = 'username'
#     slug_url_kwarg = 'username'
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         posts = self.object.posts(
#             manager='owner_manager' if (
#                 self.request.user == self.object
#             ) else 'published_manager'
#         ).all()
#
#         paginator = Paginator(
#             posts,
#             self.paginate_by,
#         )
#         context['page_obj'] = paginator.get_page(
#             self.request.GET.get('page'),
#         )
#
#         return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):

    model = User
    form_class = ProfileEditForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            User,
            username=self.request.user.username,
        )

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={
                'username': self.request.user.username,
            },
        )


class CommentCreateView(LoginRequiredMixin, ModelFormCommentMixin, CreateView):

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs['pk'],
        )
        return super().form_valid(form)


class CommentUpdateView(
    LoginRequiredMixin, ModelFormCommentMixin, CommentDefPostMixin, UpdateView,
):

    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


class CommentDeleteView(
    LoginRequiredMixin, ModelFormCommentMixin, CommentDefPostMixin, DeleteView,
):

    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        return self.object.get_absolute_url()
