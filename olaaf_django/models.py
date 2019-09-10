from django.core.validators import MinLengthValidator
from django.db import models

# Create your models here.


class Repository(models.Model):
    name = models.CharField(max_length=60)

    def __str__(self):
        return self.name


class Edition(models.Model):
    date = models.DateField()
    name = models.CharField(max_length=10)
    repository = models.ForeignKey(Repository, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('repository', 'name')
        indexes = [
            models.Index(fields=['repository', 'name'])
        ]

    def __str__(self):
        return 'repository={}, name={}, date={}'.format(self.repository, self.name, self.date)


class Commit(models.Model):
    sha = models.CharField(max_length=40)
    date = models.DateField()
    document = models.CharField(max_length=100)
    revoked = models.BooleanField(default=False)
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)

    class Meta:
        unique_together = [('edition', 'sha')]  # not ready to add this yet ('date', 'document')]
        indexes = [
            models.Index(fields=['edition', 'sha']),
            models.Index(fields=['date', 'id'])
        ]

    def __str__(self):
        return 'sha={}, date={}'.format(self.sha, self.date)


class Path(models.Model):
    filesystem = models.CharField(max_length=260)
    url = models.CharField(max_length=260)
    search_path = models.CharField(max_length=200, null=True)
    citation = models.CharField(max_length=100, null=True)
    edition = models.ForeignKey(Edition, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('filesystem', 'edition')
        indexes = [
            models.Index(fields=['filesystem', 'edition']),
            models.Index(fields=['url', 'edition'])
        ]

    def __str__(self):
        return 'filesystem path: {}, url={}, citation={}, edition={}, search_path={}'. \
            format(self.filesystem, self.url, self.citation, self.edition, self.search_path)


class Hash(models.Model):
    BITSTREAM = 'B'
    RENDERED = 'R'
    TYPE_CHOICES = [
        (BITSTREAM, 'Bitstream'),
        (RENDERED, 'Rendered')
    ]
    value = models.CharField(max_length=64, validators=[MinLengthValidator(64)])
    path = models.ForeignKey(Path, on_delete=models.CASCADE)
    start_commit = models.ForeignKey(Commit, on_delete=models.CASCADE,
                                     related_name='hash_start_commit')
    end_commit = models.ForeignKey(Commit, on_delete=models.SET_NULL,
                                   null=True, related_name='hash_end_commit')
    hash_type = models.CharField(max_length=1, choices=TYPE_CHOICES, default=BITSTREAM)

    class Meta:
        unique_together = ('path', 'value', 'hash_type')
        indexes = [
            models.Index(fields=['path', 'value', 'hash_type'])
        ]

    def __str__(self):
        return 'path={}, hash={}, start_commit={}, end_commit={}, type={}'.format(self.path, self.value,
                                                                                  self.start_commit,
                                                                                  self.end_commit,
                                                                                  self.hash_type)
