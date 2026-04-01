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


-- SELECT 
--   a.*,
--   b.payment_method,
--   d.daily_rate,
--   DATEDIFF(day, a.start_date, a.end_date) AS total_days,
--   total_days * d.daily_rate as total_amount 
-- FROM [easyrental_source].[reservations] a   
-- LEFT JOIN [easyrental_source].[payments] b ON a.id = b.reservation_id  
-- LEFT JOIN [easyrental_stg].[cars] c ON c.id = a.car_id
-- LEFT JOIN [easyrental_stg].[car_categories] d ON d.id = c.category_id


with cte AS 
(
SELECT 
  a.*,
  b.payment_method,
  d.daily_rate,
  DATEDIFF(day, a.start_date, a.end_date) AS total_days
FROM [easyrental_source].[reservations] a   
LEFT JOIN [easyrental_source].[payments] b ON a.id = b.reservation_id  
LEFT JOIN [easyrental_stg].[cars] c ON c.id = a.car_id
LEFT JOIN [easyrental_stg].[car_categories] d ON d.id = c.category_id
) 
INSERT INTO [easyrental_dwh].[fact_reservations]
select 
cte.*,
cte.total_days * cte.daily_rate as total_amount 
from cte 


