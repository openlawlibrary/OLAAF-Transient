from django.db import models
from django.core.validators import MinLengthValidator

# Create your models here.

class Commit(models.Model):
  sha = models.CharField(max_length=40)
  date = models.DateTimeField()

  def __str__(self):
    return 'sha={}, date={}'.format(self.sha, self.date)

class Hash(models.Model):
  value = models.CharField(max_length=64, validators=[MinLengthValidator(64)])
  path = models.CharField(max_length=200)
  start_commit = models.ForeignKey(Commit, on_delete=models.PROTECT, related_name='hash_start_commit')
  end_commit = models.ForeignKey(Commit, on_delete=models.PROTECT, null=True, related_name='hash_end_commit')

  def __str__(self):
    return 'path={}, hash={}, start_commit={}, end_commit={}'.format(self.path, self.value,
                                                                     self.start_commit,
                                                                     self.end_commit)
