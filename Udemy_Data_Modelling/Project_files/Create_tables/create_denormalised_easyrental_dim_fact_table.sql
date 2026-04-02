CREATE TABLE [d_easyrental_dwh].[fact_reservations] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [customer_id] int,
  [car_id] int,
  [pickup_branch_id] int,
  [return_branch_id] int,
  [start_date] date,
  [end_date] date,
  [booking_date] date,
  [payment_method] nvarchar(255),
  [total_days] int,
  [total_amount] int
)


CREATE TABLE [d_easyrental_dwh].[dim_customers] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] nvarchar(255),
  [email] nvarchar(255),
  [phone] nvarchar(255),
  [driver_license_number] nvarchar(255),
  [date_of_birth] date
)


CREATE TABLE [d_easyrental_dwh].[dim_cars] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [license_plate] nvarchar(255),
  [model] nvarchar(255),
  [year] int,
  [category_name] nvarchar(255)
)


CREATE TABLE [d_easyrental_dwh].[dim_branches] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] nvarchar(255),
  [city] nvarchar(255),
  [capacity] int
)


CREATE TABLE [d_easyrental_dwh].[dim_dates] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [date] date,
  [year] int,
  [quarter] int,
  [month] int,
  [day] int,
  [weekday] nvarchar(255)
)


-- ALTER TABLE [fact_reservations] ADD FOREIGN KEY ([customer_id]) REFERENCES [dim_customers] ([id])
-- 

-- ALTER TABLE [fact_reservations] ADD FOREIGN KEY ([car_id]) REFERENCES [dim_cars] ([id])
-- 

-- ALTER TABLE [fact_reservations] ADD FOREIGN KEY ([pickup_branch_id]) REFERENCES [dim_branches] ([id])
-- 

-- ALTER TABLE [fact_reservations] ADD FOREIGN KEY ([return_branch_id]) REFERENCES [dim_branches] ([id])
-- 

-- ALTER TABLE [fact_reservations] ADD FOREIGN KEY ([start_date_id]) REFERENCES [dim_dates] ([id])
-- 

-- ALTER TABLE [fact_reservations] ADD FOREIGN KEY ([end_date_id]) REFERENCES [dim_dates] ([id])
-- 

-- ALTER TABLE [fact_reservations] ADD FOREIGN KEY ([booking_date_id]) REFERENCES [dim_dates] ([id])
-- 
