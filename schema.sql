CREATE TABLE IF NOT exists customers (
    customer_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    city VARCHAR(50) NOT NULL,
    signup_date DATE
);
CREATE TABLE IF NOT exists products (
    product_id SERIAL PRIMARY KEY,
    title VARCHAR(150) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price NUMERIC(10,2) NOT NULL
);

CREATE TABLE IF NOT exists orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    product_id INT NOT NULL REFERENCES products(product_id),
    quantity INT NOT NULL CHECK (quantity > 0),
    order_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('completed', 'pending', 'returned', 'cancelled'))
);

CREATE TABLE IF NOT exists payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL REFERENCES orders(order_id),
    payment_date DATE NOT NULL,
    amount NUMERIC(10,2) NOT NULL CHECK (amount > 0),
    method VARCHAR(20) NOT NULL
);
