from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from searches.models import Search
import requests
from django.conf import settings

URL = settings.SEARCH_API_URL

def get_data(url):
    # Получает данные из JSON-server API с проверкой структуры ответа
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Проверяем структуру ответа
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('products', [])
        else:
            raise Exception("Неверный формат данных от API")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Ошибка при запросе к API: {str(e)}")
    except ValueError as e:
        raise Exception(f"Ошибка при парсинге JSON: {str(e)}")

def search_products(query, all_products):
    # Ищет товары по запросу без учета регистра с релевантностью
    if not query or not all_products:
        return []
    
    query_lower = query.lower().strip()
    query_words = query_lower.split()
    
    matched_products = []
    
    for product in all_products:
        if not isinstance(product, dict):
            continue
        
        product_name = product.get('name', '')
        if not product_name:
            continue
        
        product_name_lower = str(product_name).lower()
        
        all_words_match = all(word in product_name_lower for word in query_words if word)
        
        if all_words_match:
            relevance = sum(len(word) for word in query_words if word in product_name_lower)
            matched_products.append({
                'product': product,
                'relevance': relevance
            })
    
    matched_products.sort(key=lambda x: x['relevance'], reverse=True)
    
    return [item['product'] for item in matched_products]

@login_required
def search(request):
    # Отображает список поисков текущего пользователя
    # Показываем только поиски текущего пользователя
    searches = Search.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'searches/search.html', {
        "searches": searches
    })

@login_required
def create_search(request):
    # Создает новый поиск товаров по API
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

            # Получаем URL и изображение первого товара для сохранения
            first_product_url = None
            first_product_image = None
            
            if matched_products:
                first_product = matched_products[0]
                first_product_url = first_product.get('product_url', '')
                first_product_image = first_product.get('image', '')

            # Создаем поиск и привязываем к текущему пользователю
            Search.objects.create(
                name=name, 
                price=price, 
                min_price=min_price, 
                price_history=0, 
                quantity=quantity, 
                image=first_product_image,
                product_url=first_product_url,
                user=request.user
            )
        
            return redirect('search')
        except Exception as e:
            error = f'Ошибка при создании поиска: {str(e)}'
            return render(request, 'searches/create_search.html', { 'error': error })

    return render(request, 'searches/create_search.html')

def sort_products_by_price(products):
    # Сортирует товары по возрастанию цены
    def get_price(product):
        price = product.get('price')
        if price is None:
            return float('inf')  # Товары без цены в конец списка
        try:
            return float(price)
        except (ValueError, TypeError):
            return float('inf')
    
    return sorted(products, key=get_price)

@login_required
def detail_search(request, id):
    # Отображает детали поиска с актуальными товарами из API
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
            # Сортируем товары по возрастанию цены
            products = sort_products_by_price(products)
    except Exception as e:
        # В случае ошибки просто показываем пустой список товаров
        products = []
    
    # Рассчитываем разницу в цене
    price_difference = float(search_obj.price) - float(search_obj.min_price)
    price_difference_abs = abs(price_difference)
    
    # Рассчитываем процент изменения для истории цен
    if float(search_obj.price_history) != 0:
        price_change_percent = ((float(search_obj.min_price) - float(search_obj.price_history)) / float(search_obj.price_history)) * 100
    else:
        price_change_percent = 0
    
    return render(request, 'searches/detail_search.html', {
        'search': search_obj,
        'products': products,
        'price_difference': price_difference,
        'price_difference_abs': price_difference_abs,
        'price_change_percent': price_change_percent
    })

@login_required
def update_search(request, id):
    # Обновляет данные поиска: минимальную цену и количество товаров
    search_obj = get_object_or_404(Search, id=id, user=request.user)
    
    try:
        items = get_data(URL)
        all_products = []
        
        if isinstance(items, list):
            all_products = items
        elif isinstance(items, dict):
            all_products = items.get('products', [])
        
        if all_products:
            products = search_products(search_obj.name, all_products)
            
            # Находим минимальную цену
            min_price = None
            for product in products:
                product_price = product.get('price')
                if product_price is not None:
                    try:
                        product_price = float(product_price)
                        if min_price is None or product_price < min_price:
                            min_price = product_price
                    except (ValueError, TypeError):
                        continue
            
            # Сохраняем старую минимальную цену в историю перед обновлением
            if min_price is not None and min_price != search_obj.min_price:
                search_obj.price_history = search_obj.min_price
            
            # Обновляем данные
            search_obj.min_price = min_price if min_price is not None else search_obj.price
            search_obj.quantity = len(products)
            search_obj.save()
            
    except Exception as e:
        # В случае ошибки просто оставляем старые данные
        pass
    
    return redirect('detail_search', id=id)

@login_required
def delete_search(request, id):
    # Удаляет поиск после подтверждения
    if request.method == 'POST':
        search_obj = get_object_or_404(Search, id=id, user=request.user)
        search_obj.delete()
        return redirect('search')
    
    # Если GET запрос, показываем страницу подтверждения
    search_obj = get_object_or_404(Search, id=id, user=request.user)
    return render(request, 'searches/confirm_delete.html', {'search': search_obj})
