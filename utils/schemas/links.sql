CREATE TABLE IF NOT EXISTS link_managers (
    batch         int,
    guild_id      int,
    manager_role  int,
    PRIMARY KEY (guild_id, manager_role)
);

CREATE TABLE IF NOT EXISTS dashboards (
    batch    int,
    section  text,
    channel  int PRIMARY KEY,
    message  int UNIQUE
);

CREATE TABLE IF NOT EXISTS links (
    batch    int,
    section  text,
    day      text,
    subject  text,
    time     text,
    link     text,
    subsecs  text,
    PRIMARY KEY (batch, section, day, subject, time)
);
