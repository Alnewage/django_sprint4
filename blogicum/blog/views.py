from django.shortcuts import get_object_or_404, redirect, Http404
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.views.generic import (
    ListView, CreateView, UpdateView, DetailView, DeleteView,
)
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count


from .models import Post, Category, Comment
from .forms import PostForm, ProfileEditForm, CommentForm

User = get_user_model()


class ModelFormPostMixin:

    model = Post
    form_class = PostForm


class ModelFormCommentMixin:

    model = Comment
    form_class = CommentForm


class PostListView(ListView):

    model = Post
    template_name = 'blog/index.html'
    ordering = '-pub_date'
    paginate_by = settings.POSTS_LIMIT

    def get_queryset(self):
        queryset = super().get_queryset().filter(
            is_published=True,
            category__is_published=True,
            pub_date__lte=timezone.now(),
        ).select_related(
            'location',
            'author',
            'category',
        ).annotate(
            comment_count=Count('comments'),
        )

        return queryset


class PostCreateView(LoginRequiredMixin, ModelFormPostMixin, CreateView):

    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={
                'username': self.request.user.username,
            },
        )


class PostUpdateView(LoginRequiredMixin, ModelFormPostMixin, UpdateView):

    template_name = 'blog/create.html'

    def post(self, request, *args, **kwargs):
        post = get_object_or_404(
            Post,
            pk=kwargs['pk'],
        )
        if post.author != request.user:
            return redirect(
                'blog:post_detail',
                pk=post.pk,
            )

        return super().post(request, *args, **kwargs)


class PostDeleteView(LoginRequiredMixin, ModelFormPostMixin, DeleteView):

    template_name = 'blog/create.html'
    success_url = reverse_lazy('birthday:list')

    def post(self, request, *args, **kwargs):
        post = get_object_or_404(
            Post,
            pk=kwargs['pk'],
        )
        if post.author != request.user:
            return redirect(
                'blog:post_detail',
                pk=post.pk,
            )
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={
                'username': self.request.user.username,
            },
        )


class PostDetailView(ModelFormPostMixin, DetailView):

    template_name = 'blog/detail.html'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if not post.is_published and post.author != request.user:
            raise Http404(
                "Страница не найдена",
            )
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.filter(
            post=context['post'],
        )
        return context


class CategoryPostsView(ListView):

    model = Category
    template_name = 'blog/category.html'
    paginate_by = settings.POSTS_LIMIT

    def get_queryset(self):
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        posts = category.posts(
            manager='published_manager',
        ).select_related(
            'location',
            'author',
        ).annotate(
            comment_count=Count('comments'),
        ).order_by('-pub_date')

        return posts


class ProfileDetailView(DetailView):

    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    paginate_by = settings.POSTS_LIMIT

    def get_object(self, queryset=None):
        return get_object_or_404(
            User,
            username=self.kwargs.get('username'),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.object.posts.select_related(
            'location',
            'author',
        ).annotate(
            comment_count=Count('comments'),
        ).order_by('-pub_date')
        paginator = Paginator(posts, self.paginate_by)
        context['page_obj'] = paginator.get_page(self.request.GET.get('page'))

        return context


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

    target_post = None

    def dispatch(self, request, *args, **kwargs):
        self.target_post = get_object_or_404(
            Post,
            pk=kwargs['pk'],
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.target_post
        return super().form_valid(form)


class CommentUpdateView(LoginRequiredMixin, ModelFormCommentMixin, UpdateView):

    template_name = 'blog/comment.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
        )

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect(
                'blog:post_detail',
                pk=kwargs['pk'],
            )
        return super().post(request, *args, **kwargs)


class CommentDeleteView(LoginRequiredMixin, ModelFormCommentMixin, DeleteView):

    template_name = 'blog/comment.html'

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect(
                'blog:post_detail',
                pk=comment.post.pk,
            )
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return self.object.get_absolute_url()
