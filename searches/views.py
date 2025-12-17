from django.shortcuts import render, redirect
from searches.models import Search
import requests

URL = 'https://dummyjson.com/products'

def get_data(url):
  response = requests.get(url)
  data = response.json()
  return data

def search(request):
  return render(request, 'searches/search.html', {
    "searches": Search.objects.all()
  })

def create_search(request):
  if request.method == 'POST':
    name = request.POST['name']
    price = request.POST['price']

    if not name or not price:
      error = 'Заполните необходимые поля'
      return render(request, 'searches/create_search.html', { 'error': error })
    
    items = get_data(URL)

    products = items['products']
    product = products[0]
    min_price = product['price']

    images = product['images']
    image = images[0]

    for product in products:
      if product['price'] < min_price:
        min_price = product['price']
        for img in product['images']:
          image = img

    print(image)
    quantity = len(products)

    Search.objects.create(name=name, price=price, min_price=min_price, price_history=0, quantity=quantity, image=image)
  
    print('Поиск успешно создан')
    return redirect('search')

  return render(request, 'searches/create_search.html')

def detail_search(request, id):
  search = Search.objects.get(id=id)

  search_name = search.name

  get_data(f"{URL}/{search_name}")