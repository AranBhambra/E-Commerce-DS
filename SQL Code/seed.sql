-- Seed test data

INSERT INTO users (username, password_hash, firstName, lastName, email, role, status) VALUES
('user1', 'hash1', 'Alice', 'Smith', 'alice.smith@example.com', 'customer', 'active'),
('user2', 'hash2', 'Bob', 'Johnson', 'bob.johnson@example.com', 'team', 'active'),
('user3', 'hash3', 'Carol', 'Williams', 'carol.williams@example.com', 'customer', 'pending'),
('user4', 'hash4', 'David', 'Brown', 'david.brown@example.com', 'team', 'inactive'),
('user5', 'hash5', 'Emma', 'Jones', 'emma.jones@example.com', 'customer', 'active'),
('user6', 'hash6', 'Frank', 'Garcia', 'frank.garcia@example.com', 'team', 'active'),
('user7', 'hash7', 'Grace', 'Martinez', 'grace.martinez@example.com', 'customer', 'inactive'),
('user8', 'hash8', 'Hank', 'Rodriguez', 'hank.rodriguez@example.com', 'team', 'pending'),
('user9', 'hash9', 'Ivy', 'Lee', 'ivy.lee@example.com', 'customer', 'active'),
('user10', 'hash10', 'Jack', 'Walker', 'jack.walker@example.com', 'team', 'inactive');

INSERT INTO products (name, description, price) VALUES 
('Product1', 'Description of Product1', 10.00),
('Product2', 'Description of Product2', 15.50),
('Product3', 'Description of Product3', 25.00),
('Product4', 'Description of Product4', 40.00),
('Product5', 'Description of Product5', 30.00),
('Product6', 'Description of Product6', 50.00),
('Product7', 'Description of Product7', 45.00),
('Product8', 'Description of Product8', 20.00),
('Product9', 'Description of Product9', 35.00),
('Product10', 'Description of Product10', 60.00);

INSERT INTO product_inventory (product_id, stock) VALUES 
(1, 100),
(2, 50),
(3, 30),
(4, 20),
(5, 60),
(6, 10),
(7, 25),
(8, 40),
(9, 15),
(10, 5);

