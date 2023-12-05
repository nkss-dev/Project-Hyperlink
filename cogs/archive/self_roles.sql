CREATE TABLE IF NOT EXISTS view (
    channel_id  int,
    message_id  int unique,
    view_type   int default 0,
    PRIMARY KEY (channel_id, message_id)
);

CREATE TABLE IF NOT EXISTS button (
    id          text PRIMARY KEY,
    label       text NOT NULL,
    emoji       text,
    role_id     int NOT NULL,
    message_id  int NOT NULL,
    FOREIGN KEY (message_id) REFERENCES view(message_id) ON UPDATE CASCADE ON DELETE CASCADE
);
