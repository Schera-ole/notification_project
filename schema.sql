CREATE SCHEMA IF NOT EXISTS template;
CREATE SCHEMA IF NOT EXISTS notification;
CREATE TABLE IF NOT EXISTS template.templates(
    id uuid PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    template TEXT NOT NULL,
    variables TEXT [],
    version INT NOT NULL
);
CREATE TABLE IF NOT EXISTS notification.notifications(
    notification_id uuid PRIMARY KEY,
    template TEXT NOT NULL,
    user_ids uuid [] NOT NULL,
    time_to_sent timestamp
);
CREATE TABLE IF NOT EXISTS notification.history(
    notification_id uuid PRIMARY KEY REFERENCES notification.notifications(notification_id),
    status TEXT NOT NULL,
    try_to_sent_at timestamp
);
