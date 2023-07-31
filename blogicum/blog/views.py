from django.shortcuts import get_object_or_404, redirect, Http404
from django.urls import reverse_lazy, reverse
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


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )


class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    # def dispatch(self, request, *args, **kwargs):
    #     # Получаем объект по первичному ключу и автору или вызываем 404 ошибку.
    #     get_object_or_404(
    #         Post,
    #         pk=kwargs['pk'],
    #         author=request.user,
    #     )
    #     return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs['pk'])
        if post.author != request.user:
            return redirect('blog:post_detail', pk=post.pk)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('birthday:list')

    def post(self, request, *args, **kwargs):
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', pk=post.pk)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        if not post.is_published and post.author != request.user:
            raise Http404("Страница не найдена")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = Comment.objects.filter(post=context['post'])
        return context


class CategoryPostsView(ListView):
    model = Category
    template_name = 'blog/category.html'

    def get_queryset(self):
        category_slug = self.kwargs['category_slug']
        category = get_object_or_404(
            Category,
            slug=category_slug,
            is_published=True,
        )
        posts = category.posts(
            manager='published_manager',
        ).select_related(
            'location',
            'author'
        )
        return posts

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )
        posts = self.get_queryset().annotate(
            comment_count=Count('comments'),
        ).order_by('-pub_date')
        paginator = Paginator(posts, settings.POSTS_LIMIT)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        context['category'] = category
        return context


class ProfileDetailView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    # ordering = 'pub_date'

    # def get_object(self, queryset=None):
    #     return self.request.user

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = self.object.posts.select_related(
            'location',
            'author',
        ).annotate(
            comment_count=Count('comments'),
        ).order_by('-pub_date')
        paginator = Paginator(posts, 10)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj

        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = 'blog/user.html'
    form_class = ProfileEditForm

    def get_success_url(self):
        return reverse_lazy(
            'blog:profile',
            kwargs={'username': self.request.user.username},
        )

    def get_object(self, queryset=None):
        return self.request.user


class CommentCreateView(LoginRequiredMixin, CreateView):
    target_post = None
    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.target_post = get_object_or_404(Post, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.target_post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'pk': self.target_post.pk})


class CommentUpdateView(LoginRequiredMixin, UpdateView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def get_object(
        self,
        queryset=None
    ):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id'],
        )

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', pk=kwargs['post_id'])
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.object.post.pk},
        )


class CommentDeleteView(LoginRequiredMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'
    form_class = CommentForm

    def get_object(
        self,
        queryset=None
    ):
        return get_object_or_404(
            Comment,
            pk=self.kwargs['comment_id']
        )

    def post(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.author != request.user:
            return redirect('blog:post_detail', pk=kwargs['post_id'])
        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'pk': self.object.post.pk}
        )
