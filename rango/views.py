from datetime import datetime
from django.shortcuts import render,redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from models import Category, Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from rango.bing_search import run_query

def index(request):

    category_list = Category.objects.order_by('-likes')
    page_list     = Page.objects.order_by('-views')[:5]
    context_dict  = {'categories': category_list, 'pages':page_list}
    
    visits = request.session.get('visits')
    if not visits:
        visits = 1
    reset_last_visit_time = False
    last_visit = request.session.get('last_visit')
    if last_visit:
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")
   
        if (datetime.now() - last_visit_time).seconds > 5:
            # ...reassign the value of the cookie to +1 what it was before...
            visits += 1
            # ...and updtate the last_visit_cookie too.
            reset_last_visit_time = True
    else:
        # Cookie last_visit doesn't exist, so create it to the current date/time
        reset_last_visit_time = True

    if reset_last_visit_time:
        request.session['last_visit'] = str(datetime.now())
        request.session['visits'] = visits
    context_dict['visits'] = visits 
    response = render(request, 'rango/index.html', context_dict)

    return response

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
    return render(request, 'rango/about.html')

def add_category(request):

    #HTTP POST?
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        #Form validation
        if form.is_valid():
            #save the new category to the database 
            form.save(commit=True)
            #Call the index() view
            #user will see the homepage
            return index(request)
        else:
            #The supplier form contained errors
            #Just print them to the terminal
            print form.errors
    else:
        #If the request was not a POST, display the form to enter details
        form = CategoryForm()
    #Bad form (or form details), no form supplied...
    #Render the form with error messages (if any).
    return render(request, 'rango/add_category.html', {'form': form})

def add_page(request, category_name_slug):

    try:
        cat = Category.objects.get(slug=category_name_slug)
    except Category.DoesNotExist:
        cat = None

    if request.method == 'POST':
        form = PageForm(request.POST)
        if form.is_valid():
            if cat:
                page = form.save(commit=False)
                page.category = cat
                page.views = 0
                page.save()
                return category(request, category_name_slug)
        else:
            print form.errors
    else:
        form = PageForm()
        context_dict = {'form':form, 'category':cat}
    
    return render(request, 'rango/add_page.html', context_dict)

def search(request):
    
    result_list = []

    if request.method == 'POST':
        query = request.POST['query'].strip()

        if query:
            result_list = run_query(query)
    
    return render(request, 'rango/search.html', {'result_list': result_list})

def register(request):
    # A boolean value for telling the template whether the registration was successful
    # Set to False initially. Code changes value to true when registration 
    registered = False

    # If it's a HTTP POST, we're insterested in processed form data.
    if request.method == 'POST':
        # Attempt to grab information from the raw form information.
        # Note that we use of both UserForm and UserProfileForm
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # If the two forms are valid...
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data to the database.
            user = user_form.save()

            # Now we hash the password with the set_password method. 
            # Once hashed, we can update the user object.
            user.set_password(user.password)
            user.save()
            
            # Now sort out the UserProfile instance.
            # Since we need to set the user attribute ourselves, we set commit=False
            # This delays saving the model until we're ready to avoid integrity problems.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Did the user provide a profile picture?
            # If so, we need to get it from the input form and put it in the UserProfile model.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the UserProfile model instance.
            profile.save()

            # Update our variable to tell the temple registration was successful.
            registered = True

        # Invalid form or forms = mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()
    # Render the template depending on the context.
    return render(request,
                'rango/register.html',
                {'user_form': user_form, 'profile_form': profile_form, 'registered': registered}
        )

def user_login(request):

    # If the request is a HTTP POST, try to pull the relevant information
    if request.method == 'POST':
        # Gather the username and password provided by the user.
        # This information is obtained from the login form.
        # We use request.POST.get('<variable>') as opposed to request.POST['<variables>'],
        # because the request.POST.get('<variable>') returns None, if the value does not exist
        # while the request.POST['<variable>'] will raise key error exception
        username = request.POST.get('username')
        password  = request.POST.get('password')
        # Use Django's machinery to attempt to see if the username/password
        # combination is valid - a User object is returned if it is.
        user = authenticate(username=username, password=password)

        # If we have a User project, the details are correct 
        # If None, (Python's way of representing the absense of a value), 
        # no user with matching credentials was found.
        if user:
            # Is the account active? It could have been disabled.
            if user.is_active:
                # If the user is account is active and valid, we can log the user in.
                # We'll send the user to the homepage
                login(request, user)
                return HttpResponseRedirect('/rango/')
            else:
                # An inactive account was used - no logging in!
                return HttpResponse("Your Rango account is currently disabled.")
        else:
            # Bad login details were provided. So we can't log the user in.
            print "Invalid login details were provided: {0}, {1}".format(username,password)
            return HttpResponse("Invalid login details supplied.")


    # The request is not an HTTP POST, so return the login form
    # this scenario would most likely be an HTTP GET
    else:
        # No context variables to pass to the template system
        # hence the blank dictionary object
        return render(request, 'rango/login.html', {})

@login_required
def restricted(request):
    return HttpResponse("Since you're logged in, you can see this text")

# Use the login_required() decorator to ensure only those logged in can access the view.
@login_required
def user_logout(request):
    # Sinve we know the user is logged in, we can now log them out.
    logout(request)
    # Take the user back to the homepage
    return HttpResponseRedirect('/rango/')
