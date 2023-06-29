from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel
from .restapis import get_request, get_dealers_from_cf, get_dealer_reviews_from_cf, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.
def static_pages(request):
    return render(request, 'djangoapp/static_pages.html')

# Create an `about` view to render a static about page
def about(request):
    return render(request, 'djangoapp/about.html')


# Create a `contact` view to return a static contact page
def contact(request):
    return render(request, 'djangoapp/contact.html')

# Create a `login_request` view to handle sign in request
def login_request(request):
    context = {}
    
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('djangoapp:index')
        else:
            return render(request, 'djangoapp/index.html', context)
    else:
        return render(request, 'djangoapp/index.html', context)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    print("Log out the user `{}`".format(request.user.username))
    logout(request)
    
    return redirect('djangoapp:index')

# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False

        try:
            User.objects.get(username=username)
            user_exist = True
        except:
            logger.debug("{} is new user".format(username))

        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else:
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/c21f65db-458f-4470-9b40-335efdfada2d/api/dealership"
        dealerships = get_dealers_from_cf(url)
        context = {'dealership_list': dealerships}
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    if request.method == "GET":
        dealer_name = request.GET.get('name')
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/c21f65db-458f-4470-9b40-335efdfada2d/api/review"
        reviews = get_dealer_reviews_from_cf(url, dealer_id)
        context = {'reviews_list': reviews, 'dealer_name': dealer_name, 'dealer_id': dealer_id}
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
@login_required
def add_review(request, dealer_id):
    if request.method== "GET":
        dealer_name = request.GET.get('name')
        cars = CarModel.objects.filter(dealer_id=dealer_id)
        context = {'cars': cars, 'dealer_id': dealer_id, 'dealer_name': dealer_name}
        return render(request, 'djangoapp/add_review.html', context)
    elif request.method == "POST":
        form = request.POST

        review = {
            "name": f"{request.user.first_name} {request.user.last_name}",
            "dealership": dealer_id,
            "review": form["content"],
            "purchase": "true" if form.get("purchase_check") == 'on' else "false",
        }
        
        if form.get("purchase_check"):
            car = CarModel.objects.get(pk=form["car"])
            review["purchase_date"] = datetime.strptime(form.get("purchase_date"), "%m/%d/%Y").isoformat() 
            review["car_make"] = car.car_make.name
            review["car_model"] = car.name
            review["car_year"] = car.year.strftime("%Y")

        json_payload = {'review': review}
        url = 'https://us-south.functions.appdomain.cloud/api/v1/web/c21f65db-458f-4470-9b40-335efdfada2d/api/add-review'
        response = post_request(url, json_payload)
        print(response)
        # return 'ok'
        return redirect('djangoapp:dealer_details', dealer_id=dealer_id)
    