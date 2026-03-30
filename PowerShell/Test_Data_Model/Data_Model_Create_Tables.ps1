Invoke-Sqlcmd -ServerInstance pw-sql-svr-01.database.windows.net -Database pw-sql-db-01 -Username sqladmin -Password $pwd -Query "

CREATE TABLE dim_product (
    product_sk INT IDENTITY(1,1) PRIMARY KEY,
    product_id INT,                 -- business key from source system
    product_name VARCHAR(100),
    product_category VARCHAR(50),
    product_genre VARCHAR(50),
    list_price DECIMAL(10,2),
    release_year INT,
    is_active BIT
);


CREATE TABLE dim_sales_date (
    date_sk INT PRIMARY KEY,
    full_date DATE,
    day_number INT,
    day_name VARCHAR(20),
    week_number INT,
    month_number INT,
    month_name VARCHAR(20),
    quarter_number INT,
    year_number INT,
    is_weekend BIT
);


CREATE TABLE dim_employee (
    employee_sk INT IDENTITY(1,1) PRIMARY KEY,
    employee_id INT,              -- business key
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    job_title VARCHAR(50),
    hire_date DATE,
    store_id INT,
    is_active BIT
);


CREATE TABLE dim_customer (
    customer_sk INT IDENTITY(1,1) PRIMARY KEY,
    customer_id INT,              -- business key
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    email VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    date_joined DATE
);

CREATE TABLE dim_store (
    store_sk INT IDENTITY(1,1) PRIMARY KEY,
    store_id INT,                 -- business key
    store_name VARCHAR(100),
    city VARCHAR(50),
    state VARCHAR(50),
    country VARCHAR(50),
    open_date DATE,
    manager_name VARCHAR(100)
);

CREATE TABLE fact_video_sales (
    sales_sk BIGINT IDENTITY(1,1) PRIMARY KEY,

    product_sk INT,
    date_sk INT,
    employee_sk INT,
    customer_sk INT,
    store_sk INT,

    quantity_sold INT,
    sales_amount DECIMAL(12,2),
    rental_duration_days INT,
    discount_amount DECIMAL(10,2),
    cost_amount DECIMAL(10,2)
);

"