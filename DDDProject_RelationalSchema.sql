CREATE TYPE order_status  AS ENUM ('issued', 'sent', 'received');
CREATE TYPE delivery_type AS ENUM ('standard', 'express');


--- TABLES ---
CREATE TABLE customer (
    customer_id  SERIAL PRIMARY KEY,
    name         VARCHAR(255) NOT NULL,
    balance      NUMERIC(12, 2) NOT NULL DEFAULT 0.00
);

CREATE TABLE customer_address (
    id           SERIAL PRIMARY KEY,
    customer_id  INT          NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    address      VARCHAR(255) NOT NULL
);

CREATE TABLE credit_card (
    card_id      SERIAL PRIMARY KEY,
    customer_id  INT          NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    number       VARCHAR(20)  NOT NULL,
    address      VARCHAR(255) NOT NULL
);

CREATE TABLE product (
    product_id   SERIAL PRIMARY KEY,
    name         VARCHAR(255) NOT NULL,
    category     VARCHAR(100),
    price        NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    type         VARCHAR(100),
    brand        VARCHAR(100),
    size         VARCHAR(50),
    description  TEXT
);

CREATE TABLE warehouse (
    warehouse_id  SERIAL PRIMARY KEY,
    address       VARCHAR(255) NOT NULL
);

CREATE TABLE stock (
    stock_id      SERIAL PRIMARY KEY,
    product_id    INT NOT NULL REFERENCES product(product_id)    ON DELETE CASCADE,
    warehouse_id  INT NOT NULL REFERENCES warehouse(warehouse_id) ON DELETE CASCADE,
    qnum          INT NOT NULL DEFAULT 0 CHECK (qnum >= 0),
    UNIQUE (product_id, warehouse_id)
);

CREATE TABLE staff_member (
    staff_id   SERIAL PRIMARY KEY,
    name       VARCHAR(255) NOT NULL,
    address    VARCHAR(255),
    salary     NUMERIC(12, 2),
    job_title  VARCHAR(100)
);

CREATE TABLE "order" (
    order_id     SERIAL PRIMARY KEY,
    customer_id  INT          NOT NULL REFERENCES customer(customer_id),
    status       order_status NOT NULL DEFAULT 'issued'
);


CREATE TABLE order_content (
	order_id     INT NOT NULL REFERENCES "order"(order_id) ON DELETE CASCADE,
    product_id   INT NOT NULL REFERENCES product(product_id),
    quantity     INT NOT NULL CHECK (quantity > 0),
    PRIMARY KEY  (order_id, product_id)
);


CREATE TABLE delivery_plan (
    delivery_id    SERIAL PRIMARY KEY,
    order_id       INT           NOT NULL UNIQUE REFERENCES "order"(order_id) ON DELETE CASCADE,
    type           delivery_type NOT NULL DEFAULT 'standard',
    price          NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    delivery_date  DATE,
    ship_date      DATE,
    CHECK (delivery_date IS NULL OR ship_date IS NULL OR delivery_date >= ship_date)
);


--- INDICES ---

CREATE INDEX idx_customer_address_cust  ON customer_address(customer_id);
CREATE INDEX idx_credit_card_cust       ON credit_card(customer_id);