from django.db import models
import json


# Create your models here.
class SavedLists(models.Model):
    inserted_date = models.DateField(auto_now=True)
    user = models.TextField(default=None)
    name = models.TextField(default=None)
    list = models.TextField(null=True)

    def set_list(self, list: [str]):
        self.list = json.dumps(list)

    def get_list(self) -> dict:
        return json.loads(self.list)

    def to_string(self) -> dict:
        return {
            "user": self.user,
            "name": self.name,
            "list": self.get_list(),
        }
