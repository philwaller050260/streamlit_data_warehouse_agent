CREATE TABLE [customer] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] nvarchar(255),
  [email_address] nvarchar(255),
  [address] nvarchar(255),
  [date_of_birth] date,
  [phone_number] nvarchar(255),
  [diver_license_number] nvarchar(255)
)
GO

CREATE TABLE [reservation] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [customer_id] int,
  [car_id] int,
  [pickup_branch_id] int,
  [return_branch_id] int,
  [pickup_start_date] date,
  [return_end_date] date,
  [booking_date] date
)
GO

CREATE TABLE [car] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [license_plate] nvarchar(255),
  [make] nvarchar(255),
  [model] nvarchar(255),
  [mileage] int,
  [fuel] nvarchar(255),
  [condition] nvarchar(255),
  [category_id] int,
  [branch_id] int
)
GO

CREATE TABLE [category] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [name] nvarchar(255),
  [daily_rate] decimal
)
GO

CREATE TABLE [branch] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [location] nvarchar(255),
  [manager] nvarchar(255),
  [contact_number] nvarchar(255)
)
GO

CREATE TABLE [payment] (
  [id] int PRIMARY KEY IDENTITY(1, 1),
  [reservation_id] int,
  [amount] decimal,
  [payment_type] nvarchar(255),
  [payment_date] date
)
GO

ALTER TABLE [reservation] ADD FOREIGN KEY ([customer_id]) REFERENCES [customer] ([id])
GO

ALTER TABLE [reservation] ADD FOREIGN KEY ([car_id]) REFERENCES [car] ([id])
GO

ALTER TABLE [reservation] ADD FOREIGN KEY ([pickup_branch_id]) REFERENCES [branch] ([id])
GO

ALTER TABLE [reservation] ADD FOREIGN KEY ([return_branch_id]) REFERENCES [branch] ([id])
GO

ALTER TABLE [car] ADD FOREIGN KEY ([category_id]) REFERENCES [category] ([id])
GO

ALTER TABLE [car] ADD FOREIGN KEY ([branch_id]) REFERENCES [branch] ([id])
GO

ALTER TABLE [payment] ADD FOREIGN KEY ([reservation_id]) REFERENCES [reservation] ([id])
GO
