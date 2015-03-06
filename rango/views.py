from django.shortcuts import render
from django.http import HttpResponse

from models import Category, Page

# Create your views here.
def index(request):
    category_list = Category.objects.order_by('-likes')[:5]
    #context_dict  = {'categories': category_list}
    page_list     = Page.objects.order_by('-views')[:5]
    #page_dict  = {'pages':page_list}
    return render(request, 'rango/index.html',{'categories':category_list,'pages':page_list})

def category(request, category_name_slug):
    context_dict = {}
    try:
        category = Category.objects.get(slug=category_name_slug)
        context_dict['category_name'] = category.name

        pages = Page.objects.filter(category=category)
        context_dict['pages'] = pages
        context_dict['category'] = category
    except Category.DoesNotExist:
        pass
    return render(request, 'rango/category.html', context_dict)

def about(request):
    return HttpResponse("This is the about page <a href='/rango/'>Index</a>")
