def products_serializer(products):
    payload = []
    content = {}

    for product in products:
        content = {
            "_id": product[0],
            "title": product[1],
            "slug": product[2],
            "description": product[3],
            "price": product[4],
            "category": product[5],
            "image": product[6],
            "countInStock": product[7],
            "offer": product[8],
            "origPrice": product[9],
            "rating": product[10],
            "reviews": product[11]
        }
        payload.append(content)
        content = {}

    return payload

def categories_serializer(categories):
    payload = []
    content = {}

    for category in categories:
        content = {
            "_id": category[0],
            "title": category[1],
            "slug": category[2]
        }
        payload.append(content)
        content = {}

    return payload

def orders_serializer(orders):
    payload = []
    content = {}

    for order in orders:
        content = {
            "user_id": order[0],
            "product_id": order[1],
            "orderdate": order[2],
            "price": order[3],
            "qty": order[4],
            "title": order[5]
        }
        payload.append(content)
        content = {}

    return payload

def prods_serializer(prods):
    payload = []
    content = {}

    for prod in prods:
        content = {
            "_id": prod[0],
            "_title": prod[1]
        }
        payload.append(content)
        content = {}
    return payload

def users_serializer(users):
    payload = []
    content = {}

    for user in users:
        content = {
            "_id": user[0],
            "name": user[1],
            "email": user[2],
            "isAdmin": user[3],
            "suspended": user[4],
        }
        payload.append(content)
        content = {}
    return payload