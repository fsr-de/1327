from django.shortcuts import render
from _1327.main.decorators import staff_required

@staff_required
def index(request):    
    return render(request, "staff_index.html")
