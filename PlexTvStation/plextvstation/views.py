import os
from pathlib import Path
from django.shortcuts import render
from .bin.LIB import LIB

lib = LIB(home=str(Path(os.path.dirname(os.path.realpath(__file__)))))


def index(request):
    lib.write_log("Index call")
    context = {}

    return render(request, template_name="plextvstation/index.html", context=context)

