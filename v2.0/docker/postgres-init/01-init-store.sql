CREATE TABLE IF NOT EXISTS branches (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    city VARCHAR(120) NOT NULL,
    address TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(120) NOT NULL,
    last_name VARCHAR(120) NOT NULL,
    position VARCHAR(120) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    salary NUMERIC(12, 2) NOT NULL CHECK (salary >= 0),
    branch_id INTEGER NOT NULL REFERENCES branches(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_branches_city ON branches(city);
CREATE INDEX IF NOT EXISTS idx_employees_branch_id ON employees(branch_id);

INSERT INTO branches (id, name, city, address)
VALUES
    (1, 'Central Store', 'Moscow', 'Prospekt Mira, 10'),
    (2, 'North Store', 'Saint Petersburg', 'Nevsky Prospect, 54'),
    (3, 'East Store', 'Kazan', 'Baumana Street, 18')
ON CONFLICT (id) DO NOTHING;

INSERT INTO employees (id, first_name, last_name, position, email, salary, branch_id)
VALUES
    (1, 'Ivan', 'Sokolov', 'Store Manager', 'ivan.sokolov@example.com', 120000.00, 1),
    (2, 'Elena', 'Smirnova', 'Sales Specialist', 'elena.smirnova@example.com', 85000.00, 1),
    (3, 'Pavel', 'Kuznetsov', 'Technician', 'pavel.kuznetsov@example.com', 92000.00, 2),
    (4, 'Maria', 'Petrova', 'Branch Manager', 'maria.petrova@example.com', 115000.00, 3)
ON CONFLICT (id) DO NOTHING;

SELECT setval('branches_id_seq', COALESCE((SELECT MAX(id) FROM branches), 1), true);
SELECT setval('employees_id_seq', COALESCE((SELECT MAX(id) FROM employees), 1), true);
