from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from searches.models import Search
import requests

URL = 'http://localhost:3000/products'

def get_data(url):
  """Получает данные из JSON-server API"""
  try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()  # Вызовет исключение для статусов 4xx, 5xx
    data = response.json()
    return data
  except requests.exceptions.RequestException as e:
    raise Exception(f"Ошибка при запросе к API: {str(e)}")
  except ValueError as e:
    raise Exception(f"Ошибка при парсинге JSON: {str(e)}")

def search_products(query, all_products):
  """
  Ищет товары по запросу без учета регистра.
  Учитывает все введенные символы для максимального совпадения.
  Структура товара: {"id": int, "name": str, "price": float}
  """
  if not query or not all_products:
    return []
  
  query_lower = query.lower().strip()
  query_words = query_lower.split()  # Разбиваем запрос на слова
  
  matched_products = []
  
  for product in all_products:
    # Получаем название товара (структура: {"id", "name", "price"})
    if not isinstance(product, dict):
      continue
    
    product_name = product.get('name', '')
    if not product_name:
      continue
    
    product_name_lower = str(product_name).lower()
    
    # Проверяем совпадение: все слова запроса должны присутствовать в названии
    all_words_match = all(word in product_name_lower for word in query_words if word)
    
    if all_words_match:
      # Вычисляем релевантность (количество совпавших символов)
      relevance = sum(len(word) for word in query_words if word in product_name_lower)
      matched_products.append({
        'product': product,
        'relevance': relevance
      })
  
  # Сортируем по релевантности (больше совпадений = выше в списке)
  matched_products.sort(key=lambda x: x['relevance'], reverse=True)
  
  # Возвращаем только товары
  return [item['product'] for item in matched_products]

@login_required
def search(request):
  # Показываем только поиски текущего пользователя
  searches = Search.objects.filter(user=request.user).order_by('-created_at')
  return render(request, 'searches/search.html', {
    "searches": searches
  })

@login_required
def create_search(request):
  if request.method == 'POST':
    name = request.POST['name']
    price = request.POST['price']

    if not name or not price:
      error = 'Заполните необходимые поля'
      return render(request, 'searches/create_search.html', { 'error': error })
    
    try:
      # Получаем все товары из JSON-server API
      # json-server возвращает массив напрямую: [{"id": 1, "name": "...", "price": ...}, ...]
      # или объект: {"products": [...]}
      items = get_data(URL)
      
      # Обрабатываем разные форматы ответа
      all_products = []
      if isinstance(items, list):
        # Если ответ - массив, используем его напрямую
        all_products = items
      elif isinstance(items, dict):
        # Если ответ - объект, извлекаем массив из ключа 'products'
        all_products = items.get('products', [])
      else:
        error = 'Неверный формат данных от API'
        return render(request, 'searches/create_search.html', { 'error': error })
      
      if not all_products:
        error = 'Товары не найдены в базе данных'
        return render(request, 'searches/create_search.html', { 'error': error })
      
      # Ищем товары по запросу пользователя
      matched_products = search_products(name, all_products)
      
      if not matched_products:
        error = f'Товары по запросу "{name}" не найдены. Попробуйте изменить поисковый запрос.'
        return render(request, 'searches/create_search.html', { 'error': error })
      
      # Находим минимальную цену среди найденных товаров
      min_price = None
      
      for product in matched_products:
        # Структура товара: {"id": int, "name": str, "price": float}
        product_price = product.get('price')
        
        if product_price is not None:
          try:
            product_price = float(product_price)
            if min_price is None or product_price < min_price:
              min_price = product_price
          except (ValueError, TypeError):
            continue
      
      # Если не нашли цену, используем желаемую цену пользователя
      if min_price is None:
        min_price = float(price)

      quantity = len(matched_products)

      # Создаем поиск и привязываем к текущему пользователю
      # Изображения нет в структуре данных, оставляем пустым
      Search.objects.create(
        name=name, 
        price=price, 
        min_price=min_price, 
        price_history=0, 
        quantity=quantity, 
        image='',  # В JSON БД нет изображений
        user=request.user
      )
    
      return redirect('search')
    except Exception as e:
      error = f'Ошибка при создании поиска: {str(e)}'
      return render(request, 'searches/create_search.html', { 'error': error })

  return render(request, 'searches/create_search.html')

@login_required
def detail_search(request, id):
  # Получаем поиск только если он принадлежит текущему пользователю
  search_obj = get_object_or_404(Search, id=id, user=request.user)
  
  # Получаем актуальные товары по запросу
  products = []
  try:
    items = get_data(URL)
    
    # Обрабатываем разные форматы ответа
    all_products = []
    if isinstance(items, list):
      # Если ответ - массив, используем его напрямую
      all_products = items
    elif isinstance(items, dict):
      # Если ответ - объект, извлекаем массив из ключа 'products'
      all_products = items.get('products', [])
    
    # Ищем товары по названию поиска
    if all_products:
      products = search_products(search_obj.name, all_products)
  except Exception as e:
    # В случае ошибки просто показываем пустой список товаров
    products = []
  
  return render(request, 'searches/detail_search.html', {
    'search': search_obj,
    'products': products
  })
