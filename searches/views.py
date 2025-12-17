from django.shortcuts import render
import requests

URL = 'https://dummyjson.com/products'

def get_data(url):
  response = requests.get(url)
  data = response.json()
  return data

def search(request):
  products = get_data(URL)

  print(products)

  return render(request, 'searches/search.html', {
    "products": products
  })