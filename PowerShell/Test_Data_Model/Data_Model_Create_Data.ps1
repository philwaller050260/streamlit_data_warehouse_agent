Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "

-- =========================
-- DIMENSION DATA
-- =========================

-- dim_products
INSERT INTO dim_product (product_id,product_name,product_category,product_genre,list_price,release_year,is_active)
VALUES
(101,'The Matrix','Movie','Sci-Fi',4.99,1999,1),
(102,'Toy Story','Movie','Animation',3.99,1995,1),
(103,'Titanic','Movie','Drama',4.49,1997,1),
(104,'Jurassic Park','Movie','Adventure',4.99,1993,1),
(105,'The Dark Knight','Movie','Action',5.49,2008,1),
(106,'Finding Nemo','Movie','Animation',3.99,2003,1),
(107,'Avengers Endgame','Movie','Action',5.99,2019,1),
(108,'Gladiator','Movie','Historical',4.99,2000,1),
(109,'Inception','Movie','Sci-Fi',5.49,2010,1),
(110,'Coco','Movie','Animation',3.99,2017,1);

-- dim_sales_date
INSERT INTO dim_sales_date (date_sk,full_date,day_number,day_name,week_number,month_number,month_name,quarter_number,year_number,is_weekend)
VALUES
(1,'2026-03-01',1,'Monday',9,3,'March',1,2026,0),
(2,'2026-03-02',2,'Tuesday',9,3,'March',1,2026,0),
(3,'2026-03-03',3,'Wednesday',9,3,'March',1,2026,0),
(4,'2026-03-04',4,'Thursday',9,3,'March',1,2026,0),
(5,'2026-03-05',5,'Friday',9,3,'March',1,2026,0),
(6,'2026-03-06',6,'Saturday',10,3,'March',1,2026,1),
(7,'2026-03-07',7,'Sunday',10,3,'March',1,2026,1);

-- dim_employee
INSERT INTO dim_employee (employee_id,first_name,last_name,job_title,hire_date,store_id,is_active)
VALUES
(201,'Alice','Smith','Sales Associate','2020-05-01',1,1),
(202,'Bob','Jones','Store Manager','2018-03-12',1,1),
(203,'Charlie','Brown','Cashier','2021-09-20',2,1),
(204,'Diana','Evans','Sales Associate','2019-07-15',2,1),
(205,'Evan','White','Store Manager','2017-11-01',3,1);

-- dim_customer
INSERT INTO dim_customer (customer_id,first_name,last_name,email,city,state,country,date_joined)
VALUES
(301,'John','Doe','john.doe@example.com','London','London','UK','2022-01-10'),
(302,'Jane','Roe','jane.roe@example.com','Manchester','Manchester','UK','2021-06-23'),
(303,'Peter','Parker','peter.parker@example.com','Bristol','Bristol','UK','2023-02-14'),
(304,'Mary','Jane','mary.jane@example.com','Leeds','West Yorkshire','UK','2020-11-30'),
(305,'Bruce','Wayne','bruce.wayne@example.com','Gotham','New York','US','2019-08-22');

-- dim_store
INSERT INTO dim_store (store_id,store_name,city,state,country,open_date,manager_name)
VALUES
(1,'Central Cinema','London','London','UK','2015-04-01','Bob Jones'),
(2,'North Cinema','Manchester','Manchester','UK','2016-05-15','Evan White'),
(3,'South Cinema','Bristol','Bristol','UK','2017-06-20','Anna Scott');

-- =========================
-- FACT TABLE DATA
-- =========================

INSERT INTO fact_video_sales (product_sk,date_sk,employee_sk,customer_sk,store_sk,quantity_sold,sales_amount,rental_duration_days,discount_amount,cost_amount)
VALUES
(1,1,1,1,1,1,4.99,3,0.00,2.50),
(2,2,2,2,1,2,7.98,2,0.00,4.00),
(3,3,3,3,2,1,4.49,5,0.50,2.00),
(4,4,4,4,2,3,14.97,1,1.00,6.00),
(5,5,5,5,3,1,5.49,4,0.00,2.75),
(6,6,1,2,1,2,7.98,3,0.50,4.00),
(7,7,2,3,1,1,3.99,2,0.00,2.00),
(8,1,3,4,2,1,5.99,1,0.00,3.50),
(9,2,4,5,3,2,10.98,5,1.00,5.50),
(10,3,5,1,3,1,4.99,3,0.00,2.50),
(1,4,1,2,1,3,14.97,4,0.00,7.50),
(2,5,2,3,1,1,3.99,2,0.00,2.00),
(3,6,3,4,2,2,8.98,3,0.50,4.00),
(4,7,4,5,2,1,4.99,2,0.00,2.50);

"