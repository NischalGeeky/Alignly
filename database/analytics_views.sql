-- SQLite analytical views for Tableau export
-- 1. Initiative Overview
CREATE VIEW IF NOT EXISTS vw_initiative_overview AS
SELECT
    i.id AS initiative_id,
    i.code,
    i.name,
    d.name AS department,
    e.full_name AS owner,
    i.priority,
    i.status,
    i.progress_pct,
    i.start_date,
    i.target_date,
    MAX(u.update_date) AS latest_update_date
FROM initiatives i
JOIN departments d ON i.department_id = d.id
JOIN employees e ON i.owner_id = e.id
LEFT JOIN initiative_updates u ON u.initiative_id = i.id
GROUP BY i.id, i.code, i.name, d.name, e.full_name, i.priority, i.status, i.progress_pct, i.start_date, i.target_date;

-- 2. Milestone Health
CREATE VIEW IF NOT EXISTS vw_milestone_health AS
SELECT
    m.id AS milestone_id,
    m.name AS milestone_name,
    i.code AS initiative_code,
    d.name AS department,
    e.full_name AS owner,
    m.planned_date,
    m.actual_date,
    m.status
FROM milestones m
JOIN initiatives i ON m.initiative_id = i.id
JOIN departments d ON i.department_id = d.id
JOIN employees e ON m.owner_id = e.id;

-- 3. Department Performance
CREATE VIEW IF NOT EXISTS vw_department_performance AS
SELECT
    d.id AS department_id,
    d.name AS department,
    COUNT(i.id) AS total_initiatives,
    SUM(CASE WHEN i.status = 'Completed' THEN 1 ELSE 0 END) AS completed_initiatives,
    SUM(CASE WHEN i.status != 'Completed' THEN 1 ELSE 0 END) AS inprogress_initiatives,
    CASE WHEN COUNT(i.id) > 0
        THEN ROUND(100.0 * SUM(CASE WHEN i.status = 'Completed' THEN 1 ELSE 0 END) / COUNT(i.id), 2)
        ELSE NULL END AS completion_rate
FROM departments d
LEFT JOIN initiatives i ON i.department_id = d.id
GROUP BY d.id, d.name;

-- 4. Leadership Actions
CREATE VIEW IF NOT EXISTS vw_leadership_actions AS
SELECT
    a.id AS action_id,
    a.description,
    a.deadline,
    a.completed_date,
    a.status,
    a.priority,
    i.code AS initiative_code,
    d.name AS department,
    e.full_name AS owner
FROM leadership_actions a
LEFT JOIN initiatives i ON a.initiative_id = i.id
LEFT JOIN departments d ON i.department_id = d.id
LEFT JOIN employees e ON a.owner_id = e.id;

-- 5. KPI Measurements
CREATE VIEW IF NOT EXISTS vw_kpi_measurements AS
SELECT
    m.id AS measurement_id,
    d.name AS department,
    def.name AS kpi_name,
    m.measurement_date AS period,
    m.actual_value,
    m.target_value,
    def.unit
FROM kpi_measurements m
JOIN kpi_definitions def ON m.definition_id = def.id
LEFT JOIN departments d ON m.department_id = d.id;

-- 6. Initiative Updates
CREATE VIEW IF NOT EXISTS vw_initiative_updates AS
SELECT
    i.code AS initiative_code,
    u.update_date,
    u.progress_pct,
    u.status,
    u.update_text
FROM initiative_updates u
JOIN initiatives i ON u.initiative_id = i.id;
