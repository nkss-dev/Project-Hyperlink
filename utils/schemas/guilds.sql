CREATE TABLE IF NOT EXISTS guild (
    id              bigint PRIMARY KEY,
    name            text   check(length(name) <= 100) not null,
    batch           int    unique check(batch >= 0),
    language        text   default 'en-GB',
    bot_role        bigint,
    mute_role       bigint,
    edit_channel    bigint,
    delete_channel  bigint
);

CREATE TABLE IF NOT EXISTS guild_role (
    id        bigint REFERENCES guild(id),
    field     text,
    value     text,
    role_ids  bigint[],
    PRIMARY KEY (id, value)
);

CREATE TABLE IF NOT EXISTS prefix (
    id      bigint REFERENCES guild(id),
    prefix  text   not null,
    PRIMARY KEY (id, prefix)
);

CREATE TABLE IF NOT EXISTS join_role (
    id    bigint REFERENCES guild(id),
    role  bigint PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS mod_role (
    id    bigint REFERENCES guild(id),
    role  bigint PRIMARY KEY
);

CREATE TABLE IF NOT EXISTS verified_server (
    id                   bigint PRIMARY KEY REFERENCES guild(id),
    batch                int    REFERENCES guild(batch),
    instruction_channel  bigint,
    command_channel      bigint,
    guest_role           bigint
);

CREATE TABLE IF NOT EXISTS event (
    guild_id         bigint REFERENCES guild(id),
    join_channel     bigint,
    join_message     text   DEFAULT '{$user} has joined the server!',
    leave_channel    bigint,
    leave_message    text   DEFAULT '{$user} has left the server.',
    kick_channel     bigint,
    kick_message     text   DEFAULT '{$user} has been kicked from the server by {$member}.',
    ban_channel      bigint,
    ban_message      text   DEFAULT '{$user} has been banned from the server by {$member}.',
    welcome_message  text
);
