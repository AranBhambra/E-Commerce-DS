SET GLOBAL max_allowed_packet = 104857600; -- 100MB
SET GLOBAL wait_timeout = 28800; -- 8 hours


-- to drop the 3 database instances.
DROP DATABASE `e_store_a`;
DROP DATABASE `e_store_b`;
DROP DATABASE `e_store_c`;

-- to create the 3 database instances.
CREATE DATABASE
    IF NOT EXISTS e_store_a DEFAULT CHARACTER SET = 'utf8mb4';
CREATE DATABASE
    IF NOT EXISTS e_store_b DEFAULT CHARACTER SET = 'utf8mb4';
CREATE DATABASE
    IF NOT EXISTS e_store_c DEFAULT CHARACTER SET = 'utf8mb4';
    
 -- create the tables for the each database instance  
CREATE TABLE
	IF NOT EXISTS users (
		`user_id` INT PRIMARY KEY AUTO_INCREMENT,
		`username` VARCHAR(50) UNIQUE NOT NULL,
		`password_hash` VARCHAR(255) NOT NULL,
		`firstName` varchar(50) NOT NULL,
        `lastName` varchar(50) NOT NULL,
		`email` VARCHAR(100) UNIQUE NOT NULL,
		`role` ENUM('customer', 'team') NOT NULL DEFAULT 'customer',
		`status` ENUM(
            'pending',
            'active',
            'inactive'
        ) NOT NULL,
		`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		`updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
	);
    
CREATE TABLE
	IF NOT EXISTS products (
		`product_id` INT PRIMARY KEY AUTO_INCREMENT,
		`name` VARCHAR(100) NOT NULL,
		`description` TEXT,
		`price` DECIMAL(10, 2) NOT NULL,
		`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
	);

CREATE TABLE 
	IF NOT EXISTS product_inventory (
		`inventory_id` INT PRIMARY KEY AUTO_INCREMENT,
		`product_id` INT,
		`stock` INT DEFAULT 0,
		`last_updated` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
		FOREIGN KEY (product_id) REFERENCES products(product_id)
	);

CREATE TABLE
	IF NOT EXISTS carts (
		`cart_id` INT PRIMARY KEY AUTO_INCREMENT,
		`user_id` INT,
		`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(user_id)
	);

CREATE TABLE
	IF NOT EXISTS cart_items (
		`cart_item_id` INT PRIMARY KEY AUTO_INCREMENT,
		`cart_id` INT,
		`product_id` INT,
		`quantity` INT NOT NULL,
		`added_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (cart_id) REFERENCES carts(cart_id),
		FOREIGN KEY (product_id) REFERENCES products(product_id),
        -- combine unique key
		UNIQUE KEY uniq_cart_items (cart_id, product_id)
        
	);

CREATE TABLE 
	IF NOT EXISTS orders (
		`order_id` INT PRIMARY KEY AUTO_INCREMENT,
		`user_id` INT,
		`total_amount` DECIMAL(10, 2) NOT NULL,
		`status` VARCHAR(20) DEFAULT 'Pending',
		`created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		`updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES users(user_id)
        
	);

CREATE TABLE
	IF NOT EXISTS order_items (
		`order_item_id` INT PRIMARY KEY AUTO_INCREMENT,
		`order_id` INT,
		`product_id` INT,
		`quantity` INT NOT NULL,
		`price` DECIMAL(10, 2) NOT NULL,
		FOREIGN KEY (order_id) REFERENCES orders(order_id),
		FOREIGN KEY (product_id) REFERENCES products(product_id)

	);
    
CREATE TABLE
	IF NOT EXISTS payments (
		`payment_id` INT PRIMARY KEY AUTO_INCREMENT,
		`order_id` INT,
		`amount` DECIMAL(10, 2) NOT NULL,
		`payment_date` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		`status` VARCHAR(20) DEFAULT 'Pending',
		`payment_method` VARCHAR(50),
		FOREIGN KEY (order_id) REFERENCES orders(order_id)
	);

-- sync fail table
CREATE TABLE sync_failures (
    sync_id INT AUTO_INCREMENT PRIMARY KEY,         
    user_id INT NOT NULL,                          
    action VARCHAR(50) NOT NULL,                   -- process type'add_to_cart', 'checkout'
    data JSON NOT NULL,                            -- detailed process data
    source_server VARCHAR(10) NOT NULL,            -- source server name, 'A'
    target_server VARCHAR(10) NOT NULL,            -- target server name 'B' , 'C', 'all'
    progress INT NOT NULL DEFAULT 0,               -- process steps, step 1,..., step 4 
    additional_data JSON DEFAULT NULL,             -- save more info about fail data
    last_attempt DATETIME DEFAULT NOW(),          
    status ENUM('pending', 'completed') DEFAULT 'pending', -- sync status
    created_at DATETIME DEFAULT NOW(),             
    updated_at DATETIME DEFAULT NOW() ON UPDATE NOW(), 
    FOREIGN KEY (user_id) REFERENCES users(user_id),

    -- combine unique key
    UNIQUE KEY uniq_sync_failures (user_id, action, source_server, target_server)
);
ALTER TABLE sync_failures AUTO_INCREMENT = 1;
