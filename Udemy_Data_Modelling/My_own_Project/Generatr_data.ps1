# Generate realistic food delivery orders CSV

$firstNames = @("John", "Jane", "Mike", "Sarah", "Tom", "Emma", "David", "Lisa", "James", "Rachel", 
               "Chris", "Amy", "Daniel", "Sophie", "Robert", "Olivia", "Paul", "Emily", "Mark", "Jessica")
$lastNames = @("Doe", "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez",
              "Martinez", "Wilson", "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "White")

# Customers
$customers = @()
for ($i = 1; $i -le 100; $i++) {
    $firstName = $firstNames[(Get-Random -Maximum $firstNames.Count)]
    $lastName = $lastNames[(Get-Random -Maximum $lastNames.Count)]
    $customers += @{
        id = "C{0:D3}" -f $i
        name = "$firstName $lastName"
        email = "cust$i@email.com"
    }
}

# Restaurants
$restaurants = @(
    @{id = "R001"; name = "Pizza Palace"; city = "London"},
    @{id = "R002"; name = "Curry House"; city = "Manchester"},
    @{id = "R003"; name = "Burger Barn"; city = "Birmingham"},
    @{id = "R004"; name = "Sushi Station"; city = "London"},
    @{id = "R005"; name = "Taco Fiesta"; city = "Leeds"},
    @{id = "R006"; name = "Thai Kitchen"; city = "Edinburgh"},
    @{id = "R007"; name = "Greek Taverna"; city = "Bristol"},
    @{id = "R008"; name = "Vietnamese Pho"; city = "Manchester"},
    @{id = "R009"; name = "Korean BBQ"; city = "London"},
    @{id = "R010"; name = "Italian Trattoria"; city = "Oxford"}
)

# Couriers
$couriers = @()
for ($i = 1; $i -le 20; $i++) {
    $firstName = $firstNames[(Get-Random -Maximum $firstNames.Count)]
    $lastName = $lastNames[(Get-Random -Maximum $lastNames.Count)]
    $couriers += @{
        id = "COU{0:D3}" -f $i
        name = "$firstName $lastName"
    }
}

# Dishes
$dishes = @(
    @{id = "D001"; name = "Margherita"; category = "Pizza"; price = 12.99},
    @{id = "D002"; name = "Pasta Carbonara"; category = "Pasta"; price = 14.99},
    @{id = "D003"; name = "Chicken Burger"; category = "Burger"; price = 10.99},
    @{id = "D004"; name = "Beef Burger"; category = "Burger"; price = 11.99},
    @{id = "D005"; name = "Chicken Tikka Masala"; category = "Curry"; price = 13.99},
    @{id = "D006"; name = "Vegetable Biryani"; category = "Curry"; price = 12.99},
    @{id = "D007"; name = "California Roll"; category = "Sushi"; price = 15.99},
    @{id = "D008"; name = "Spicy Tuna Roll"; category = "Sushi"; price = 16.99},
    @{id = "D009"; name = "Carne Asada Tacos"; category = "Mexican"; price = 9.99},
    @{id = "D010"; name = "Fish Tacos"; category = "Mexican"; price = 10.99},
    @{id = "D011"; name = "Pad Thai"; category = "Thai"; price = 11.99},
    @{id = "D012"; name = "Green Curry"; category = "Thai"; price = 13.49},
    @{id = "D013"; name = "Souvlaki"; category = "Greek"; price = 12.49},
    @{id = "D014"; name = "Moussaka"; category = "Greek"; price = 13.99},
    @{id = "D015"; name = "Pho Beef"; category = "Vietnamese"; price = 10.99},
    @{id = "D016"; name = "Banh Mi"; category = "Vietnamese"; price = 9.99},
    @{id = "D017"; name = "Bibimbap"; category = "Korean"; price = 12.99},
    @{id = "D018"; name = "Korean BBQ"; category = "Korean"; price = 17.99},
    @{id = "D019"; name = "Lasagna"; category = "Italian"; price = 14.99},
    @{id = "D020"; name = "Risotto"; category = "Italian"; price = 15.49}
)

$paymentMethods = @("Card", "PayPal", "Cash", "Apple Pay", "Google Pay", "Bank Transfer")
$ratings = @(1, 2, 3, 4, 5)
$comments = @(
    "Great!", "Good", "Excellent service", "A bit slow", "Perfect",
    "Could be better", "Loved it!", "Not satisfied", "Will order again", "Decent",
    "Amazing", "Disappointing", "Highly recommend", "Average", "Outstanding",
    "Mediocre", "Fantastic", "Poor", "Great value", "Worth it"
)

# Generate orders
$orders = @()
$orderId = 1
$baseDate = Get-Date "2025-01-01"

for ($i = 0; $i -lt 1000; $i++) {
    $customer = $customers[(Get-Random -Maximum $customers.Count)]
    $restaurant = $restaurants[(Get-Random -Maximum $restaurants.Count)]
    $courier = $couriers[(Get-Random -Maximum $couriers.Count)]
    $dish = $dishes[(Get-Random -Maximum $dishes.Count)]
    
    $orderDate = $baseDate.AddDays((Get-Random -Maximum 91))
    $deliveryDate = $orderDate.AddHours((Get-Random -Minimum 1 -Maximum 5))
    
    $quantity = Get-Random -Minimum 1 -Maximum 6
    $paymentMethod = $paymentMethods[(Get-Random -Maximum $paymentMethods.Count)]
    $rating = $ratings[(Get-Random -Maximum $ratings.Count)]
    $comment = $comments[(Get-Random -Maximum $comments.Count)]
    
    $order = [PSCustomObject]@{
        OrderID = "ORD{0:D5}" -f $orderId
        CustomerID = $customer.id
        CustomerName = $customer.name
        CustomerEmail = $customer.email
        RestaurantID = $restaurant.id
        RestaurantName = $restaurant.name
        RestaurantCity = $restaurant.city
        CourierID = $courier.id
        CourierName = $courier.name
        DishID = $dish.id
        DishName = $dish.name
        DishCategory = $dish.category
        Price = $dish.price
        Quantity = $quantity
        OrderDate = $orderDate.ToString("yyyy-MM-dd")
        DeliveryDate = $deliveryDate.ToString("yyyy-MM-dd")
        PaymentMethod = $paymentMethod
        Rating = $rating
        Comments = $comment
    }
    
    $orders += $order
    $orderId++
}

# Write CSV
$csvFile = "food_delivery_orders.csv"
$orders | Export-Csv -Path $csvFile -NoTypeInformation -Encoding UTF8

Write-Host "✅ Generated $($orders.Count) orders in $csvFile"
Write-Host "📊 Columns: 19"