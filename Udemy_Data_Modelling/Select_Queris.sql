-- TRUNCATE TABLE [n_easyrental_dwh].[fact_reservations];

-- WITH reservation_data AS 
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
-- ),
-- dates_mapped AS
-- (
--   SELECT 
--     rd.customer_id,
--     rd.car_id,
--     rd.pickup_branch_id,
--     rd.return_branch_id,
--     rd.start_date,
--     rd.end_date,
--     rd.booking_date,
--     rd.payment_method,
--     rd.total_days,
--     rd.daily_rate,
--     d1.id AS start_date_id,
--     d2.id AS end_date_id,
--     d3.id AS booking_date_id,
--     rd.total_days * rd.daily_rate AS total_amount
--   FROM reservation_data rd
--   LEFT JOIN [n_easyrental_dwh].[dim_dates] d1 ON rd.start_date = d1.date
--   LEFT JOIN [n_easyrental_dwh].[dim_dates] d2 ON rd.end_date = d2.date
--   LEFT JOIN [n_easyrental_dwh].[dim_dates] d3 ON rd.booking_date = d3.date
-- )
-- INSERT INTO [n_easyrental_dwh].[fact_reservations]
-- (customer_id, car_id, pickup_branch_id, return_branch_id, start_date_id, end_date_id, booking_date_id, payment_method, total_days, total_amount)
-- SELECT 
--   customer_id,
--   car_id,
--   pickup_branch_id,
--   return_branch_id,
--   start_date_id,
--   end_date_id,
--   booking_date_id,
--   payment_method,
--   total_days,
--   total_amount
-- FROM dates_mapped

-- select * from [n_easyrental_dwh].[fact_reservations]

-- select * from [easyrental_stg].[reservations]

-- select count(category_name),category_name from [n_easyrental_dwh].[dim_cars]
-- GROUP BY category_name


-- select * from n_easyrental_dwh.dim_cars

-- select top 1 * from n_easyrental_dwh.dim_cars where category_name = 'SUV'

-- select top 1 * from n_easyrental_dwh.fact_reservations

-- select count(*) from n_easyrental_dwh.fact_reservations A
-- INNER JOIN n_easyrental_dwh.dim_cars B
-- on a.car_id = b.id where b.category_name = 'SUV'
