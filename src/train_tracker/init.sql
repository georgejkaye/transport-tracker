CREATE TABLE Operator (
    operator_id TEXT PRIMARY KEY,
    operator_name TEXT NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT
);

CREATE TABLE Brand (
    brand_id TEXT PRIMARY KEY,
    brand_name TEXT NOT NULL,
    parent_operator TEXT NOT NULL,
    bg_colour TEXT,
    fg_colour TEXT,
    FOREIGN KEY (parent_operator) REFERENCES Operator(operator_id)
);

CREATE TABLE Stock (
    stock_class INT NOT NULL,
    subclass INT,
    name TEXT,
    CONSTRAINT stock_classes_unique UNIQUE NULLS NOT DISTINCT (stock_class, subclass)
);

CREATE TABLE CurrentStock (
    operator_id TEXT NOT NULL,
    brand_id TEXT,
    stock_class INT NOT NULL,
    subclass INT,
    FOREIGN KEY (operator_id) REFERENCES Operator(operator_id),
    FOREIGN KEY (brand_id) REFERENCES Brand(brand_id),
    FOREIGN KEY (stock_class, subclass) REFERENCES Stock(stock_class, subclass),
    CONSTRAINT current_stock_classes_unique UNIQUE NULLS NOT DISTINCT (operator_id, brand_id, stock_class, subclass)
);