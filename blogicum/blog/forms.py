from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth import get_user_model

from .models import Post, Comment

User = get_user_model()


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ('author',)
        # fields = '__all__'
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'date'})
        }


class ProfileEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Удаляем поле "Пароль" из формы
        self.fields.pop('password')


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
