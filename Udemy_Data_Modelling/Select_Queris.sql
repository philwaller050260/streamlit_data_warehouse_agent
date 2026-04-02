-- select * from easyrental_source.branches

-- select * from [easyrental_source].[cars]

-- select * from [easyrental_stg].[cars]
-- select * from [easyrental_dwh].[dim_branches]

-- select * from [easyrental_dwh].[dim_customers]


-- select top 10* from [easyrental_stg].[car_categories]
-- select top 10 * from [easyrental_stg].[cars]

-- select a.id,a.license_plate,a.model,a.year, b.name as category_name
-- from [easyrental_stg].[cars] a
-- left OUTER JOIN  [easyrental_stg].[car_categories] b on a.category_id = b.id


-- TRUNCATE TABLE [easyrental_dwh].[dim_cars]
-- INSERT INTO [easyrental_dwh].[dim_cars]
-- SELECT 
--        a.license_plate,
--        a.model,
--        a.year,
--        b.name AS category_name
-- FROM [easyrental_stg].[cars] a
-- LEFT OUTER JOIN [easyrental_stg].[car_categories] b ON a.category_id = b.id


-- select model,year,count(model) as model_count from [easyrental_stg].[cars]
-- GROUP BY model,year 



-- select model,year from [easyrental_stg].[cars]
-- GROUP BY year,model
-- select name,email,count(name) from [easyrental_source].[customers]
-- GROUP BY name,email

-- select model,count(model) count_of_model, year from [easyrental_stg].[cars]
-- where model = 'Honda Civic' and [year] = 2017
-- GROUP BY model, year 

--  select * from [easyrental_stg].[cars]
--  where model = 'Honda Civic' and year = 2017


-- select top 1 * from  [easyrental_stg].[car_categories] where id = 5
-- select top 1 * from [easyrental_stg].[cars] where category_id = 5

-- select 
-- license_plate,model,id
-- from [easyrental_stg].[cars] 
-- where category_id IN (
--     select id from [easyrental_stg].[car_categories]
--     where id = 5
-- )


-- cars dim
-- TRUNCATE TABLE [easyrental_dwh].[dim_cars]
-- INSERT INTO [easyrental_dwh].[dim_cars]
-- SELECT 
--        a.license_plate,
--        a.model,
--        a.year,
--        b.name AS category_name
-- FROM [easyrental_stg].[cars] a
-- LEFT OUTER JOIN [easyrental_stg].[car_categories] b ON a.category_id = b.id



-- # denormalised fact_reservations

-- WITH cte AS 
-- (
--   SELECT 
--     a.customer_id,
--     a.car_id,
--     a.pickup_branch_id,
--     a.return_branch_id,
--     a.start_date,
--     a.end_date,
--     a.booking_date,
--     b.payment_method,
--     d.daily_rate,
--     DATEDIFF(day, a.start_date, a.end_date) AS total_days
--   FROM [easyrental_source].[reservations] a   
--   LEFT JOIN [easyrental_source].[payments] b ON a.id = b.reservation_id  
--   LEFT JOIN [easyrental_stg].[cars] c ON c.id = a.car_id
--   LEFT JOIN [easyrental_stg].[car_categories] d ON d.id = c.category_id
-- )
-- INSERT INTO [d_easyrental_dwh].[fact_reservations]
-- SELECT 
--   customer_id,
--   car_id,
--   pickup_branch_id,
--   return_branch_id,
--   start_date,
--   end_date,
--   booking_date,
--   payment_method,
--   total_days,
--   total_days * daily_rate AS total_amount
-- FROM cte


-- # normalised fact dimensions

WITH reservation_data AS 
(
  SELECT 
    a.id,
    a.customer_id,
    a.car_id,
    a.pickup_branch_id,
    a.return_branch_id,
    a.start_date,
    a.end_date,
    a.booking_date,
    b.payment_method,
    d.daily_rate,
    DATEDIFF(day, a.start_date, a.end_date) AS total_days
  FROM [easyrental_source].[reservations] a   
  LEFT JOIN [easyrental_source].[payments] b ON a.id = b.reservation_id  
  LEFT JOIN [easyrental_stg].[cars] c ON c.id = a.car_id
  LEFT JOIN [easyrental_stg].[car_categories] d ON d.id = c.category_id
),
dates_mapped AS
(
  SELECT 
    rd.*,
    d1.id AS start_date_id,
    d2.id AS end_date_id,
    d3.id AS booking_date_id,
    rd.total_days * rd.daily_rate AS total_amount
  FROM reservation_data rd
  LEFT JOIN [n_easyrental_dwh].[dim_dates] d1 ON rd.start_date = d1.date
  LEFT JOIN [n_easyrental_dwh].[dim_dates] d2 ON rd.end_date = d2.date
  LEFT JOIN [n_easyrental_dwh].[dim_dates] d3 ON rd.booking_date = d3.date
)
INSERT INTO [n_easyrental_dwh].[fact_reservations]
SELECT 
  id,
  customer_id,
  car_id,
  pickup_branch_id,
  return_branch_id,
  start_date_id,
  end_date_id,
  booking_date_id,
  payment_method,
  total_days,
  total_amount
FROM dates_mapped