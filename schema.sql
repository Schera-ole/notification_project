CREATE SCHEMA IF NOT EXISTS template;
CREATE SCHEMA IF NOT EXISTS notification;
CREATE TABLE IF NOT EXISTS template.templates(
    id uuid PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    text TEXT NOT NULL,
    variables TEXT [],
    version INT NOT NULL
);
CREATE TABLE IF NOT EXISTS notification.notifications(
    notification_id uuid PRIMARY KEY,
    template_name TEXT NOT NULL,
    version INT NOT NULL,
    user_ids uuid [] NOT NULL,
    create_at timestamp
);
CREATE TABLE IF NOT EXISTS notification.history(
    notification_id uuid PRIMARY KEY REFERENCES notification.notifications(notification_id),
    status TEXT NOT NULL,
    attempt_at timestamp
);
