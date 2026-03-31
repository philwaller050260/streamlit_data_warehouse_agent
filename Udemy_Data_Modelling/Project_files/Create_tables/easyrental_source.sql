--- easyrental schema ---

CREATE TABLE [easyrental_source].[customers] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] nvarchar(255),
  [email] nvarchar(255),
  [date_of_birth] date,
  [phone] nvarchar(255),
  [driver_license_number] nvarchar(255)
)


CREATE TABLE [easyrental_source].[reservations] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [customer_id] int,
  [car_id] int,
  [pickup_branch_id] int,
  [return_branch_id] int,
  [start_date] date,
  [end_date] date,
  [booking_date] date
)


CREATE TABLE [easyrental_source].[cars] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [license_plate] nvarchar(255),
  [model] nvarchar(255),
  [year] int,
  [category_id] int,
  [current_branch_id] int
)


CREATE TABLE [easyrental_source].[car_categories] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] nvarchar(255),
  [daily_rate] decimal
)


CREATE TABLE [easyrental_source].[branches] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] nvarchar(255),
  [city] nvarchar(255),
  [capacity] int
)


CREATE TABLE [easyrental_source].[payments] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [reservation_id] int,
  [amount] decimal,
  [payment_method] nvarchar(255),
  [payment_date] date
)


-- ALTER TABLE [reservations] ADD FOREIGN KEY ([customer_id]) REFERENCES [customers] ([id])
-- 

-- ALTER TABLE [reservations] ADD FOREIGN KEY ([car_id]) REFERENCES [cars] ([id])
-- 

-- ALTER TABLE [reservations] ADD FOREIGN KEY ([pickup_branch_id]) REFERENCES [branches] ([id])
-- 

-- ALTER TABLE [reservations] ADD FOREIGN KEY ([return_branch_id]) REFERENCES [branches] ([id])
-- 

-- ALTER TABLE [cars] ADD FOREIGN KEY ([category_id]) REFERENCES [car_categories] ([id])
-- 

-- ALTER TABLE [cars] ADD FOREIGN KEY ([branch_id]) REFERENCES [branches] ([id])
-- 

-- ALTER TABLE [payments] ADD FOREIGN KEY ([reservation_id]) REFERENCES [reservations] ([id])
-- 


