from tortoise import models, fields
from tortoise.contrib.pydantic import pydantic_model_creator

class User(models.Model):
    user_id = fields.IntField(pk=True)
    username = fields.CharField(max_length=100, unique=True)
    email = fields.CharField(max_length=50, null=True)
    full_name = fields.CharField(max_length=50, null=True)
    hashed_password = fields.CharField(max_length=256)
    disabled = fields.BooleanField(default=True)
    date_joined = fields.DatetimeField(auto_now_add=True)
    last_logged_in = fields.DatetimeField(auto_now=True)

    class Meta:
        ordering = ['username']


class Genre(models.Model):
    genre_id = fields.IntField(pk=True)
    genre_name = fields.CharField(max_length=15)

    class Meta:
        ordering = ['genre_name']


class Movie(models.Model):
    movie_id = fields.IntField(pk=True)
    movie_name = fields.CharField(max_length=30)
    director = fields.CharField(max_length=30, null=True)
    imdb_score = fields.FloatField()
    popularity = fields.FloatField()
    movie_poster = fields.TextField() 
    user = fields.ForeignKeyField("models.User", related_name="author", on_delete=fields.CASCADE)
    date_posted = fields.DatetimeField(auto_now_add=True)
    last_edited = fields.DatetimeField(auto_now=True)
    
    class Meta:
        # ordering = ['date_posted'] // acesending
        # ordering = ['-date_posted'] // decending
        ordering = ['-popularity']

    # def __str__(self):
    #     return self.movie_name

class MovieGenre(models.Model):
    moviegenre_id = fields.IntField(pk=True)
    movie = fields.ForeignKeyField(model_name='models.Movie', on_delete=fields.CASCADE)
    genre = fields.ForeignKeyField(model_name='models.Genre', on_delete=fields.CASCADE)
    
    class Meta:
        unique_together = (("movie", "genre"),)
