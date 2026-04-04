import csv
import random
from datetime import datetime, timedelta

# Sample data
customers = [
    {"id": "C001", "name": "John Doe", "email": "john.doe@email.com"},
    {"id": "C002", "name": "Jane Smith", "email": "jane.smith@email.com"},
    {"id": "C003", "name": "Mike Johnson", "email": "mike.j@email.com"},
    {"id": "C004", "name": "Sarah Williams", "email": "sarah.w@email.com"},
    {"id": "C005", "name": "Tom Brown", "email": "tom.brown@email.com"},
]

restaurants = [
    {"id": "R001", "name": "Pizza Palace", "city": "London"},
    {"id": "R002", "name": "Curry House", "city": "Manchester"},
    {"id": "R003", "name": "Burger Barn", "city": "Birmingham"},
    {"id": "R004", "name": "Sushi Station", "city": "London"},
    {"id": "R005", "name": "Taco Fiesta", "city": "Leeds"},
]

couriers = [
    {"id": "COU001", "name": "Dave Smith"},
    {"id": "COU002", "name": "Bob Jones"},
    {"id": "COU003", "name": "Alice Green"},
    {"id": "COU004", "name": "Charlie Davis"},
]

dishes = [
    {"id": "D001", "name": "Margherita", "category": "Pizza", "price": 12.99},
    {"id": "D002", "name": "Pasta Carbonara", "category": "Pasta", "price": 14.99},
    {"id": "D003", "name": "Chicken Burger", "category": "Burger", "price": 10.99},
    {"id": "D004", "name": "Beef Burger", "category": "Burger", "price": 11.99},
    {"id": "D005", "name": "Chicken Tikka Masala", "category": "Curry", "price": 13.99},
    {"id": "D006", "name": "Vegetable Biryani", "category": "Curry", "price": 12.99},
    {"id": "D007", "name": "California Roll", "category": "Sushi", "price": 15.99},
    {"id": "D008", "name": "Spicy Tuna Roll", "category": "Sushi", "price": 16.99},
    {"id": "D009", "name": "Carne Asada Tacos", "category": "Mexican", "price": 9.99},
    {"id": "D010", "name": "Fish Tacos", "category": "Mexican", "price": 10.99},
]

payment_methods = ["Card", "PayPal", "Cash", "Apple Pay"]
ratings = [1, 2, 3, 4, 5]

# Generate orders
orders = []
order_id = 1
base_date = datetime(2025, 1, 1)

for i in range(500):
    customer = random.choice(customers)
    restaurant = random.choice(restaurants)
    courier = random.choice(couriers)
    dish = random.choice(dishes)
    
    order_date = base_date + timedelta(days=random.randint(0, 90))
    delivery_date = order_date + timedelta(hours=random.randint(1, 4))
    
    quantity = random.randint(1, 5)
    payment_method = random.choice(payment_methods)
    rating = random.choice(ratings)
    
    comments = [
        "Great!",
        "Good",
        "Excellent service",
        "A bit slow",
        "Perfect",
        "Could be better",
        "Loved it!",
        "Not satisfied",
        "Will order again",
        "Decent"
    ]
    comment = random.choice(comments)
    
    orders.append({
        "OrderID": f"ORD{order_id:05d}",
        "CustomerID": customer["id"],
        "CustomerName": customer["name"],
        "CustomerEmail": customer["email"],
        "RestaurantID": restaurant["id"],
        "RestaurantName": restaurant["name"],
        "RestaurantCity": restaurant["city"],
        "CourierID": courier["id"],
        "CourierName": courier["name"],
        "DishID": dish["id"],
        "DishName": dish["name"],
        "DishCategory": dish["category"],
        "Price": dish["price"],
        "Quantity": quantity,
        "OrderDate": order_date.strftime("%Y-%m-%d"),
        "DeliveryDate": delivery_date.strftime("%Y-%m-%d"),
        "PaymentMethod": payment_method,
        "Rating": rating,
        "Comments": comment
    })
    
    order_id += 1

# Write CSV
csv_file = "food_delivery_orders.csv"
fieldnames = [
    "OrderID", "CustomerID", "CustomerName", "CustomerEmail",
    "RestaurantID", "RestaurantName", "RestaurantCity",
    "CourierID", "CourierName",
    "DishID", "DishName", "DishCategory", "Price", "Quantity",
    "OrderDate", "DeliveryDate", "PaymentMethod", "Rating", "Comments"
]

with open(csv_file, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(orders)

print(f"✅ Generated {len(orders)} orders in {csv_file}")