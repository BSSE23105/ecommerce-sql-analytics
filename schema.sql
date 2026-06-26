CREATE TABLE IF NOT exists customers (
    customer_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100),
    email VARCHAR(100),
    city VARCHAR(50),
    signup_date DATE
);
CREATE TABLE IF NOT exists products (
    product_id SERIAL PRIMARY KEY,
    title VARCHAR(150),
    category VARCHAR(50),
    price NUMERIC(10,2)
);

CREATE TABLE IF NOT exists orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(customer_id),
    product_id INT REFERENCES products(product_id),
    quantity INT,
    order_date DATE,
    status VARCHAR(20)
);

CREATE TABLE IF NOT exists payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(order_id),
    payment_date DATE,
    amount NUMERIC(10,2),
    method VARCHAR(20)
);

